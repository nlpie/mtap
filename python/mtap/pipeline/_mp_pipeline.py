# Copyright 2023 Regents of the University of Minnesota.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
import multiprocessing
import signal
import traceback
from logging.handlers import QueueListener
from threading import Condition, Lock
from typing import Optional, TYPE_CHECKING

from grpc import RpcError
from tqdm import tqdm

from mtap._config import Config
from mtap.pipeline._common import event_and_params
from mtap.pipeline._error_handling import StopProcessing, SuppressError
from mtap.pipeline._results import BatchPipelineResult
from mtap.pipeline._sources import ProcessingSource, IterableProcessingSource
from mtap.processing import (
    ProcessingException,
)

if TYPE_CHECKING:
    from mtap.pipeline._pipeline import ActivePipeline


_mp_pipeline: Optional['ActivePipeline'] = None


def _mp_process_init(config, pipeline, queue, log_level):
    global _mp_pipeline

    # set up multiprocess logging via queue back to listener
    h = logging.handlers.QueueHandler(queue)
    root = logging.getLogger()
    root.addHandler(h)
    root.setLevel(log_level)

    Config(config).enter_context()
    cm = pipeline.activate()
    _mp_pipeline = cm.__enter__()

    def cleanup_pipeline(*_):
        cm.__exit__()

    signal.signal(signal.SIGINT, cleanup_pipeline)


def _mp_process_event(event_id, event_service_instance_id, params):
    if _mp_pipeline is None:
        raise ValueError('_mp_pipeline not initialized correctly.')
    try:
        result = _mp_pipeline.run_by_event_id(
            event_id,
            event_service_instance_id,
            params
        )
    except ProcessingException as e:
        return event_id, None, e.error_info
    except Exception as e:
        ei = ProcessingException.from_local_exception(e, 'pipeline').error_info
        return event_id, None, ei
    return event_id, result, None


class ActiveMpRun:
    __slots__ = (
        'pipeline',
        'config',
        'targets_cond',
        'active_targets',
        'progress_bar',
        'source',
        'pool',
        'active_events',
        'log_listener',
        'stop',
        'result',
        'handler_states',
        'callback'
    )

    def __init__(self, pipeline, source, total=None, callback=None):
        self.pipeline = pipeline
        self.config = pipeline.mp_config
        self.targets_cond = Condition(Lock())
        total = (source.total if hasattr(source, 'total') else None) or total
        self.progress_bar = tqdm(
            total=total,
            unit='events',
            smoothing=0.01
        ) if self.config.show_progress else None

        if not isinstance(source, ProcessingSource):
            if not hasattr(source, '__iter__'):
                raise ValueError('The source needs to either be a '
                                 'ProcessingSource or an Iterable.')
            source = IterableProcessingSource(source)
        self.source = source

        mp_context = self.config.mp_context
        if mp_context is None:
            mp_context = multiprocessing.get_context(
                self.config.mp_start_method
            )

        logging_queue = mp_context.Queue(-1)
        handler = logging.StreamHandler()
        f = logging.Formatter('%(asctime)s %(processName)-10s %(name)s '
                              '%(levelname)-8s %(message)s')
        handler.setFormatter(f)
        handler.setLevel(self.config.log_level)
        self.log_listener = QueueListener(logging_queue, handler)
        self.log_listener.start()

        self.pool = mp_context.Pool(
            self.config.workers,
            initializer=_mp_process_init,
            initargs=(
                dict(Config()),
                self.pipeline,
                logging_queue,
                self.config.log_level
            )
        )
        self.active_targets = 0
        self.active_events = {}
        self.stop = False
        self.result = BatchPipelineResult(
            self.pipeline.name,
            [component.component_id for component in self.pipeline]
        )
        self.handler_states = [{} for _ in self.pipeline.error_handlers]
        self.callback = callback

    @property
    def max_targets(self):
        return self.config.workers + self.config.read_ahead

    def increment_active_tasks(self):
        with self.targets_cond:
            self.active_targets += 1

    def task_completed(self):
        with self.targets_cond:
            if self.progress_bar is not None:
                self.progress_bar.update(1)
            self.active_targets -= 1
            self.targets_cond.notify()

    def tasks_done(self):
        return self.active_targets == 0

    def wait_tasks_completed(self):
        with self.targets_cond:
            self.targets_cond.wait_for(self.tasks_done)

    def read_ready(self):
        return self.active_targets < self.max_targets

    def wait_to_read(self):
        with self.targets_cond:
            self.targets_cond.wait_for(self.read_ready)

    def stop_processing(self):
        self.stop = True
        self.pool.terminate()

    def handle_result(self, result):
        event_id, result, error = result
        event = self.active_events[event_id]
        if result is not None:
            self.result.add_result_times(result)
            if self.callback:
                self.callback(result, event)
        else:
            for handler, state in zip(self.pipeline.error_handlers,
                                      self.handler_states):
                try:
                    handler.handle_error(event, error, state)
                except StopProcessing:
                    self.stop_processing()
                except SuppressError:
                    break
                except Exception as e:
                    print("An error handler raised an exception: ", e)
                    traceback.print_exc()

        self.task_completed()
        if self.config.close_events:
            event.release_lease()
        self.active_events.pop(event_id)

    def consume(self, target):
        if self.stop:
            raise StopIteration
        event, params = event_and_params(target, self.config.params)
        try:
            event.lease()
            event_id = event.event_id
            self.active_events[event_id] = event
            self.pool.apply_async(_mp_process_event,
                                  args=(event_id,
                                        event.event_service_instance_id,
                                        params),
                                  callback=self.handle_result)
            self.increment_active_tasks()
        except BaseException as e:
            # here we failed (or exited) sometime between taking a new
            # lease and adding the done callback to the future,
            # meaning the lease will never get freed.
            try:
                event.release_lease()
            except RpcError:
                # Client might already be closed, we tried our best
                pass
            raise e
        self.wait_to_read()

    def run(self):
        try:
            with self.source:
                self.source.produce(self.consume)
            self.wait_tasks_completed()
        except KeyboardInterrupt:
            print('Pipeline terminated by user (KeyboardInterrupt).')
        return self.result

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.pool.terminate()
        self.pool.join()
        if self.config.close_events:
            for event in self.active_events.values():
                event.close()
        self.log_listener.stop()

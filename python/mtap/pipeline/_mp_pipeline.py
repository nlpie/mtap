#  Copyright (c) Regents of the University of Minnesota.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import logging
import multiprocessing
import signal
import sys
from contextlib import ExitStack
from logging.handlers import QueueListener
from queue import Queue, Empty
from threading import BoundedSemaphore
from typing import Optional, TYPE_CHECKING

from grpc import RpcError
from tqdm import tqdm

from mtap._config import Config
from mtap.pipeline._common import event_and_params
from mtap.pipeline._error_handling import handle_error, StopProcessing
from mtap.pipeline._sources import ProcessingSource, IterableProcessingSource
from mtap.processing import ProcessingException

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
    exit_stack = ExitStack()

    _mp_pipeline = exit_stack.enter_context(cm)

    def cleanup_pipeline(*_):
        exit_stack.close()

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
        logging.debug("Exception during processing: ", e)
        return event_id, None, e.error_info
    except Exception as e:
        logging.debug("MTAP exception during processing: ", e)
        ei = ProcessingException.from_local_exception(*sys.exc_info(), 'pipeline').error_info
        return event_id, None, ei
    return event_id, result, None


class MpPipelinePool:
    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.config = pipeline.mp_config
        self.active_events = {}
        self.sem = BoundedSemaphore(self.config.workers + self.config.read_ahead)

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

    def start_task(self, event, params, callback=None):
        self.sem.acquire()
        event_id = event.event_id
        res = self.pool.apply_async(_mp_process_event,
                                    args=(event_id,
                                          event.event_service_instance_id,
                                          params),
                                    callback=self.task_complete)
        self.active_events[event_id] = event, callback
        return res

    def task_complete(self, result):
        event_id, result, error = result
        event, callback = self.active_events.pop(event_id)
        if callback:
            callback(event, result, error)
        self.sem.release()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.pool.terminate()
        self.pool.join()
        self.log_listener.stop()


class MpPipelineRunner:
    def __init__(self, pool: MpPipelinePool, source, total=None, callback=None, show_progress=True):
        self.pool = pool
        self.config = pool.config
        self.pipeline = pool.pipeline
        total = (source.total if hasattr(source, 'total') else (len(source) if hasattr(source, '__len__') else None))
        if pool.config.show_progress is not None:
            show_progress = pool.config.show_progress
        self.progress_bar = tqdm(
            total=total,
            unit='events',
            smoothing=0.01
        ) if show_progress else None

        if not isinstance(source, ProcessingSource):
            if not hasattr(source, '__iter__'):
                raise ValueError('The source needs to either be a '
                                 'ProcessingSource or an Iterable.')
            source = IterableProcessingSource(source)
        self.source = source
        self.stop = False
        self.times = self.pipeline.create_times()
        self.error_handlers = [(handler, {}) for handler in self.pipeline.error_handlers]
        self.callback = callback
        self.results = Queue()
        self.active_targets = 0

    def tasks_done(self):
        return self.active_targets == 0

    def stop_processing(self):
        self.stop = True

    def run(self):
        try:
            with ExitStack() as es:
                es.callback(self.finish_results)
                it = iter(self.source.produce())
                es.callback(it.close)
                self.run_loop(it)
        except KeyboardInterrupt as e:
            self.stop = True
            print('Pipeline terminated by user (KeyboardInterrupt).')
            raise e
        return self.times

    def run_loop(self, it):
        while True:
            if self.stop:
                break
            try:
                target = next(it)
            except StopIteration:
                break
            event, params = event_and_params(target, self.config.params)
            event.lease()
            try:
                self.pool.start_task(event, params, self.result_callback)
                self.active_targets += 1
            except BaseException as e:
                # here we failed (or exited) sometime between taking a new
                # lease and adding the done callback to the future,
                # meaning the lease will never get freed.
                try:
                    event.release_lease()
                except RpcError as e2:
                    print("Failed to clean up event on termination: ", e2)
                raise e
            self.drain_results()

    def result_callback(self, event, result, error):
        self.results.put_nowait((event, result, error))

    def finish_results(self):
        while self.active_targets > 0:
            res = self.results.get()
            self.handle_result(*res)

    def drain_results(self):
        while True:
            try:
                res = self.results.get_nowait()
                self.handle_result(*res)
            except Empty:
                break

    def handle_result(self, event, result, error):
        self.active_targets -= 1
        if self.progress_bar is not None:
            self.progress_bar.update(1)

        try:
            if result is not None:
                self.times.add_result_times(result)
                if self.callback:
                    self.callback(result, event)
                return
            if not self.stop:
                try:
                    handle_error(self.error_handlers, event, error)
                except StopProcessing:
                    self.stop = True
                    raise
        finally:
            event.release_lease()

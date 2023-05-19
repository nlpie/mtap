# Copyright 2019 Regents of the University of Minnesota.
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
import signal
import threading
from contextlib import contextmanager
from logging.handlers import QueueListener
from typing import TypeVar, Optional


def run_server_forever(server):
    e = threading.Event()

    def do_stop(*_):
        e.set()

    signal.signal(signal.SIGINT, do_stop)
    signal.signal(signal.SIGTERM, do_stop)
    server.start()
    try:
        e.wait()
    except KeyboardInterrupt:
        pass
    server.stop()


T = TypeVar('T')


def or_default(option: Optional[T], default: T) -> T:
    if option is None:
        return default
    return option


@contextmanager
def mp_logging_listener(log_level, mp_context=None):
    if mp_context is None:
        import multiprocessing
        mp_context = multiprocessing
    logging_queue = mp_context.Queue(-1)
    handler = logging.StreamHandler()
    f = logging.Formatter('%(asctime)s %(processName)-10s %(name)s '
                          '%(levelname)-8s %(message)s')
    handler.setFormatter(f)
    handler.setLevel(log_level)
    q_listener = QueueListener(logging_queue, handler)
    q_listener.start()
    try:
        yield logging_queue
    finally:
        q_listener.stop()

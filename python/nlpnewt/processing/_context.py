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
import contextlib
import threading
from datetime import datetime
from typing import ContextManager

processor_local = threading.local()  # processor context thread local


@contextlib.contextmanager
def enter_context(identifier: str) -> ContextManager['ProcessorThreadContext']:
    try:
        old_context = processor_local.context
        identifier = old_context.identifier + '.' + identifier
    except AttributeError:
        old_context = None
    try:
        context = ProcessorThreadContext(identifier)
        processor_local.context = context
        yield context
    finally:
        del processor_local.context
        if old_context is not None:
            processor_local.context = old_context


class ProcessorThreadContext:
    def __init__(self, identifier):
        self.times = {}
        self.identifier = identifier

    @contextlib.contextmanager
    def stopwatch(self, key: str) -> ContextManager:
        start = datetime.now()
        try:
            yield
        finally:
            stop = datetime.now()
            duration = stop - start
            self.add_time(key, duration)

    def add_time(self, key, duration):
        self.times[self.identifier + ':' + key] = duration
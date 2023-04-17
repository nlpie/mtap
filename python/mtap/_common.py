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
import signal
import threading


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

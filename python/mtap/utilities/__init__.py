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
import os
import signal
import subprocess
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Optional

import grpc


def find_free_port() -> int:
    """Borrowed from ``https://stackoverflow.com/questions/1365265``.

    Returns
    -------
    int
        A free port which can be bound to.

    """
    import socket
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


@contextmanager
def subprocess_events_server(port: Optional[int] = None,
                             cwd: Optional[Path] = None,
                             config_path: Optional[Path] = None,
                             register: bool = False) -> str:
    """Context manager which launches a events server on a subprocess and yields the address.

    Parameters
    ----------
    port: optional int
        A port to bind the events server to.
    cwd: optional Path
        A current working directory to use.
    config_path: optional Path
        A path to a configuration file to use.
    register: bool
        Whether to register the events server with service discovery.

    Returns
    -------
    str
        The address that the events server us running on.

    """
    if cwd is None:
        cwd = Path.cwd()
    env = dict(os.environ)
    if config_path is not None:
        env['MTAP_CONFIG'] = str(config_path)
    if port is None:
        port = find_free_port()
    address = '127.0.0.1:' + str(port)
    cmd = ['python', '-m', 'mtap', 'events', '-p', str(port)]
    if register:
        cmd += ['--register']
    p = subprocess.Popen(cmd,
                         start_new_session=True, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         cwd=str(cwd), env=env)
    try:
        with grpc.insecure_channel(address) as channel:
            future = grpc.channel_ready_future(channel)
            future.result(timeout=10)
        yield address
    finally:
        p.send_signal(signal.SIGINT)
        try:
            stdout, _ = p.communicate(timeout=1)
            print("python events exited with code: ", p.returncode)
            print(stdout.decode('utf-8'))
        except subprocess.TimeoutExpired:
            print("timed out waiting for python events to terminate")
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
import os
import subprocess
from threading import Thread

import grpc
import pytest

logging.basicConfig(level=logging.DEBUG)


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "consul"
    )
    config.addinivalue_line(
        "markers", "integration"
    )
    config.addinivalue_line(
        "markers", "gateway"
    )


def pytest_addoption(parser):
    parser.addoption(
        "--consul", action="store_true", default=False,
        help="runs integration tests that require consul",
    )
    parser.addoption(
        "--integration", action="store_true", default=False, help="runs integration tests"
    )
    parser.addoption(
        "--gateway", action="store_true", default=False, help="runs tests that require the Go gateway"
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--consul"):
        skip_consul = pytest.mark.skip(reason="need --consul option to run")
        for item in items:
            if "consul" in item.keywords:
                item.add_marker(skip_consul)
    if not config.getoption("--integration"):
        skip_integration = pytest.mark.skip("need --integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
    if not config.getoption("--gateway"):
        skip_gateway = pytest.mark.skip(reason="need --gatway option to run")
        for item in items:
            if "gateway" in item.keywords:
                item.add_marker(skip_gateway)


def _listen(process: subprocess.Popen):
    for line in process.stdout:
        print(line.decode(), end='')
    return process.wait()


@pytest.fixture(name='processor_watcher', scope="session")
def fixture_processor_watcher():
    def func(address, process, timeout=20.0):
        listener = Thread(target=_listen, args=(process,))
        listener.start()
        try:
            if process.returncode is not None:
                raise ValueError('subprocess terminated')
            with grpc.insecure_channel(address, [('grpc.enable_http_proxy', False)]) as channel:
                future = grpc.channel_ready_future(channel)
                future.result(timeout=timeout)
            yield address
        finally:
            try:
                process.terminate()
                listener.join(timeout=5.0)
                if listener.is_alive():
                    process.kill()
                    listener.join()
                print("processor exited with code: ", process.returncode)
            except Exception:
                pass
    return func


@pytest.fixture(name='java_exe', scope="session")
def fixture_java_exe():
    import pathlib
    try:
        mtap_jar = os.environ['MTAP_JAR']
    except KeyError:
        mtap_jar = None
    if not mtap_jar:
        try:
            java_libs = pathlib.Path(__file__).parents[2] / 'java' / 'build' / 'libs'
            mtap_jar = next(java_libs.glob('*-all.jar'))
        except (FileNotFoundError, StopIteration):
            raise ValueError('MTAP_JAR not found, is required for tests')
    cp = ['-cp', str(mtap_jar)]
    try:
        return [str(pathlib.Path(os.environ['JAVA_HOME']) / 'bin' / 'java')] + cp
    except KeyError:
        return ['java'] + cp

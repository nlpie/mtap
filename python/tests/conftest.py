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
import subprocess

import grpc
import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "consul"
    )
    config.addinivalue_line(
        "markers", "integration"
    )


def pytest_addoption(parser):
    parser.addoption(
        "--consul", action="store_true", default=False,
        help="runs integration tests that require consul",
    )
    parser.addoption(
        "--integration", action="store_true", default=False, help="runs integration tests"
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


@pytest.fixture(name='processor_watcher')
def fixture_processor_watcher():
    def func(address, process):
        try:
            if process.returncode is not None:
                raise ValueError('subprocess terminated')
            with grpc.insecure_channel(address, [('grpc.enable_http_proxy', False)]) as channel:
                future = grpc.channel_ready_future(channel)
                future.result(timeout=20)
            yield address
        finally:
            process.send_signal(signal.SIGINT)
            try:
                stdout, _ = process.communicate(timeout=1)
                print("processor exited with code: ", process.returncode)
                print(stdout.decode('utf-8'))
            except subprocess.TimeoutExpired:
                print("timed out waiting for processor to terminate")
    return func

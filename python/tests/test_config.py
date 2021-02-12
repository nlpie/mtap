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
import os
from pathlib import Path

import pytest

from mtap import Config

NO_KEY = object()


@contextlib.contextmanager
def set_env(key, val):
    old = NO_KEY
    try:
        old = os.environ[key]
    except KeyError:
        pass
    os.environ[key] = val
    yield
    if old is NO_KEY:
        del os.environ[key]
    else:
        os.environ[key] = old


def test_load_broken_config():
    Config._global_instance = None
    with set_env('MTAP_CONFIG', str(Path(__file__).parent / 'brokenConfig.yaml')):
        with pytest.raises(TypeError):
            Config()


def test_load_config():
    with set_env('MTAP_CONFIG', str(Path(__file__).parent / 'workingConfig.yaml')):
        Config._global_instance = None
        c = Config()
        assert c['foo'] == 'bar'
        assert c['baz.bot'] == [1, 2, 3]


def test_config_context():
    Config._global_instance = None
    with Config() as c1:
        c1['foo'] = 'bar'
        c2 = Config()
        assert c2['foo'] == 'bar'


def test_enter_twice():
    Config._global_instance = None
    with Config():
        with pytest.raises(ValueError):
            with Config():
                pass


def test_update_from_yaml():
    Config._global_instance = None
    c = Config()
    c.update_from_yaml(str(Path(__file__).parent) + '/workingConfig.yaml')
    assert c['foo'] == 'bar'
    assert c['baz.bot'] == [1, 2, 3]

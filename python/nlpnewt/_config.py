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
"""nlpnewt SDK configuration."""

import os
import threading
from pathlib import Path

from . import base


def _collapse(d, path, v):
    try:
        p = ''
        if path is not None:
            p = path + '.'
        for k, v in v.items():
            _collapse(d, p + k, v)
        return d
    except (AttributeError, TypeError):
        pass
    d[path] = v
    return d


_DEFAULT_CONFIG = _collapse({}, None, {
    'discovery': 'consul',
    'consul': {
        'host': 'localhost',
        'port': 8500,
        'scheme': 'http',
        'dns_ip': '127.0.0.1',
        'dns_port': 8600
    }
})


def load_config(f):
    from yaml import load
    try:
        from yaml import CLoader as Loader
    except ImportError:
        from yaml import Loader
    config = load(f, Loader=Loader)
    return _collapse({}, None, config)


def load_default_config(config_path=None):
    potential_paths = [config_path, os.getenv('NEWT_CONFIG')]
    locations = [Path.cwd(), Path.home().joinpath('.newt'), Path('/etc/newt/')]
    potential_paths += [location.joinpath('newtConfig.yml') for location in locations]

    for config_path in potential_paths:
        try:
            with config_path.open('rb') as f:
                return load_config(f)
        except (AttributeError, FileNotFoundError):
            pass
    return _DEFAULT_CONFIG


class _Config(dict, base.Config):
    _lock = threading.RLock()
    _global_instance = None
    _context = threading.local()
    _context.config = None

    def __new__(cls):
        if cls._global_instance is None:
            with cls._lock:
                if cls._global_instance is None:
                    instance = dict.__new__(cls)
                    cls._global_instance = instance
                    cls._global_instance._load_default_config()
        inst = cls._context.config
        if inst is not None:
            return inst
        inst = dict.__new__(cls)
        inst.update(cls._global_instance)
        return inst

    def __enter__(self):
        with self._lock:
            if self._context.config is not None:
                raise ValueError("Already in a configuration context.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._context.config = None

    def _load_default_config(self):
        self.update(load_default_config())

    def update_from_yaml(self, path):
        with path.open('rb') as f:
            self.update(load_config(f))


def get_config():
    return _Config()

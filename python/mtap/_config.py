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
"""MTAP SDK configuration."""

import os
import threading
from pathlib import Path
from typing import Any, MutableMapping, Iterator, Union


def _collapse(d, path, v):
    try:
        p = ''
        if path is not None:
            p = path + '.'
        for k, v in v.items():
            _collapse(d, p + k, v)
        return d
    except AttributeError:
        pass
    except TypeError:
        raise ValueError('Failed to load configuration')

    d[path] = v
    return d


_DEFAULT_CONFIG = _collapse({}, None, {
    'discovery': 'consul',
    'consul': {
        'host': 'localhost',
        'port': 8500,
        'scheme': 'http',
        'python_naming_scheme': 'ipv4'
    }
})


def _load_config(f):
    from yaml import load
    try:
        from yaml import CLoader as Loader
    except ImportError:
        from yaml import Loader
    config = load(f, Loader=Loader)
    if not isinstance(config, dict):
        raise TypeError("Failed to load configuration from file: " + str(f))
    return _collapse({}, None, config)


def _load_default_config():
    potential_paths = []
    try:
        cnf = os.getenv('MTAP_CONFIG')
        potential_paths.append(Path(cnf))
    except TypeError:
        pass
    locations = [Path.cwd(), Path.home().joinpath('.mtap'), Path('/etc/mtap/')]
    potential_paths += [location.joinpath('mtapConfig.yml') for location in locations]

    for config_path in potential_paths:
        try:
            with config_path.open('rb') as f:
                return _load_config(f)
        except FileNotFoundError:
            pass
    return _DEFAULT_CONFIG


class Config(MutableMapping[str, Any]):
    """The MTAP configuration dictionary.

    By default configuration is loaded from one of a number of locations in the following priority:

      - A file at the path of the '--config' parameter passed into main methods.
      - A file at the path of the 'MTAP_CONFIG' environment variable
      - $PWD/mtapConfig.yml
      - $HOME/.mtap/mtapConfig.yml'
      - /etc/mtap/mtapConfig.yml


    Nlpnewt components will use a global shared configuration object, by entering the context of a
    config object using "with", all of the nlpnewt functions called on that thread will make use of
    that config object.

    Examples
    --------
    >>> with mtap.Config() as config:
    >>>     config['key'] = 'value'
    >>>     # other nlpnewt methods in this
    >>>     # block will use the updated config object.

    """

    _lock = threading.RLock()
    _global_instance = None
    _context = threading.local()
    _context.config = None

    def __new__(cls):
        if cls._global_instance is None:
            with cls._lock:
                if cls._global_instance is None:
                    cls._global_instance = object.__new__(cls)
                    cls._global_instance._config = {}
                    cls._global_instance._load_default_config()
        inst = cls._context.config
        if inst is not None:
            return inst
        inst = object.__new__(cls)
        inst._config = {}
        inst.update(cls._global_instance)
        return inst

    def __enter__(self) -> 'Config':
        with self._lock:
            if self._context.config is not None:
                raise ValueError("Already in a configuration context.")
            self._context.config = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._context.config = None
        if exc_val is not None:
            return False

    def _load_default_config(self):
        self.update(_load_default_config())

    def update_from_yaml(self, path: Union[Path, str]):
        """Updates the configuration by loading and collapsing all of the structures in a yaml file.

        Parameters
        ----------
        path: str
            The path to the yaml file to load.

        """
        if isinstance(path, str):
            path = Path(path)
        with path.open('rb') as f:
            self.update(_load_config(f))

    def __setitem__(self, k: str, v: Any) -> None:
        self._config[k] = v

    def __delitem__(self, v: str) -> None:
        del self._config[v]

    def __getitem__(self, k: str) -> Any:
        return self._config[k]

    def __len__(self) -> int:
        return len(self._config)

    def __iter__(self) -> Iterator[str]:
        return iter(self._config)

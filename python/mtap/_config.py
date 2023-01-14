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
import logging
import os
import threading
from pathlib import Path
from typing import Any, MutableMapping, Iterator, Union

from mtap.utilities import mtap_home

logger = logging.getLogger('mtap.config')


def _collapse(d, path, v):
    d[path] = v
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
    return d


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
    locations = [Path.cwd(), mtap_home(), Path('/etc/mtap/')]
    potential_paths += [location / 'mtapConfig.yml' for location in locations]
    potential_paths.append(Path(__file__).parent / 'defaultConfig.yml')
    for config_path in potential_paths:
        try:
            with config_path.open('rb') as f:
                logger.debug('Loading MTAP config from "{}"'.format(config_path))
                return _load_config(f)
        except FileNotFoundError:
            pass
    raise ValueError('Failed to load configuration file from')


class Config(MutableMapping[str, Any]):
    """The MTAP configuration dictionary.

    By default configuration is loaded from one of a number of locations in the following priority:

      - A file at the path of the '--config' parameter passed into main methods.
      - A file at the path of the 'MTAP_CONFIG' environment variable
      - $PWD/mtapConfig.yml
      - $HOME/.mtap/mtapConfig.yml'
      - /etc/mtap/mtapConfig.yml


    MTAP components will use a global shared configuration object, by entering the context of a
    config object using "with", all of the MTAP functions called on that thread will make use of
    that config object.

    Examples:

        >>> with mtap.Config() as config:
        >>>     config['key'] = 'value'
        >>>     # other MTAP methods in this
        >>>     # block will use the updated config object.

    """

    _lock = threading.RLock()
    _global_instance = None
    _context = threading.local()
    _context.config = None

    def __new__(cls, *args):
        if cls._global_instance is None:
            with cls._lock:
                if cls._global_instance is None:
                    cls._global_instance = object.__new__(cls)
                    cls._global_instance._config = {}
                    if len(args) == 0:
                        cls._global_instance._load_default_config()
                    else:
                        cls._global_instance._config.update(*args)
        try:
            inst = cls._context.config
        except AttributeError:
            cls._context.config = None
            inst = None
        if inst is not None:
            return inst
        inst = object.__new__(cls)
        inst._config = {}
        inst.update(cls._global_instance)
        return inst

    def __enter__(self) -> 'Config':
        self.enter_context()
        return self

    def enter_context(self):
        with self._lock:
            if hasattr(self._context, "config") and self._context.config is not None:
                raise ValueError("Already in a configuration context.")
            self._context.config = self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self._context.config = None

    def __reduce__(self):
        return Config, (dict(self), )

    def _load_default_config(self):
        self.update(_load_default_config())

    def update_from_yaml(self, path: Union[Path, str]):
        """Updates the configuration by loading and collapsing all of the structures in a yaml file.

        Parameters:
            path: The path to the yaml file to load.

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

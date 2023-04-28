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
import copy
import logging
from contextlib import suppress
from contextvars import ContextVar
from os import PathLike, getenv
from pathlib import Path
from typing import Any, MutableMapping, Iterator, Union, ClassVar, Dict, Optional

from importlib_resources import files, as_file

from mtap.utilities import mtap_home

logger = logging.getLogger('mtap.config')
DEFAULT_CONFIG = files('mtap').joinpath('defaultConfig.yml')


def expand(d: Dict):
    queue = [d]
    seen = {id(d)}
    while len(queue) > 0:
        cur = queue.pop()
        keys = list(cur.keys())
        for k in keys:
            splits = k.split('.')
            v = cur[k]
            if len(splits) > 1:
                del cur[k]
                it = cur
                for split in splits[:-1]:
                    try:
                        it = it[split]
                    except KeyError:
                        it[split] = it = {}
                it[splits[-1]] = v
            if isinstance(v, dict) and not id(v) in seen:
                queue.append(v)
                seen.add(id(v))


def collapse(d: Dict) -> Dict:
    if not isinstance(d, dict):
        return d
    path = tuple()
    result = {}
    stack = [(d, list(d.keys()))]
    # DFS
    while len(stack) > 0:
        d, keys = stack.pop()
        while len(keys) > 0:
            k = keys.pop()
            path = path + (k,)
            v = d[k]
            if isinstance(v, dict):
                stack.append((d, keys))
                stack.append((v, list(v.keys())))
                break
            else:
                result['.'.join(path)] = v
            with suppress(IndexError):
                path = path[:-1]
    return result


def load_config(config_path: Union[str, bytes, PathLike]):
    import yaml
    try:
        from yaml import CLoader as Loader
    except ImportError:
        from yaml import Loader
    with open(config_path, 'rb') as f:
        result = yaml.load(f, Loader=Loader)
    expand(result)
    return result


def load_default_config():
    potential_paths = []
    from_env = getenv('MTAP_CONFIG')
    if from_env is not None:
        potential_paths += [from_env]
    locations = [Path.cwd(), mtap_home(), Path('/etc/mtap/')]
    potential_paths += [location / 'mtapConfig.yml' for location in locations]
    with as_file(DEFAULT_CONFIG) as default_config_path:
        potential_paths.append(default_config_path)
        for config_path in potential_paths:
            try:
                config = load_config(config_path)
                logger.debug(f'Loaded MTAP config from "{config_path}"')
                return config
            except FileNotFoundError:
                pass
        raise ValueError(f'Failed to load configuration file from {potential_paths}')


class Config(MutableMapping[str, Any]):
    """The MTAP configuration dictionary.

    The default configuration is loaded from one of a number of locations in the following priority:

      - A file at the path of the '--config' parameter passed into main methods.
      - A file at the path of the 'MTAP_CONFIG' environment variable
      - $PWD/mtapConfig.yml
      - $HOME/.mtap/mtapConfig.yml'
      - /etc/mtap/mtapConfig.yml


    MTAP components will use a global shared configuration object, by entering the context of a
    config object using "with", all the MTAP functions called on that thread will make use of
    that config object.

    Examples:

        >>> with mtap.Config() as config:
        >>>     config['key'] = 'value'
        >>>     # other MTAP methods in this
        >>>     # block will use the updated config object.

    """
    GLOBAL_DEFAULTS: ClassVar[Optional[Dict[str, Any]]] = None

    def __init__(self, data=None):
        if Config.GLOBAL_DEFAULTS is None:
            Config.GLOBAL_DEFAULTS = load_default_config()
        try:
            self.data = config_ctx.get()
        except LookupError:
            self.data = copy.deepcopy(Config.GLOBAL_DEFAULTS)
        self.token = None
        if data is not None:
            self.data.update(data)

    def __enter__(self) -> 'Config':
        self.enter_context()
        return self

    def enter_context(self):
        self.data = copy.deepcopy(self.data)
        self.token = config_ctx.set(self.data)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        config_ctx.reset(self.token)
        self.token = None

    def __reduce__(self):
        return Config, (self.data,)

    def update_from_yaml(self, path: Union[str, bytes, PathLike]):
        """Updates the configuration by loading and collapsing all the structures in a yaml file.

        Parameters:
            path: The path to the yaml file to load.
        """
        self.data.update(load_config(path))

    def __setitem__(self, k: str, v: Any) -> None:
        if not isinstance(k, str):
            raise KeyError("Key must be instance of `str`")
        splits = k.split('.')
        ptr = self.data
        for split in splits[:-1]:
            try:
                ptr = ptr[split]
            except KeyError:
                ptr = {}
                ptr[split] = ptr
        ptr[splits[-1]] = v

    def __delitem__(self, v: str) -> None:
        if not isinstance(v, str):
            raise KeyError("Key must be instance of `str`")
        splits = v.split('.')
        ptr = self.data
        for split in splits[:-1]:
            ptr = ptr[split]
        del ptr[splits[-1]]

    def __getitem__(self, k: str) -> Any:
        if not isinstance(k, str):
            raise KeyError("Key must be instance of `str`")
        splits = k.split('.')
        ptr = self.data
        for split in splits:
            ptr = ptr[split]
        return collapse(ptr)

    def __len__(self) -> int:
        return len(self.data)

    def __iter__(self) -> Iterator[str]:
        return iter(self.data)


config_ctx: ContextVar[Dict] = ContextVar('config_ctx')

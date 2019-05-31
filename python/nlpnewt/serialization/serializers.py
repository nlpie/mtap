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
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Dict

_serializers = {}


class Serializer(ABC):
    @abstractmethod
    @property
    def extension(self) -> str:
        ...

    @abstractmethod
    def dict_to_file(self, d: Dict, filepath: Path):
        ...


def serializer(name: str) -> Callable[[Callable[[], Serializer]], Callable[[], Serializer]]:
    def decorator(func: Callable[[], Serializer]) -> Callable[[], Serializer]:
        _serializers[name] = func
        return func
    return decorator


def get_serializer(name: str) -> Callable[[], Serializer]:
    return _serializers[name]

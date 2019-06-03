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
import io
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Union

from nlpnewt.events import Event

_serializers = {}


class Serializer(ABC):
    """Base class for a serializer of NLP-NEWT events.
    """

    @property
    @abstractmethod
    def extension(self) -> str:
        """The default filename extension.

        Returns
        -------
        str
            Filename extension, including period. Ex: ``'.json'``.
        """
        ...

    @abstractmethod
    def event_to_file(self, event: Event, f: Union[Path, str, io.IOBase]):
        """Writes the event to a file.

        Parameters
        ----------
        event: Event
            The event object to serialize.
        f: Path or str or file-like object
            A file or a path to a file to write the event to.
        """
        ...


def serializer(name: str) -> Callable[[Callable[[], Serializer]], Callable[[], Serializer]]:
    """Decorator which marks an implementation of :obj:`Serializer` that can be used for a specific
    kind of serialization.

    Parameters
    ----------
    name: str
        The name to register the serializer under, Ex. ``'json'``.

    Returns
    -------
    decorator
        Decorator of class or function which returns a serializer.

    """

    def decorator(func: Callable[[], Serializer]) -> Callable[[], Serializer]:
        _serializers[name] = func
        return func

    return decorator


def get_serializer(name: str) -> Callable[[], Serializer]:
    """Gets a callable which creates a serializer for the specific name.

    Parameters
    ----------
    name: str
        The name for the type of serialization, Ex. ``'json'``.

    Returns
    -------
    Callable[[], Serializer]
        Function that can be used to create a :obj:`Serializer`.

    """
    return _serializers[name]

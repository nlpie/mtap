# Copyright 2023 Regents of the University of Minnesota.
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
from abc import ABC, abstractmethod
from os import PathLike
from pathlib import Path
from typing import Union, Optional, ContextManager, Callable

from mtap._document import Document
from mtap._event import Event
from mtap._events_client import EventsClient


class ProcessingSource(ContextManager, ABC):
    """Provides events or documents for the multithreaded pipeline runner.
    Also has functionality for receiving results.

    """
    __slots__ = ()

    _total: Optional[int] = None

    @property
    def total(self) -> Optional[int]:
        """The total number of documents this source will provide.

        Returns:
            Total number of events this source will provide or ``None`` if not
            known.

        """
        return self._total

    @total.setter
    def total(self, count: Optional[int]):
        self._total = count

    @abstractmethod
    def produce(
            self,
            consume: Callable[[Union[Document, Event]], None]
    ):
        """The method which provides documents or events to the pipeline
        to batch process.

        Args:
            consume: The consumer method to pass documents or events to
                process.

        Examples:
            Example implementation for processing text documents:

            >>> ...
            >>> def produce(self, consume):
            >>>     for file in Path(".").glob("*.txt"):
            >>>         with file.open('r') as fio:
            >>>             txt = fio.read()
            >>>         with Event(client=client) as e:
            >>>             doc = event.create_document('plaintext', txt)
            >>>             consume(doc)
        """
        ...

    def close(self):
        """Optional method: called to clean up after processing is complete.

        Default behavior is to do nothing.
        """
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return None


class IterableProcessingSource(ProcessingSource):
    """Wraps an iterable in a ProcessingSource for the multi-thread processor.

    """
    __slots__ = ('it',)

    def __init__(self, source):
        # We use an iterator here to can ensure that it gets closed on
        # unexpected / early termination and any caller context managers are
        # exited before their client gets shut down.
        # Using a for-in loop we're not guaranteed, which can cause zombie
        # unclosed events on the event service.
        self.it = iter(source)
        try:
            self.total = len(source)
        except (AttributeError, TypeError):
            pass

    def produce(self, consume):
        while True:
            try:
                target = next(self.it)
            except StopIteration:
                break
            consume(target)

    def close(self):
        try:
            self.it.close()
        except AttributeError:
            pass


class FilesInDirectoryProcessingSource(ProcessingSource):
    """Processing source for pipelines which iterates over files in a
    directory.

    Args:
        count_total: Should the ``count_total`` attribute be populated by
            iterating through the directory once to count all matching files.

    Attributes:
        client: Create the events using this client.
        directory: The path to the directory of files to process.
        document_name: Creates documents with this name and adds the file's
            plain text.
        extension_glob: A glob used to filter documents from the directory.
        total: The total number of documents.
        errors: The errors argument for :func:`open`.

    Examples:

        >>> with Pipeline(...) as pipeline:
        >>>     pipeline.run_multithread(
        >>>         FilesInDirectoryProcessingSource("/path/to/docs")
        >>>     )
    """
    __slots__ = (
        'client',
        'directory',
        'document_name',
        'extension_glob',
        'errors',
        'total'
    )

    def __init__(self, client: EventsClient,
                 directory: Union[str, bytes, PathLike],
                 *, document_name: str = 'plaintext',
                 extension_glob: str = '*.txt',
                 count_total: bool = True,
                 errors: Optional[str] = None):
        self.client = client
        if not os.path.isdir(directory):
            raise ValueError(
                f'Invalid input directory: {self.directory}'
            )
        self.directory = directory
        self.document_name = document_name
        self.extension_glob = extension_glob
        self.errors = errors
        if count_total:
            self.total = sum(1 for _
                             in Path(directory).rglob(self.extension_glob))

    def produce(self, consume):
        for path in Path(self.directory).rglob(self.extension_glob):
            with path.open('r', errors=self.errors) as f:
                txt = f.read()
            relative = str(path.relative_to(self.directory))
            with Event(event_id=relative, client=self.client,
                       only_create_new=True) as e:
                doc = e.create_document(self.document_name, txt)
                consume(doc)

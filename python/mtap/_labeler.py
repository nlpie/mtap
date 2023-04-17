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
import threading
from typing import Generic, ContextManager, TypeVar, TYPE_CHECKING

from mtap._labels import Label

if TYPE_CHECKING:
    from mtap import Document
    from mtap.types import ProtoLabelAdapter

L = TypeVar('L', bound=Label)


class Labeler(Generic[L], ContextManager['Labeler']):
    """Object provided by :func:`~'mtap.Document'.get_labeler` which is
    responsible for adding labels to a label index on a document.
    """
    __slots__ = (
        '_client',
        '_document',
        '_label_index_name',
        '_label_adapter',
        'is_done',
        '_current_labels',
        '_lock'
    )

    def __init__(self,
                 document: 'Document',
                 label_index_name: str,
                 label_adapter: 'ProtoLabelAdapter[L]'):
        self._document = document
        self._label_index_name = label_index_name
        self._label_adapter = label_adapter
        self.is_done = False
        self._current_labels = []
        self._lock = threading.Lock()

    def __call__(self, *args, **kwargs) -> L:
        """Calls the constructor for the label type adding it to the list of
        labels to be uploaded.

        Args:
            args: Arguments passed to the label type's constructor.
            kwargs: Keyword arguments passed to the label type's constructor.

        Returns:
            The object that was created by the label type's constructor.

        Examples:
            >>> labeler(0, 25, some_field='some_value', x=3)
            GenericLabel(start_index=0, end_index=25, some_field='some_value',
                         x=3)
        """
        label = self._label_adapter.create_label(*args,
                                                 document=self._document,
                                                 **kwargs)
        self._current_labels.append(label)
        return label

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            return False
        self.done()

    def done(self):
        """Finalizes the label index, uploads the added labels to the events
        service.

        Normally called automatically on exit from a context manager block,
        but can be manually invoked if the labeler is not used in a context
        manager block."""
        with self._lock:
            if self.is_done:
                return
            self.is_done = True
            self._document.add_labels(self._label_index_name,
                                      self._current_labels,
                                      label_adapter=self._label_adapter)

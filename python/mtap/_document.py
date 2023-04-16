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
from typing import overload, Optional, Mapping, Iterator, \
    Iterable, Sequence, TypeVar, List, TYPE_CHECKING

from mtap._label_adapters import GENERIC_ADAPTER, DISTINCT_GENERIC_ADAPTER
from mtap._labeler import Labeler

if TYPE_CHECKING:
    from mtap import Event, GenericLabel
    from mtap.types import EventsClient, ProtoLabelAdapter, LabelIndex

L = TypeVar('L', bound='Label')
LabelAdapters = Mapping[str, 'ProtoLabelAdapter']


class Document:
    """An object for interacting with text and labels stored on an
    :class:`Event`.

    Documents are keyed by their name, and pipelines can store different
    pieces of related text on a single processing event using multiple
    documents. An example would be storing the text of one language on one
    document, and a translation on another, or storing the rtf or html
    encoding on one document (or as a binary in :method:`Event.binaries`), and
    the parsed plaintext on another document.

    Both the document text and any added label indices are immutable. This is
    to enable parallelization and distribution of processing, and because other
    label indices might be downstream dependents on the earlier created labels.

    Args:
        document_name: The document name identifier.
        text: The document text, can be omitted if this is an existing
            document and text needs to be retrieved from the events service.
        event: The parent event of this document. If the event has a client,
            then that client will be used to share changes to this document
            with all other clients of the Events service. In that case, text
            should only be specified if it is the known existing text of the
            document.

    Examples:
        Local document:

        >>> document = Document('plaintext', text='Some document text.')

        Existing distributed object:

        >>> with EventsClient(address='localhost:8080') as client, \
        >>>      Event(event_id='1',
        >>>            event_service_instance_id='events_sid',
        >>>            client=client) as event:
        >>>     document = event.documents['plaintext']
        >>>     document.text
        'Some document text fetched from the server.'

        New distributed object:

        >>> with EventsClient(address='localhost:8080') as client, \
        >>>      Event(event_id='1', client=client) as event:
        >>>     document = Document('plaintext', text='Some document text.')
        >>>     event.add_document(document)

        or

        >>> with EventsClient(address='localhost:8080') as client, \
        >>>      Event(event_id='1', client=client) as event:
        >>>     document = event.create_document('plaintext',
        >>>                                      text='Some document text.')

    """
    __slots__ = (
        '_document_name',
        '_event',
        '_text',
        '_labelers',
        '_created_indices',
        '_waiting_indices',
        'label_adapters',
        '_labels',
    )

    @overload
    def __init__(
            self,
            document_name: str,
            *, text: str,
            label_adapters: Optional[LabelAdapters] = None
    ):
        ...

    @overload
    def __init__(
            self,
            document_name: str,
            *, event: 'Event',
            label_adapters: Optional[LabelAdapters] = None
    ):
        pass

    @overload
    def __init__(
            self,
            document_name: str,
            *, text: str,
            event: 'Event',
            label_adapters: Optional[LabelAdapters] = None
    ):
        pass

    def __init__(
            self,
            document_name: str,
            *, text: Optional[str] = None,
            event: Optional['Event'] = None,
            label_adapters: Optional[LabelAdapters] = None
    ):
        if not isinstance(document_name, str):
            raise TypeError('Document name is not string.')
        self._document_name = document_name
        self._event = event
        self._text = text
        self._labelers = []
        self._created_indices = []
        self._waiting_indices = []
        self.label_adapters = label_adapters or {}
        if self.event is not None and self.event.client is None and text is None:
            raise ValueError(
                'Document must either be an existing document (event.client '
                'is not None) or must have the text parameter specified.'
            )

    @property
    def event(self) -> Optional['Event']:
        """The parent event of this document."""
        return self._event

    @property
    def document_name(self) -> str:
        """The unique identifier for this document on the event."""
        return self._document_name

    @property
    def text(self) -> str:
        """The document text."""
        if self._text is None and event_client(self) is not None:
            self._text = event_client(self).get_document_text(*ids(self))
        return self._text

    @property
    def created_indices(self) -> List[str]:
        """A list of all the label index names that have been created on this
        document using a labeler either locally or by remote pipeline
        components invoked on this document."""
        return list(self._created_indices)

    @property
    def labels(self) -> Mapping[str, 'LabelIndex']:
        """A mapping from label index names to their label index.

        Items will be fetched from the events service if they are not cached
        locally when the document has an event with a client.
        """
        return self._label_indices

    @property
    def _label_indices(self) -> '_LabelIndices':
        try:
            return self._labels
        except AttributeError:
            self._labels = _LabelIndices(self)
            return self._labels

    def get_labeler(
            self,
            label_index_name: str,
            *, distinct: Optional[bool] = None
    ) -> Labeler['GenericLabel']:
        """Alias for :meth:`labeler`
        """
        return self.labeler(label_index_name, distinct=distinct)

    def labeler(
            self,
            label_index_name: str,
            *, distinct: Optional[bool] = None
    ) -> Labeler['GenericLabel']:
        """Creates a function that can be used to add labels to a label index.

        Args:
            label_index_name: An identifying name for the label index.
            distinct: Optional, if using generic labels, whether to use
                distinct generic labels or non-distinct generic labels, will
                default to False. Distinct labels are non-overlapping and
                can use faster binary search indices.

        Returns:
            A callable when used in conjunction with the 'with' keyword will
            automatically handle uploading any added labels to the server.

        Examples:
            >>> with document.get_labeler('sentences',
            >>>                           distinct=True) as labeler:
            >>>     labeler(0, 25, sentence_type='STANDARD')
            >>>     sentence = labeler(26, 34)
            >>>     sentence.sentence_type = 'FRAGMENT'
        """
        if label_index_name in self._labelers:
            raise KeyError("Labeler already in use: " + label_index_name)
        label_adapter = self.default_adapter(label_index_name, distinct)

        labeler = Labeler(self, label_index_name, label_adapter)
        self._labelers.append(label_index_name)
        return labeler

    def add_labels(self,
                   label_index_name: str,
                   labels: Sequence[L],
                   *, distinct: Optional[bool] = None,
                   label_adapter: Optional['ProtoLabelAdapter'] = None):
        """Skips using a labeler and adds the sequence of labels as a new
        label index.

        Args:
            label_index_name: The name of the label index.
            labels: The labels to add.
            distinct: Whether the index is distinct or non-distinct.
            label_adapter: A label adapter to use.

        Returns:
            The new label index created from the labels.
        """
        if label_index_name in self.labels:
            raise KeyError(
                "Label index already exists with name: " + label_index_name)
        if label_adapter is None:
            if distinct is None:
                distinct = False
            label_adapter = self.default_adapter(label_index_name,
                                                 distinct)
        labels = sorted(labels, key=lambda x: x.location)
        waiting_on = set()
        for i, lbl in enumerate(labels):
            lbl.document = self
            lbl.identifier = i
            lbl.label_index_name = label_index_name
        for lbl in labels:
            lbl.collect_floating_references(waiting_on)
        if len(self._waiting_indices) > 0:
            label_ids = {id(label) for label in labels}
            self.check_waiting_indices(label_ids)

        if len(waiting_on) > 0:
            self._waiting_indices.append(
                (label_index_name, labels, label_adapter, waiting_on))
        else:
            self.finalize_labels(label_adapter, label_index_name, labels)

    def check_waiting_indices(self, updated_ids):
        waiting_indices = []
        for (label_index_name,
             labels,
             label_adapter,
             waiting_on) in self._waiting_indices:
            still_waiting = waiting_on.difference(updated_ids)
            if len(still_waiting) == 0:
                self.finalize_labels(label_adapter, label_index_name, labels)
            else:
                waiting_indices.append(
                    (label_index_name, labels, label_adapter, still_waiting))
        self._waiting_indices = waiting_indices

    def finalize_labels(self, label_adapter, label_index_name, labels):
        label_adapter.store_references(labels)
        if event_client(self) is not None:
            event_client(self).add_labels(*ids(self),
                                          index_name=label_index_name,
                                          labels=labels,
                                          adapter=label_adapter)
        self._created_indices.append(label_index_name)
        index = label_adapter.create_index(labels)
        self._label_indices.add_to_cache(label_index_name, index)
        return index

    def default_adapter(
            self,
            label_index_name: str,
            distinct: Optional[bool] = None
    ) -> Optional['ProtoLabelAdapter']:
        try:
            return self.label_adapters[label_index_name]
        except KeyError:
            pass
        try:
            return self.event.label_adapters[label_index_name]
        except (AttributeError, KeyError):
            return DISTINCT_GENERIC_ADAPTER if distinct else GENERIC_ADAPTER

    def add_created_indices(self, created_indices: Iterable[str]):
        return self._created_indices.extend(created_indices)


class _LabelIndices(Mapping[str, 'LabelIndex']):
    __slots__ = (
        'document',
        'cache',
        'names_cache'
    )

    def __init__(self, document: Document):
        self.document = document
        self.cache = {}
        self.names_cache = set()

    def __getitem__(self, k: str) -> 'LabelIndex':
        try:
            return self.cache[k]
        except KeyError:
            pass

        if k not in self:
            raise KeyError

        if event_client(self.document) is not None:
            label_adapter = self.document.default_adapter(k)
            if label_adapter is None:
                label_adapter = GENERIC_ADAPTER
            index = event_client(self.document).get_labels(
                *ids(self.document),
                k,
                adapter=label_adapter
            )
            for label in index:
                label.label_index_name = k
                label.document = self.document
            self.cache[k] = index
            self.names_cache.add(k)
            return index
        else:
            raise KeyError('Document does not have label index: ' + k)

    def __contains__(self, item):
        self.refresh_names()
        return item in self.names_cache

    def __len__(self) -> int:
        self.refresh_names()
        return len(self.names_cache)

    def __iter__(self) -> Iterator[str]:
        self.refresh_names()
        return iter(self.names_cache)

    def refresh_names(self):
        if event_client(self.document) is not None:
            infos = event_client(self.document).get_label_index_info(
                *ids(self.document)
            )
            for info in infos:
                self.names_cache.add(info.index_name)

    def add_to_cache(self, label_index_name, index):
        self.cache[label_index_name] = index
        self.names_cache.add(label_index_name)


def ids(document: 'Document'):
    return (
        document.event.event_service_instance_id,
        document.event.event_id,
        document.document_name
    )


def event_client(document: 'Document') -> Optional['EventsClient']:
    if document.event is None:
        return None
    return document.event.client

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
"""Abstract base classes for nlpnewt functionality."""
import abc
import datetime
import sys
from typing import TypeVar, ContextManager, MutableMapping, AnyStr, Any, Mapping, Sequence, \
    Generic, Union, Iterator, Optional, Dict, List, NamedTuple

L = TypeVar('L', bound='Label')


class Config(ContextManager, MutableMapping[AnyStr, Any], metaclass=abc.ABCMeta):
    """The nlpnewt configuration dictionary.

    By default configuration is loaded from one of a number of locations in the following priority:

      - A file at the path of the '--config' parameter passed into main methods.
      - A file at the path of the 'NEWT_CONFIG' environment variable
      - $PWD/newtConfig.yml
      - $HOME/.newt/newtConfig.yml'
      - etc/newt/newtConfig.yml


    Nlpnewt components will use a global shared configuration object, by entering the context of a
    config object using "with", all of the nlpnewt functions called on that thread will make use of
    that config object.

    Examples
    --------
    >>> with nlpnewt.config() as config:
    >>>     config['key'] = 'value'
    >>>     # other nlpnewt methods in this
    >>>     # block will use the updated config object.

    """

    @abc.abstractmethod
    def update_from_yaml(self, path):
        """Updates the configuration by loading and collapsing all of the structures in a yaml file.

        Parameters
        ----------
        path: str
            The path to the yaml file to load.

        """
        ...


class Events(ContextManager, metaclass=abc.ABCMeta):
    """The object created by :func:`events` to interact with all of the events.

    """

    @abc.abstractmethod
    def open_event(self, event_id: str = None) -> 'Event':
        """Opens or creates an event on the events service and returns an Event object that can be
        used to access and manipulate data.

        Parameters
        ----------
        event_id : str, optional
            A globally-unique identifier for the event, or omit / none for a random UUID.

        Returns
        -------
        Event
            An Event object for interacting with the event.

        """
        ...

    @abc.abstractmethod
    def create_event(self, event_id: str = None) -> 'Event':
        """Creates an event on the events service, failing if an event already exists with the
        specified ID, returns an :obj:`Event` object that can be used to access and manipulate data.

        Parameters
        ----------
        event_id : str, optional
            A globally-unique identifier for the event, or omit / none for a random UUID.

        Returns
        -------
        Event
            A newly initialized event.

        Raises
        ------
        ValueError
            If the event already exists on the server.

        """
        ...

    @abc.abstractmethod
    def close(self):
        """Closes the connection to the events service.
        """
        ...


class Event(Mapping[str, 'Document'], ContextManager, metaclass=abc.ABCMeta):
    """The object created by :func:`~Events.open_event` or :func:`~Events.create_event` to interact
    with a specific event on the events service.

    The Event object functions as a map from string document names to :obj:`Document` objects that
    can be used to access document data from the events server.

    Examples
    --------
    >>> with events.open_event('id') as event:
    >>>     # use event

    """

    def __getitem__(self, document_name):
        """Retrieves an object for interacting with an existing document on this event.

        Parameters
        ----------
        document_name : str
            The document_name identifier.

        Returns
        -------
        Document
            An object that is set up to connect to the events service to retrieve data and
            modify the document with the `document_name` on this event.

        Examples
        --------
        >>> plaintext_document = event['plaintext']
        >>> plaintext_document.text
        'The quick brown fox jumped over the lazy dog.'

        """
        ...

    @property
    @abc.abstractmethod
    def event_id(self) -> str:
        """Returns the globally unique identifier for this event.

        Returns
        -------
        str
            The event ID.
        """
        ...

    @property
    @abc.abstractmethod
    def metadata(self) -> MutableMapping[str, str]:
        """Returns an object that can be used to query and add metadata to the object.

        Returns
        -------
        typing.MutableMapping[str, str]
            An object containing the metadata

        """
        ...

    @property
    @abc.abstractmethod
    def created_indices(self) -> Mapping[AnyStr, Sequence[AnyStr]]:
        """Returns a map of label indices that have been added to any document on this event.

        Returns
        -------
        dict[str, list[str]]
            A dictionary of string ``document_name`` to lists of string ``index_name``.

        """
        ...

    @abc.abstractmethod
    def close(self) -> None:
        """Closes this event. Lets the event service know that we are done with the event,
        allowing to clean up the event if everyone is done with it.
        """
        ...

    @abc.abstractmethod
    def add_document(self, document_name: str, text: str) -> 'Document':
        """Adds a document to the event keyed by the document_name and
        containing the specified text.

        Parameters
        ----------
        document_name : str
            The event-unique identifier for the document, example: 'plaintext'.
        text : str
            The content of the document. This is a required field, document text is final and
            immutable, as changing the text very likely would invalidate any labels on the document.

        Returns
        -------
        Document
            An object that is set up to connect to the events service to retrieve data and
            modify the document with the `document_name` on this event.
        """
        ...


class Document(abc.ABC):
    """An object returned by :func:`~Event.__getitem__` or :func:`~Event.add_document`
    for accessing document data.

    Documents are keyed by their name, this is to allow pipelines to store different pieces of
    related text on a single processing event. An example would be storing the text of one language
    on one document, and the text of another language on another, or, for example, storing the
    plaintext.

    Both label indices, once added, and the document text are immutable. This is to enable
    parallelization and distribution of processing, and to prevent changes to upstream data that
    has already been used in the creation of downstream data.

    """

    @property
    @abc.abstractmethod
    def event(self) -> Event:
        """Returns the parent event of this document.

        Returns
        -------
        Event
            The event object which contains this document.

        """
        ...

    @property
    @abc.abstractmethod
    def document_name(self) -> AnyStr:
        """The event-unique identifier.

        Returns
        -------

        """
        ...

    @property
    @abc.abstractmethod
    def text(self) -> str:
        """Returns the document text, fetching if it is not cached locally.

        Returns
        -------
        str
            The text that the document was created

        """
        ...

    @property
    @abc.abstractmethod
    def created_indices(self) -> Sequence[AnyStr]:
        """Returns the newly created label indices on this document using a labeler.

        Returns
        -------
        list[str]
            A list of all of the label indices that have created on this document using a labeler.
        """
        ...

    @abc.abstractmethod
    def get_label_index(self,
                        label_index_name: str,
                        *,
                        label_type_id: str = None) -> 'LabelIndex':
        """Gets the document's label index with the specified key, fetching it from the
        service if it is not cached locally.

        Parameters
        ----------
        label_index_name : str
            The name of the label index to get.
        label_type_id : str, optional
            The identifier that a :obj:`ProtoLabelAdapter` was registered with
            :func:`proto_label_adapter`. It will be used to deserialize the labels in the index.
            If not set, the adapter for :obj:`GenericLabel` will be used.

        Returns
        -------
        LabelIndex
            LabelIndex object containing the labels.

        """
        ...

    @abc.abstractmethod
    def get_labeler(self,
                    label_index_name: str,
                    *,
                    distinct: bool = None,
                    label_type_id: str = None) -> ContextManager['Labeler']:
        """Creates a function that can be used to add labels to a label index.

        If the label id is not specified it will use :obj:`GenericLabel`, otherwise it will
        look for a custom :obj:`ProtoLabelAdapter` registered using :func:`proto_label_adapter`

        Parameters
        ----------
        label_index_name : str
            A document-unique identifier for the label index to be created.
        label_type_id: str
            Optional, the string identifier that an adapter has been registered under, or None if
            the default, generic labels are being used.
        distinct: bool
            Optional, whether to use GenericLabel or DistinctGenericLabel

        Returns
        -------
        typing.ContextManager
            A contextmanager for the labeler, which when used in conjunction with the 'with'
            keyword will automatically handle uploading any added labels to the server

        Examples
        --------
        >>> with document.get_labeler('sentences', distinct=True) as labeler:
        >>>     labeler(0, 25)
        >>>     sentence = labeler(26, 34)
        >>>     sentence.sentence_type = 'FRAGMENT'

        """
        ...


class Label(abc.ABC):
    """An abstract base class for a label of attributes on text.

    """

    @property
    @abc.abstractmethod
    def start_index(self) -> int:
        """The index of the first character of the text covered by this label"""
        ...

    @start_index.setter
    @abc.abstractmethod
    def start_index(self, value: int):
        ...

    @property
    @abc.abstractmethod
    def end_index(self) -> int:
        """The index after the last character of the text covered by this label."""
        ...

    @end_index.setter
    @abc.abstractmethod
    def end_index(self, value: int):
        ...

    def get_covered_text(self, text: str):
        """Retrieves the slice of text from `start_index` to `end_index`.

        Parameters
        ----------
        text: str
            The text to retrieve covered text from.

        Returns
        -------
        str
            Substring slice of the text.

        Examples
        --------
        >>> label = labeler(0, 9)
        >>> label.get_covered_text("The quick brown fox jumped over the lazy dog.")
        "The quick"

        >>> label = labeler(0, 9)
        >>> "The quick brown fox jumped over the lazy dog."[label.start_index:label.end_index]
        "The quick"
        """
        return text[self.start_index:self.end_index]


class LabelIndex(Sequence[L], Generic[L]):
    """An immutable sequence of labels ordered by their location in text. By default sorts by
    ascending :func:`Label.start_index` and then by ascending :func:`Label.end_index`.

    Parameters
    ==========
    L

    See Also
    ========
    Document.get_label_index : Method for getting existing label indices.
    Document.get_labeler : Method for adding new label indexes to documents.
    Labeler : Object for adding new label indices to documents.
    """

    @property
    @abc.abstractmethod
    def distinct(self):
        ...

    @abc.abstractmethod
    def __getitem__(self, idx: Union[int, slice, Label]) -> Union[L, 'LabelIndex[L]']:
        """Returns the label at the specified index.

        Parameters
        ----------
        idx : int or slice or Label
            The index of the label to return or a slice of indices to return as a new label index,
            or a label to indicate to indicate a location.

        Returns
        -------
        L or LabelIndex
            Label if a single index, LabelIndex if a slice of indices or a location.
            If location is a LabelIndex of all of the labels with that location.

        Examples
        --------
        At index:

        >>> sentences = distinct_label_index(label(0, 10),
        >>>                                  label(11, 40),
        >>>                                  label(41, 60),
        >>>                                  label(61, 90))
        >>> sentence = sentences[0]
        >>> print(sentence)
        GenericLabel{start_index = 0, end_index = 10}


        With location:

        >>> index = standard_label_index(label(0, 3, x=1),
        >>>                              label(0, 3, x=2),
        >>>                              label(1, 2, x=3))
        >>> index[label(0, 3)]
        LabelIndex[GenericLabel{0, 3, x=1}, GenericLabel{0, 3, x=2}]

        Slice:

        >>> sentences = distinct_label_index(label(0, 10),
        >>>                                  label(11, 40),
        >>>                                  label(41, 60),
        >>>                                  label(61, 90))
        >>> sentences[:2]
        LabelIndex[GenericLabel{0, 10}, GenericLabel{11, 40}]
        >>> last_two_sentences = [-2:]
        LabelIndex[GenericLabel{41, 60}, GenericLabel{61, 90}]

        """
        ...

    @abc.abstractmethod
    def __len__(self) -> int:
        """The number of labels in this label index.

        Returns
        -------
        int
            Count of labels in this index.

        Examples
        --------
        >>> len(sentences_index)
        25

        """
        ...

    @abc.abstractmethod
    def __contains__(self, item: Any):
        """Checks if the item is a label in this label index.

        Parameters
        ----------
        item: Any

        Returns
        -------
        bool
            True if the item is a label and it is in this label index. False if it is not.

        """
        ...

    @abc.abstractmethod
    def __iter__(self) -> Iterator[L]:
        """An iterator of the label objects in this index.

        Returns
        -------
        typing.Iterator[Label]


        Examples
        --------
        >>> for sentence in sentences_index:
        >>>     # use sentence

        >>> it = iter(sentences_index)
        >>> try:
        >>>     next_sentence = next(it)
        >>> except StopIteration:
        >>>     pass
        """
        ...

    @abc.abstractmethod
    def __reversed__(self) -> 'LabelIndex[L]':
        """The labels in this label index in reverse order.

        Returns
        -------
        LabelIndex[L]
        """
        ...

    @abc.abstractmethod
    def index(self, x: Any, start: int = ..., end: int = ...) -> int:
        """The index of the first occurrence of `x` in the label index at or after `start`
        and before `end`.

        Parameters
        ----------
        x: Any
        start: int, optional
            Inclusive start index.
        end: int, optional
            Exclusive end index.

        Returns
        -------
        index: int

        Raises
        ------
        ValueError
            If x is not found in this label index.

        """
        ...

    @abc.abstractmethod
    def count(self, x: Any) -> int:
        """The number of times `x` occurs in the label index.

        Parameters
        ----------
        x: Any

        Returns
        -------
        count: int

        """
        ...

    @abc.abstractmethod
    def covering(self, x: Union[Label, int], end: Optional[int] = None) -> 'LabelIndex[L]':
        """A label index containing all labels that cover / contain the specified span of text.

        Parameters
        ----------
        x: Label or int
            Either a label whose location specifies the entire span of text, or the start index of
            the span of text.
        end: int, optional
            The exclusive end index of the span of text if it has not been specified by a label.

        Returns
        -------
        LabelIndex[L]

        """
        ...

    @abc.abstractmethod
    def inside(self, x: Union[Label, int], end: Optional[int] = None) -> 'LabelIndex[L]':
        """A label index containing all labels that are inside the specified span of text.

        Parameters
        ----------
        x: Label or int
            Either a label whose location specifies the entire span of text, or the start index of
            the span of text.
        end: int, optional
            The exclusive end index of the span of text if it has not been specified by a label.

        Returns
        -------
        LabelIndex[L]
        """
        ...

    @abc.abstractmethod
    def beginning_inside(self, x: Union[Label, int], end: Optional[int] = None) -> 'LabelIndex[L]':
        """A label index containing all labels whose begin index is inside the specified span of
        text.

        Parameters
        ----------
        x: Label or int
            Either a label whose location specifies the entire span of text, or the start index of
            the span of text.
        end: int, optional
            The exclusive end index of the span of text if it has not been specified by a label.

        Returns
        -------
        LabelIndex[L]
        """
        ...

    def before(self, x: Union[Label, int]) -> 'LabelIndex[L]':
        """A label index containing all labels that are before a label's location in text or
        an index in text.

        Parameters
        ----------
        x: Label or int
            Either a label whose begin indicates a text index to use, or the text index itself.

        Returns
        -------
        LabelIndex[L]
        """
        try:
            index = x.start_index
        except AttributeError:
            index = x
        return self.inside(0, index)

    def after(self, x: Union[Label, int]) -> 'LabelIndex[L]':
        """A label index containing all labels that are after a label's location in text
        or an index in text.

        Parameters
        ----------
        x: Label or int
            Either a label whose end indicates a text index to use, or the text index itself.


        Returns
        -------
        LabelIndex[L]
        """
        try:
            index = x.end_index
        except AttributeError:
            index = x
        return self.inside(index, sys.maxsize)

    @abc.abstractmethod
    def ascending(self) -> 'LabelIndex[L]':
        """This label index sorted according to ascending start and end index.

        Returns
        -------
        LabelIndex[L]
        """
        ...

    @abc.abstractmethod
    def descending(self) -> 'LabelIndex[L]':
        """This label index sorted according to descending start index and ascending end index.

        Returns
        -------
        LabelIndex[L]
        """
        ...


class Labeler(abc.ABC, Generic[L]):
    """Object provided by :func:`~Document.get_labeler` which is responsible for adding labels to a
    label index on a document.

    See Also
    --------
    GenericLabel : The default Label type used if another registered label type is not specified.
    """

    @abc.abstractmethod
    def __call__(self, *args, **kwargs) -> L:
        """Calls the constructor for the label type adding it to the list of labels to be uploaded.

        Parameters
        ----------
        args
            Arguments raise passed to the label type's constructor.
        kwargs
            Keyword arguments passed to the label type's constructor.

        Returns
        -------
        Label
            The object that was created by the label type's constructor.

        Examples
        --------
        >>> labeler(0, 25, some_field='some_value', x=3)
        GenericLabel(start_index=0, end_index=25, some_field='some_value', x=3)
        """
        ...


class GenericLabel(Label):
    """Default implementation of the Label class which uses a dictionary to store attributes.

    Will be suitable for the majority of use cases for labels.

    Parameters
    ----------
    start_index : int, required
        The index of the first character in text to be included in the label.
    end_index : int, required
        The index after the last character in text to be included in the label.
    kwargs : dynamic
        Any other fields that should be added to the label.


    Examples
    --------
    >>> pos_tag = pos_tag_labeler(0, 5)
    >>> pos_tag.tag = 'NNS'
    >>> pos_tag.tag
    'NNS'

    >>> pos_tag2 = pos_tag_labeler(6, 10, tag='VB')
    >>> pos_tag2.tag
    'VB'

    """

    def __init__(self, start_index: int, end_index: int, **kwargs):
        self.__dict__['fields'] = dict(kwargs)
        self.fields['start_index'] = start_index
        self.fields['end_index'] = end_index

    @property
    def start_index(self):
        return self.fields['start_index']

    @start_index.setter
    def start_index(self, value):
        self.fields['start_index'] = value

    @property
    def end_index(self):
        return self.fields['end_index']

    @end_index.setter
    def end_index(self, value):
        self.fields['end_index'] = value

    def __getattr__(self, item):
        fields = self.__dict__['fields']
        if item == 'fields':
            return fields
        else:
            return fields[item]

    def __setattr__(self, key, value):
        """Sets the value of a field on the label.

        Parameters
        ----------
        key: str
            Name of the string.
        value: json serialization compliant
            Some kind of value, must be able to be serialized to json.

        """
        self.__dict__['_fields'][key] = value


class ProtoLabelAdapter(abc.ABC):
    """Responsible for serialization and deserialization of non-standard label types.

    See Also
    --------
    proto_label_adapter: The decorator used to create

    """

    @abc.abstractmethod
    def create_label(self, *args, **kwargs):
        ...

    @abc.abstractmethod
    def create_index_from_response(self, response):
        ...

    @abc.abstractmethod
    def add_to_message(self, labels, request):
        ...


class Processor(metaclass=abc.ABCMeta):
    """Abstract base class for an event processor.
    """

    @property
    def status(self) -> str:
        """Returns the current status of the processor for health checking.

        Returns
        -------
        str
            One of "SERVING", "NOT_SERVING", "UNKNOWN".

        """
        return "SERVING"

    @abc.abstractmethod
    def process(self, event: Event, params: Dict[str, str]) -> Optional[Dict[str, str]]:
        """Performs processing on an event.

        Parameters
        ----------
        event : Event
            The event to process.
        params: dict
            Generic parameters.


        Returns
        -------
        dict
            Generic results.

        """
        ...

    def close(self):
        """Used for cleaning up anything that needs to be cleaned up.

        """
        pass


class DocumentProcessor(Processor, metaclass=abc.ABCMeta):
    """Abstract base class for a document processor, a :obj:`Processor` which automatically
    retrieves a :obj:`Document` from the event using the processing parameter 'document_name'.
    """

    def process(self, event: Event, params: Dict[str, str]) -> Optional[Dict[str, str]]:
        """Calls the subclass's implementation of :func:`process_document` """
        document = event[params['document_name']]
        return self.process_document(document, params)

    @abc.abstractmethod
    def process_document(self,
                         document: Document,
                         params: Dict[str, str]) -> Optional[Dict[str, str]]:
        """Implemented by the subclass, your processor.

        Parameters
        ----------
        document: Document
            The document object to be passed.
        params: typing.Dict[str, str]
            Processing parameters. A dictionary of strings mapped to strings.
            This may be replaced with a json struct or another option that allows non-string
            parameters.

        Returns
        -------
        typing.Dict[str, str], optional
            A dictionary of strings mapped to strings. This likewise may be replaced with a json
            struct at a later point.

        """
        ...


class Server(abc.ABC):
    """A server that hosts an events or processing service.

    """

    @abc.abstractmethod
    def start(self, *, register: bool):
        """Starts the service and registers it with the service discovery framework.

        Parameters
        ----------
        register: bool
            If the service should be registered for service discovery.
        """
        ...

    @abc.abstractmethod
    def stop(self, *, grace: float = None):
        """De-registers (if registered with service discovery) the service and immediately stops
        accepting requests, completely stopping the service after a specified `grace` time.

        During the grace period the server will continue to process existing requests, but it will
        not accept any new requests. This function is idempotent, multiple calls will shutdown
        the server after the soonest grace to expire, calling the shutdown event for all calls to
        this function.

        Parameters
        ----------
        grace: float, optional
            The grace period that the server should continue processing requests for shutdown.

        Returns
        -------
        threading.Event
            A shutdown event for the server.
        """
        ...


class ProcessingResult(NamedTuple):
    """The result of processing one document or event

    Attributes
    ----------
    identifier: str
        The id of the processor with respect to the pipeline.
    results: dict
        The json object returned by the processor as its results
    timing_info: dict[str, datetime.timedelta]
        A dictionary of the times taken processing this document
    created_indices: dict[str, list[str]]
        Any indices that have been added to documents by this processor.

    """
    identifier: str
    results: Dict
    timing_info: Dict
    created_indices: Dict[str, List[str]]


class TimerStats(NamedTuple):
    """Statistics about a labeled runtime.

    Attributes
    ----------
    mean: datetime.timedelta
        The mean duration.
    std: datetime.timedelta
        The standard deviation of all times.
    max: datetime.timedelta
        The maximum of all times.
    min: datetime.timedelta
        The minimum of all times.
    sum: datetime.timedelta
        The sum of all times.

    """
    mean: 'datetime.timedelta'
    std: 'datetime.timedelta'
    max: 'datetime.timedelta'
    min: 'datetime.timedelta'
    sum: 'datetime.timedelta'


class AggregateTimingInfo(NamedTuple):
    """Collection of all of the timing info for a specific processor.

    Attributes
    ----------
    identifier: str
        The id of the processor with respect to the pipeline.
    timing_info: dict[str, TimerStats]
        A map from all of the timer labels to their aggregate values.
    """
    identifier: str
    timing_info: Dict[str, TimerStats]

    def print_times(self):
        print(self.identifier)
        print("-------------------------------------")
        for key, stats in self.timing_info.items():
            print(f"  [{key}]\n"
                  f"    mean: {str(stats.mean)}\n"
                  f"    std: {str(stats.std)}\n"
                  f"    min: {str(stats.min)}\n"
                  f"    max: {str(stats.max)}\n"
                  f"    sum: {str(stats.sum)}")
        print("")


class Pipeline(metaclass=abc.ABCMeta):
    """An active, connected, pipeline ready to process events and documents.

    """

    @abc.abstractmethod
    def add_processor(self, name: str, address: str = None, *, identifier: str = None,
                      params: Dict[str, str] = None):
        """Adds a processor in serial to the pipeline.

        Parameters
        ----------
        name: str
            The processor as declared using the :func:`processor` decorator.
        address: str, optional
            Optionally an address to use, will use service discovery configuration to locate
            processors if this is None / omitted.
        identifier: str
            How the processor's results will be identified locally.
        params: dict, optional
            An optional parameter dictionary that will be passed to the processor as parameters
            with every document.

        """
        ...

    @abc.abstractmethod
    def add_local_processor(self, processor: Processor, identifier: str, events: Events,
                            *, params=None):
        """Adds a processor to the pipeline which will run locally (in the same process as the
        pipeline).

        Parameters
        ----------
        processor: Processor
            The processor instance to run with the pipeline.
        identifier: str
            An identifier for processor in the context of the pipeline.
        events: Events
            The events object that will be used to open copies of the event.
        params: dict, optional
            An optional parameter dictionary that will be passed to the processor as parameters
            with every document.
        """
        ...

    def run(self, target: Union[Event, Document], *, params: Dict = None) -> List[ProcessingResult]:
        """Processes the event/document using all of the processors in the pipeline.

        Parameters
        ----------
        target: Event, Document
            Either an event or a document to process.
        params: dict
            Json object containing params specific to processing this event, the existing params
            dictionary defined in :func:`~PipelineBuilder.add_processor` will be updated with
            the contents of this dict.
        Returns
        -------
        list[ProcessingResult]
            The results of all the processors in the pipeline.

        Examples
        --------
        The statement

        >>> pipeline.run(document)

        with a document parameter is an alias for

        >>> pipeline.run(document.event, params={'document_name': document.document_name})

        The 'document_name' param is used to indicate to :obj:`DocumentProcessor` which document on
        the event to process.

        """
        ...

    def __call__(self, target: Union[Event, Document],
                 *, params: Dict = None) -> List[ProcessingResult]:
        """Alias for :func:`~Pipeline:run`.

        Parameters
        ----------
        target: Event, Document
            Either an event or a document to process.
        params: dict
            Json object containing params specific to processing this event, the existing params
            dictionary defined in :func:`~PipelineBuilder.add_processor` will be updated with
            the contents of this dict.
        Returns
        -------
        list[ProcessingResult]
            The results of all the processors in the pipeline.
        """
        return self.run(target, params=params)

    def processor_timer_stats(self) -> List[AggregateTimingInfo]:
        """Returns the aggregated timing infos for all processors.

        Returns
        -------
        list[AggregateTimingInfo]
            A list of AggregateTimingInfo objects in the same order that they were added to the
            pipeline.

        """
        ...

    def pipeline_timer_stats(self) -> AggregateTimingInfo:
        """The aggregated statistics for the runtime of the entire pipeline.

        Returns
        -------

        """
        ...

    def close(self):
        """Closes any open connections to remote processors.
        """
        ...

    def print_times(self):
        self.pipeline_timer_stats().print_times()
        for pipeline_timer in self.processor_timer_stats():
            pipeline_timer.print_times()

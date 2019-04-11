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
"""Public API and access points for the nlpnewt Framework."""

import abc as _abc
import typing as _typing

from pkg_resources import get_distribution, DistributionNotFound

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    __version__ = "development0"


class Config(_typing.ContextManager, _typing.MutableMapping[_typing.AnyStr, _typing.Any],
             metaclass=_abc.ABCMeta):
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

    @_abc.abstractmethod
    def update_from_yaml(self, path):
        """Updates the configuration by loading and collapsing all of the structures in a yaml file.

        Parameters
        ----------
        path: str
            The path to the yaml file to load.

        """
        raise NotImplementedError


def config() -> Config:
    """Constructs a new `Config` object.

    Returns
    -------
    Config
        Configuration object.

    """
    from nlpnewt import _config
    return _config.get_config()


def events(target=None) -> 'Events':
    """Creates an object that can be used for making requests to an events service.

    Parameters
    ----------
    target: str, optional
        The events service target e.g. 'localhost:9090' or omit/None to use service discovery.

    Returns
    -------
    Events
        An object for interacting with the documents on the documents service.

    Examples
    --------
    Use service discovery to create connection:

    >>> with nlpnewt.events() as events:
    >>>     # use events

    Use address to create connection:

    >>> with nlpnewt.events('localhost:9090') as events:
    >>>     # use events

    """
    from nlpnewt import _events_client
    c = config()  # loads config
    return _events_client.get_events(config=c, address=target)


class Events(_typing.ContextManager, metaclass=_abc.ABCMeta):
    """The object created by :func:`events` to interact with all of the events.

    """

    @_abc.abstractmethod
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
        raise NotImplementedError

    @_abc.abstractmethod
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
        raise NotImplementedError

    @_abc.abstractmethod
    def close(self):
        """Closes the connection to the events service.
        """
        raise NotImplementedError


class Event(_typing.Mapping[str, 'Document'], _typing.ContextManager, metaclass=_abc.ABCMeta):
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
        raise NotImplementedError

    @property
    @_abc.abstractmethod
    def event_id(self) -> str:
        """Returns the globally unique identifier for this event.

        Returns
        -------
        str
            The event ID.
        """
        raise NotImplementedError

    @property
    @_abc.abstractmethod
    def metadata(self) -> _typing.MutableMapping[str, str]:
        """Returns an object that can be used to query and add metadata to the object.

        Returns
        -------
        typing.MutableMapping[str, str]
            An object containing the metadata

        """
        raise NotImplementedError

    @property
    @_abc.abstractmethod
    def created_indices(self) -> _typing.Dict[_typing.AnyStr, _typing.List[_typing.AnyStr]]:
        """Returns a map of label indices that have been added to any document on this event.

        Returns
        -------
        dict[str, list[str]]
            A dictionary of string ``document_name`` to lists of string ``index_name``.

        """
        raise NotImplementedError

    @_abc.abstractmethod
    def close(self) -> None:
        """Closes this event. Lets the event service know that we are done with the event,
        allowing to clean up the event if everyone is done with it.
        """
        raise NotImplementedError

    @_abc.abstractmethod
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
        raise NotImplementedError


class Document(_abc.ABC):
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
    @_abc.abstractmethod
    def event(self) -> Event:
        """Returns the parent event of this document.

        Returns
        -------
        Event
            The event object which contains this document.

        """
        raise NotImplementedError

    @property
    @_abc.abstractmethod
    def document_name(self) -> _typing.AnyStr:
        """The event-unique identifier.

        Returns
        -------

        """
        raise NotImplementedError

    @property
    @_abc.abstractmethod
    def text(self) -> str:
        """Returns the document text, fetching if it is not cached locally.

        Returns
        -------
        str
            The text that the document was created

        """
        raise NotImplementedError

    @property
    @_abc.abstractmethod
    def created_indices(self) -> _typing.List[_typing.AnyStr]:
        """Returns the newly created label indices on this document using a labeler.

        Returns
        -------
        list[str]
            A list of all of the label indices that have created on this document using a labeler.
        """
        raise NotImplementedError

    @_abc.abstractmethod
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
        raise NotImplementedError

    @_abc.abstractmethod
    def get_labeler(self,
                    label_index_name: str,
                    *,
                    distinct: bool = None,
                    label_type_id: str = None) -> _typing.ContextManager['Labeler']:
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
        raise NotImplementedError


class Label(_abc.ABC):
    """An abstract base class for a label of attributes on text.

    """

    @property
    @_abc.abstractmethod
    def start_index(self) -> int:
        """The index of the first character of the text covered by this label"""
        raise NotImplementedError

    @start_index.setter
    @_abc.abstractmethod
    def start_index(self, value: int):
        raise NotImplementedError

    @property
    @_abc.abstractmethod
    def end_index(self) -> int:
        """The index after the last character of the text covered by this label."""
        raise NotImplementedError

    @end_index.setter
    @_abc.abstractmethod
    def end_index(self, value: int):
        raise NotImplementedError

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


_L = _typing.TypeVar('_L', bound=Label)


class LabelIndex(_abc.ABC, _typing.Generic[_L]):
    """A container of labels. Either contains dict objects for standard labels or custom adapter
    labels.

    See Also
    ========
    Document.get_label_index : Method for getting existing label indices.
    Document.get_labeler : Method for adding new label indexes to documents.
    Labeler : Object for adding new label indices to documents.
    """

    @property
    @_abc.abstractmethod
    def distinct(self):
        raise NotImplementedError

    def __getitem__(self, idx: int) -> _L:
        """Returns the label at the specified index.

        Parameters
        ----------
        idx : int
            The index of the label to return.

        Returns
        -------
        Label
            Label of the type in this label index.

        Examples
        --------
        >>> sentence = sentences_index[0]
        """
        raise NotImplementedError

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
        raise NotImplementedError

    def __iter__(self) -> _typing.Iterator[_L]:
        """An iterator of the label objects.

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
        raise NotImplementedError


class Labeler(_abc.ABC, _typing.Generic[_L]):
    """Object provided by :func:`~Document.get_labeler` which is responsible for adding labels to a label index on a document.

    See Also
    --------
    GenericLabel : The default Label type used if another registered label type is not specified.
    """

    @_abc.abstractmethod
    def __call__(self, *args, **kwargs) -> _L:
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
        raise NotImplementedError


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

    def __init__(self, start_index, end_index, **kwargs):
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


class ProtoLabelAdapter(_abc.ABC):
    """Responsible for serialization and deserialization of non-standard label types.

    See Also
    --------
    proto_label_adapter: The decorator used to create

    """

    @_abc.abstractmethod
    def create_label(self, *args, **kwargs):
        raise NotImplementedError

    @_abc.abstractmethod
    def create_index_from_response(self, response):
        raise NotImplementedError

    @_abc.abstractmethod
    def add_to_message(self, labels, request):
        raise NotImplementedError


def proto_label_adapter(label_type_id: str):
    """Registers a :obj:`ProtoLabelAdapter` for a specific identifier.

    When that id is referenced in the document :func:`~Document.get_labeler`
    and  :func:`~Document.get_label_index`.

    Parameters
    ----------
    label_type_id: hashable
        This can be anything as long as it is hashable, good choices are strings or the label types
        themselves if they are concrete classes.

    Returns
    -------
    decorator
        Decorator object which invokes the callable to create the label adapter.

    Examples
    --------
    >>> @nlpnewt.proto_label_adapter("example.Sentence")
    >>> class SentenceAdapter(nlpnewt.ProtoLabelAdapter):
    >>>    # ... implementation of the ProtoLabelAdapter for sentences.

    >>> with document.get_labeler("sentences", "example.Sentence") as labeler
    >>>     # add labels

    >>> label_index = document.get_label_index("sentences", "example.Sentence")
    >>>     # do something with labels
    """
    from nlpnewt import _events_client

    def decorator(func: _typing.Callable[[], ProtoLabelAdapter]):
        _events_client.register_proto_label_adapter(label_type_id, func())
        return func

    return decorator


class Processor(metaclass=_abc.ABCMeta):
    """Abstract base class for an event processor.

    Attributes
    ----------
    status
    """
    arguments_parser = None  #: Used internally by the :func:`processor` decorator, do not override.

    @property
    def status(self) -> str:
        """Returns the current status of the processor for health checking.

        Returns
        -------
        str
            One of "SERVING", "NOT_SERVING", "UNKNOWN".

        """
        return "SERVING"

    @_abc.abstractmethod
    def process(self,
                event: Event,
                params: _typing.Dict[str, str]) -> _typing.Optional[_typing.Dict[str, str]]:
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
        raise NotImplementedError

    def close(self):
        """Used for cleaning up anything that needs to be cleaned up.

        """
        pass


class DocumentProcessor(Processor, metaclass=_abc.ABCMeta):
    """Abstract base class for a document processor, a :obj:`Processor` which automatically
    retrieves a :obj:`Document` from the event using the processing parameter 'document_name'.
    """

    def process(self,
                event: Event,
                params: _typing.Dict[str, str]) -> _typing.Optional[_typing.Dict[str, str]]:
        """Calls the subclass's implementation of :func:`process_document` """
        document = event[params['document_name']]
        return self.process_document(document, params)

    @_abc.abstractmethod
    def process_document(
            self,
            document: Document,
            params: _typing.Dict[str, str]
    ) -> _typing.Optional[_typing.Dict[str, str]]:
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
        raise NotImplementedError


def processor(name: str):
    """Decorator which attaches a service name to a processor for launching with the nlpnewt command
    line


    Parameters
    ----------
    name: str
        Identifying service name both for launching via command line and for service registration.

        Should be a mix of alphanumeric characters and dashes so that they play nice with the DNS
        name requirements of stuff like Consul.

        This can be modified for service registration at runtime by overriding
        :func:'Processor.registration_processor_name'.

    Returns
    -------
    decorator
        This decorator should be applied to a 0-arg
        (or 0 and 1-arg to handle additional command line arguments) functions that return
        either :obj:`Processor` or :obj:`DocumentProcessor` types.

    Examples
    --------
    >>> @nlpnewt.processor('example-text-converter')
    >>> class TextConverter(nlpnewt.Processor):
    >>>     def __init__(self):
    >>>         # not necessary to have arguments parameter.

    or

    >>> @nlpnewt.processor('example-sentence-detector')
    >>> class SentenceDetector(nlpnewt.DocumentProcessor):
    >>>     def __init__(self, args=None):
    >>>         # parse and use args

    or

    >>> @nlpnewt.processor('parameterizable-processor')
    >>> def create_from_args(args=None):
    >>>     parser = argparse.ArgumentParser()
    >>>     parser.add_argument('-f', help='file')
    >>>     args = parser.parse_args(args)
    >>>     return ParameterizableProcessor(args.f)

    These are all valid ways of registering processors.

    """

    def decorator(func):
        from nlpnewt import _processing
        _processing.register_processor(name, func)
        return func

    return decorator


class Server(_abc.ABC):
    """A server that hosts an events or processing service.

    """

    @_abc.abstractmethod
    def start(self, *, register: bool):
        """Starts the service and registers it with the service discovery framework.

        Parameters
        ----------
        register: bool
            If the service should be registered for service discovery.
        """
        raise NotImplementedError

    @_abc.abstractmethod
    def stop(self, *, grace=None):
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
        raise NotImplementedError


def stopwatch(key: str) -> _typing.ContextManager:
    """Starts a timer for the current processor.

    The timer starts running immediately, and it will save a time when the context is exited
    with the given key to timing info that will be returned by the processor.

    Parameters
    ----------
    key: str
        The key to add the elapsed time to the process call's timing info.

    Examples
    --------
    >>> with nlpnewt.stopwatch('subtask1'):
    >>>    # do subtask

    """
    from nlpnewt import _processing
    return _processing.stopwatch(key)


class ProcessingResult(_typing.NamedTuple):
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
    results: _typing.Dict
    timing_info: _typing.Dict
    created_indices: _typing.Dict[str, _typing.List[str]]


class TimerStats(_typing.NamedTuple):
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


class AggregateTimingInfo(_typing.NamedTuple):
    """Collection of all of the timing info for a specific processor.

    Attributes
    ----------
    identifier: str
        The id of the processor with respect to the pipeline.
    timing_info: dict[str, TimerStats]
        A map from all of the timer labels to their aggregate values.
    """
    identifier: str
    timing_info: _typing.Dict[str, TimerStats]

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


class Pipeline(metaclass=_abc.ABCMeta):
    """An active, connected, pipeline ready to process events and documents.

    """

    @_abc.abstractmethod
    def add_processor(self, name: str, address: str = None,
                      *, identifier: str = None, params: _typing.Dict = None):
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
        raise NotImplementedError

    @_abc.abstractmethod
    def add_local_processor(self,
                            processor: Processor,
                            identifier: str,
                            events: Events,
                            *,
                            params=None):
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
        raise NotImplementedError

    def run(self, target: _typing.Union[Event, Document],
            *, params: _typing.Dict = None) -> _typing.List[ProcessingResult]:
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
        raise NotImplementedError

    def __call__(self, target: _typing.Union[Event, Document],
                 *, params: _typing.Dict = None) -> _typing.List[ProcessingResult]:
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

    def processor_timer_stats(self) -> _typing.List[AggregateTimingInfo]:
        """Returns the aggregated timing infos for all processors.

        Returns
        -------
        list[AggregateTimingInfo]
            A list of AggregateTimingInfo objects in the same order that they were added to the
            pipeline.

        """
        raise NotImplementedError

    def pipeline_timer_stats(self) -> TimerStats:
        """The aggregated statistics for the runtime of the entire pipeline.

        Returns
        -------

        """
        raise NotImplementedError

    def close(self):
        """Closes any open connections to remote processors.
        """
        raise NotImplementedError

    def print_times(self):
        self.pipeline_timer_stats().print_times()
        for pipeline_timer in self.processor_timer_stats():
            pipeline_timer.print_times()


def pipeline(processor_ids=None) -> Pipeline:
    """Creates an object which can be used to build and run a pipeline of document processors.

    Returns
    -------
    Pipeline
        The object which encapsulates a pipeline configuration


    Examples
    --------
    Remote pipeline with name discovery:

    >>> with nlpnewt.pipeline() as pipeline, nlpnewt.events() as events:
    >>>     pipeline.add_processor('processor-1-id')
    >>>     pipeline.add_processor('processor-2-id')
    >>>     pipeline.add_processor('processor-3-id')
    >>>     for txt in txts:
    >>>         with events.open_event() as event:
    >>>             document = event.add_document('plaintext', txt)
    >>>             results = pipeline.run(document)

    Remote pipeline using addresses:

    >>> with nlpnewt.pipeline() as pipeline, nlpnewt.events('localhost:50051') as events:
    >>>     pipeline.add_processor('processor-1-name', 'localhost:50052')
    >>>     pipeline.add_processor('processor-2-name', 'localhost:50053')
    >>>     pipeline.add_processor('processor-3-name', 'localhost:50054')
    >>>     for txt in txts:
    >>>         event = events.open_event()
    >>>         document = event.add_document('plaintext', txt)
    >>>         results = pipeline.run(document)

    The statement

    >>> pipeline.run(document)

    with a document parameter is an alias for

    >>> pipeline.run(document.event, params={'document_name': document.document_name})

    The 'document_name' param is used to indicate to :obj:`DocumentProcessor` which document on
    the event to process.

    """
    from nlpnewt import _processing
    c = config()
    return _processing.create_pipeline(c, processor_ids)


def events_service_name():
    """The service name used for the events service.

    Returns
    -------
    str
        Service name.

    """
    return 'nlpnewt-events'


def processing_service_tag():
    """The service name used for all deployed processors.

    Returns
    -------
    str
        Service name.

    """
    return 'v1-nlpnewt-processor'


def events_server(address: _typing.AnyStr, port: int, *, workers: int = 10) -> Server:
    """Creates a events server that will host the events service at the specified address.

    Parameters
    ----------
    address: str
        The address / hostname / IP to host the server on.
    port: int
        The port to host the server on.
    workers: int, optional
        The number of workers that should handle requests.

    Returns
    -------
    Server
        Server object that can be used to start and stop the server.

    """
    from nlpnewt import _events_service
    c = config()
    return _events_service.create_server(c, address, port, workers)


def processor_server(processor_name: str,
                     address: str,
                     port: int,
                     *,
                     processor_id=None,
                     workers=10,
                     events_address=None,
                     params=None,
                     args=None,
                     kwargs=None) -> Server:
    """Creates a server that will host a processor as a service.

    Parameters
    ----------
    processor_name: str
        The name of the processor as regsitered with :func:`processor`.
    address: str
        The address / hostname / IP to host the server on.
    port: int
        The port to host the server on.
    processor_id: str, optional
        The identifier to register the processor under, if omitted the processor name will be used.
    workers: int, optional
        The number of workers that should handle requests.
    params: dict
        A set of default parameters that will be passed to the processor every time it runs.
    events_address: str, optional
        The address of the events server, or omitted / None if the events service should be
        discovered.
    args: list[str]
        Any additional command line arguments that should be passed to the processor on
        instantiation.
    kwargs: dict
        Any additional keyword arguments that should be passed to the constructor for the processor

    Returns
    -------
    Server
        Server object that can be used to start and stop the server.

    """
    from nlpnewt import _processing
    c = config()
    runner = _processing.create_runner(config=c,
                                       events_address=events_address,
                                       processor_name=processor_name,
                                       identifier=processor_id, params=params,
                                       processor_args=args, processor_kwargs=kwargs)
    return _processing.create_server(config=c,
                                     address=address,
                                     port=port,
                                     workers=workers,
                                     runner=runner)


def generic_label_id():
    """The ID used to register the generic label adapter.

    Returns
    -------
    str
        Generic labels ID.

    """
    return 'nlpnewt.labels.Generic'


def distinct_generic_label_id():
    """The ID used to register distinct generic labels.

    Returns
    -------
    str
        Distinct generic labels ID.

    """
    return 'nlpnewt.labels.DistinctGeneric'


@proto_label_adapter('nlpnewt.labels.Generic')
def generic_adapter():
    from nlpnewt import _labels
    return _labels.generic_adapter


@proto_label_adapter('nlpnewt.labels.DistinctGeneric')
def distinct_generic_adapter():
    from nlpnewt import _labels
    return _labels.distinct_generic_adapter


_ONE_DAY_IN_SECONDS = 60 * 60 * 24


def run_events_server(args):
    """Runs the documents service, blocking until keyboard interrupt

    Parameters
    ----------
    args
        Command line arguments.
    """
    from nlpnewt import _events_service, _utils
    import time
    with config() as c:
        if args.config is not None:
            c.update_from_yaml(args.config)
        server = events_server(args.address, args.port, workers=args.workers)
        server.start(register=args.register)

        while True:
            try:
                time.sleep(_ONE_DAY_IN_SECONDS)
            except KeyboardInterrupt:
                print('stopping server')
                server.stop()
                return


def run_processor_service(args):
    """Runs a processor, blocking until keyboard interrupt

    Parameters
    ----------
    args
        Command line arguments.
    """
    from nlpnewt import _processing, _utils
    import importlib
    import time
    if args.module is not None:
        importlib.import_module(args.module)

    with config() as c:
        if args.config is not None:
            c.update_from_yaml(args.config)
        processor_name = args.name
        server = processor_server(processor_name,
                                  address=args.address,
                                  port=args.port,
                                  workers=args.workers,
                                  processor_id=args.identifier,
                                  events_address=args.events_address,
                                  args=args.args)
        server.start(register=args.register)
        while True:
            try:
                time.sleep(_ONE_DAY_IN_SECONDS)
            except KeyboardInterrupt:
                print('stopping server')
                server.stop()
                return


def main(args=None):
    import argparse as argparse
    parser = argparse.ArgumentParser(description='Starts a nlpnewt grpc server.',
                                     allow_abbrev=False)
    subparsers = parser.add_subparsers(title='sub-commands', description='valid sub-commands')

    # Arguments shared by service sub-commands
    service_parser = argparse.ArgumentParser(add_help=False)
    service_parser.add_argument('--address', '-a', default="127.0.0.1", metavar="HOST",
                                help='the address to serve the service on')
    service_parser.add_argument('--port', '-p', type=int, default=0, metavar="PORT",
                                help='the port to serve the service on')
    service_parser.add_argument('--workers', '-w', type=int, default=10,
                                help='number of worker threads to handle requests')
    service_parser.add_argument('--register', '-r', action='store_true',
                                help='whether to register the service with the configured service '
                                     'discovery')
    service_parser.add_argument("--config", '-c', default=None,
                                help="path to config file")

    # Documents service sub-command
    documents_parser = subparsers.add_parser('events', parents=[service_parser],
                                             help='starts a events service')
    documents_parser.set_defaults(func=run_events_server)

    # Processing services sub-command
    processors_parser = subparsers.add_parser('processor', parents=[service_parser],
                                              help='starts a processor service')
    processors_parser.add_argument('--events-address', '--events', '-e', default=None,
                                   help='address of the events service to use, '
                                        'omit to use discovery')
    processors_parser.add_argument('--name', '-n', required=True,
                                   help='The name the processor is registered under using the '
                                        'processor decorator.')
    processors_parser.add_argument('--identifier', '-i',
                                   help="Optional argument if you want the processor to register "
                                        "under a different identifier than its name.")
    processors_parser.add_argument('--module', '-m', default=None,
                                   help='A python module to load to trigger the processor '
                                        'decorator')
    processors_parser.add_argument('args', nargs='*', default=None,
                                   help='args that will be passed to the processor')
    processors_parser.set_defaults(func=run_processor_service)

    # parse and execute
    args = parser.parse_args(args)
    args.func(args)

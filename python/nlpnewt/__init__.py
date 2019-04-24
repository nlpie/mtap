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

import typing

from pkg_resources import get_distribution, DistributionNotFound

from . import _config
from . import _discovery
from . import _events_client
from . import _events_service
from . import _processing
from . import _utils
from . import base
from ._labels import GenericLabel
from ._labels import distinct_label_index
from ._labels import proto_label_adapter
from ._labels import standard_label_index

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    __version__ = "development0"

__all__ = [
    '__version__',
    'config',
    'events',
    'distinct_label_index',
    'standard_label_index',
    'GenericLabel',
    'proto_label_adapter',
    'processor',
    'stopwatch',
    'pipeline',
    'events_server',
    'processor_server'
]


def config() -> base.Config:
    """Constructs a new `Config` object.

    Returns
    -------
    nlpnewt.base.Config
        Configuration object.

    """
    return _config.get_config()


def events(target=None) -> base.Events:
    """Creates an object that can be used for making requests to an events service.

    Parameters
    ----------
    target: str, optional
        The events service target e.g. 'localhost:9090' or omit/None to use service discovery.

    Returns
    -------
    nlpnewt.base.Events
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
    c = config()  # loads config
    return _events_client.get_events(config=c, address=target)


L = typing.TypeVar('L', bound=base.Label)


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
        _processing.register_processor(name, func)
        return func

    return decorator


def stopwatch(key: str) -> typing.ContextManager:
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
    return _processing.stopwatch(key)


def pipeline() -> base.Pipeline:
    """Creates an object which can be used to build and run a pipeline of document processors.

    Returns
    -------
    nlpnewt.base.Pipeline
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
    c = config()
    return _processing.create_pipeline(c)


def events_server(address: typing.AnyStr, port: int, *, workers: int = 10) -> base.Server:
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
    nlpnewt.base.Server
        Server object that can be used to start and stop the server.

    """
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
                     kwargs=None) -> base.Server:
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
    nlpnewt.base.Server
        Server object that can be used to start and stop the server.

    """
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

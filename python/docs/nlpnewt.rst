.. Copyright 2018 Regents of the University of Minnesota.

.. Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

..     http://www.apache.org/licenses/LICENSE-2.0

.. Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

nlpnewt
=======
.. module:: nlpnewt

Quickstart
----------

Interacting with the Events Service
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In nlpnewt, the top level data object is an ``Event``. An event's primary function is to store
documents, it functions as a dictionary / map of document names (identifiers for specific
types of documents) to documents. Events are stored on a service called the "events service" which
stores and provides the data associated with an event for the lifetime of the event.
The :obj:`Event` python object functions as both a client to the events service and as a cache of
data stored locally.

To connect to an events service the :obj:`nlpnewt.Events` class is used, which either takes an
address to the events service, or optionally will use service discovery such
as :ref:`discovery <consul>`::

 with nlpnewt.events(address) as events:
     with events.open_event('1') as event:

.. Should maybe add something about metadata here.

On events, there are documents, which are encapsulated in a python object implementing
:obj:`Document`.  Documents have two purposes, to store the text of the document, which it does on
the immutable property :func:`Document.text`, and to store "label indices". A :obj:`LabelIndex` is
an immutable, ordered set of :obj:`Label` objects.

To create a document on an event, the :func:`Event.add_document` is used. This function takes the
document name and text and adds it to the event as a :obj:`Document` object::

 document = event.add_document('plaintext', some_text_str)

To retrieve an existing document from an event such as one created by a client or another
processor, the index accessor :func:`Event.__getitem__` is used::

 document = event['plaintext']



To add new label indexes to the document, the :obj:`Labeler` type is used. :obj:`Labeler` is a
function which passes its arguments to a registered function which returns an instance of a `Label`
subclass. It internally keeps track of all labels that are added, uploading them to the server when
the `with` block is exited. By default is :obj:`GenericLabel` is used, which can accept dynamic
fields in the constructor. Custom label types can be used, even that use custom serialization to /
from protocol buffers, for more information see `Custom Label Types`_::

 with document.get_labeler('sentences') as labeler:
     labeler(0, 5)
     labeler(6, 20)



To retrieve existing label indices, use the :func:`Document.get_label_index` function::

 sentences = document.get_label_index('sentences')

 for sentence in sentences:
    print(sentence.start_index)
    print(sentence.end_index)

Currently label indices only function as iterables of the sorted labels that were originally added
to them, functionality for sorting, searching, and subsetting will be added in the future.

Labels and Label Indices that have been uploaded to the events service are effectively immutable,
any changes to the labels and label indices on a client will not be propogated to the events
service. This makes parallelism and debugging much easier, as you don't have the issues with objects
which may have many downstream pipeline dependencies changing after things have already been
computed using their original values.

Writing a processor
^^^^^^^^^^^^^^^^^^^

To write a document processor, create a subclass of :obj:`DocumentProcessor`
decorated with the ``@nlpnewt.processor`` decorator::

 @nlpnewt.processor('my-processor')
 class MyProcessor(nlpnewt.DocumentProcessor):
      def __init__(args=None):
          if args is not None:
              # can parse args into configuration for the processor

      def process_document(self, document, params):
          # do things to the document

``DocumentProcessor`` is an implementation of the :obj:`Processor` class, the base class for
processing events. ``DocumentProcessor`` processes a specific document on events indicated by a
`document_name` parameter. More info about this parameterization is in the
`Creating Pipelines`_ section.

If a processor needs to manipulate multiple ``Document`` objects on the same event, such as in text
pre-processing, conversion, or translation, the ``Processor`` base class can be used.

For more information about writing processors, look at the documentation for :obj:`Processor` and
:func:`~DocumentProcessor.processor_document`. When your processor is deployed, each time the
service receives a request for to a process a document, it will automatically use its connection
to the events service to retrieve the document and pass it to the `process_document` method.

Creating Pipelines
^^^^^^^^^^^^^^^^^^

Pipelines are created using the :func:`pipeline_builder` function which returns a
:obj:`PipelineBuilder` object. For usage see the documentation for :func:`pipeline_builder`.

Command-Line Utility
--------------------

Running Events Service
^^^^^^^^^^^^^^^^^^^^^^

usage:

.. code-block:: text

 python -m nlpnewt events [-h] [--address ADDRESS] [--port PORT]
                          [--workers WORKERS] [--register] [--config CONFIG]

 optional arguments:
  -h, --help            show this help message and exit
  --address ADDRESS, -a ADDRESS
                        the address to serve the service on
  --port PORT, -p PORT  the port to serve the service on
  --workers WORKERS, -w WORKERS
                        number of worker threads to handle requests
  --register, -r        whether to register the service with the configured
                        service discovery
  --config CONFIG, -c CONFIG
                        path to config file


Running Processors
^^^^^^^^^^^^^^^^^^

usage:

.. code-block:: text

 python -m nlpnewt processor [-h] [--address ADDRESS] [--port PORT]
                             [--workers WORKERS] [--register]
                             [--config CONFIG]
                             [--events-address EVENTS_ADDRESS] --name NAME
                             [--module MODULE]
                             [args [args ...]]

 positional arguments:
  args                  args that will be passed to the processor

 optional arguments:
  -h, --help            show this help message and exit
  --address ADDRESS, -a ADDRESS
                        the address to serve the service on
  --port PORT, -p PORT  the port to serve the service on
  --workers WORKERS, -w WORKERS
                        number of worker threads to handle requests
  --register, -r        whether to register the service with the configured
                        service discovery
  --config CONFIG, -c CONFIG
                        path to config file
  --events-address EVENTS_ADDRESS, --events EVENTS_ADDRESS, -e EVENTS_ADDRESS
                        address of the events service to use, omit to use
                        discovery
  --name NAME, -n NAME  The name the processor is registered under using
                        the processor decorator.
  --module MODULE, -m MODULE
                        A python module to load to trigger the
                        processor decorator

Examples
--------

A hello world tutorial on creating and running a processor can be found at :ref:`tutorial <tutorial>`.

Examples can be found here_.

.. _here: https://github.umn.edu/NLPIE/nlpnewt/tree/master/python/nlpnewt/examples


API Documentation
-----------------

Events service client, documents
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: Events
.. autoclass:: nlpnewt.events.Event
.. autoclass:: nlpnewt.events.Document

Labels on text
^^^^^^^^^^^^^^
.. autoclass:: nlpnewt.labels.Label
.. autoclass:: nlpnewt.labels.Location
.. autoclass:: nlpnewt.events.Labeler
.. autoclass:: GenericLabel
.. autoclass:: nlpnewt.label_indices.LabelIndex

Custom Label Types
^^^^^^^^^^^^^^^^^^
.. autofunction:: proto_label_adapter
.. autoclass:: nlpnewt.events.ProtoLabelAdapter

Creating Processors
^^^^^^^^^^^^^^^^^^^
.. autofunction:: processor
.. autoclass:: nlpnewt.processing.EventProcessor
.. autoclass:: nlpnewt.processing.DocumentProcessor
.. autoclass:: nlpnewt.processing.ProcessorContext

Running Services
^^^^^^^^^^^^^^^^
.. autoclass:: EventsServer
.. autoclass:: ProcessorServer

Running a pipeline
^^^^^^^^^^^^^^^^^^
.. autoclass:: Pipeline
.. autoclass:: nlpnewt.processing.ProcessingResult
.. autoclass:: nlpnewt.processing.TimerStats
.. autoclass:: nlpnewt.processing.AggregateTimingInfo

Configuration
^^^^^^^^^^^^^
.. autoclass:: Config

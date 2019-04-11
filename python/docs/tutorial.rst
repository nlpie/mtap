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

.. _tutorial:

Tutorial
========

Requirements
------------

- Python 3.6 or later

Installing nlpnewt
------------------

To install nlpnewt run the following:

.. code-block:: bash

  pip install nlpnewt.tgz

This is an sdist for now, but will be on PyPi eventually.

Creating a processor
----------------------

We will be creating a document processor which simply writes a hello world label to a document.

To start, create a file named ``hello.py``, this file will contain our processor:

.. code-block:: python

 import nlpnewt

 @nlpnewt.processor('hello')
 class HelloProcessor(nlpnewt.DocumentProcessor):

     def process_document(self, document, params):
         with document.get_labeler('hello') as hello_labeler:
             text = document.text

             hello_labeler(0, len(text), response='Hello ' + text + '!')

This file receives a request to process a document, and then labels that documents text with
a hello response.

To host the processor, run the following commands in terminal windows (they run in the foreground)

.. code-block:: bash

 python -m nlpnewt events -a localhost -p 9090

 python -m nlpnewt processor -a localhost -p 9091 -e localhost:9090 -m hello -n hello

In both calls, ``-a`` and ``-p`` are the host and port respectively. ``-e`` is the address for the
events server, ``-m`` is a python module to load (it will load hello.py) and ``-n`` is the name of
the processor to launch.

Running the processor
---------------------

To run the processor, create another file ``pipeline.py``:

.. code-block:: python

 import nlpnewt

 with nlpnewt.events('localhost:9090') as events, nlpnewt.pipeline() as pipeline:
     pipeline.add_processor('hello', 'localhost:9091')
     event = events.open_event('1')
     document = event.add_document('name', 'YOUR NAME')
     pipeline.process_document(document)
     index = document.get_label_index('hello')
     for label in index:
         print(label.response)

To run this pipeline type

.. code-block:: bash

 python pipeline.py


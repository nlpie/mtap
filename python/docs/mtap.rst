****
mtap
****
.. module:: mtap

.. contents::

Running Events Service
======================

usage:

.. code-block:: text

 python -m mtap events [-h] [--address ADDRESS] [--port PORT]
                          [--workers WORKERS] [--register] [--config CONFIG]

 optional arguments:
  -h, --help            show this help message and exit
  --address ADDRESS, -a ADDRESS
                        the address to serve the service on
  --port PORT, -p PORT  the port to serve the service on
  --workers WORKERS, -w WORKERS
                        number of worker threads to handle requests
  --config CONFIG, -c CONFIG
                        path to config file


Events service client, documents
================================
.. autofunction:: events_client
.. autoclass:: mtap.types.EventsClient
   :show-inheritance:
   :members:
.. autoclass:: Event
   :members:
.. autoclass:: Document
   :members:
.. autoclass:: mtap.types.Labeler
   :members:

Labels
======
.. autoclass:: mtap.types.Label
   :members:
.. autoclass:: Location
   :members:
.. autofunction:: label
.. autoclass:: GenericLabel
   :members:
   :show-inheritance:

Label Indices
=============
Label indices are normally retrieved via the :attr:`~mtap.Document.labels` property, but
they can be created independently of documents as well.

.. autofunction:: label_index
.. autoclass:: mtap.types.LabelIndex
   :members:

Configuration
=============
.. module:: mtap
   :noindex:
.. autoclass:: Config

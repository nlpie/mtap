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

mtap.io
=======
.. module:: mtap.io

.. contents::

Serialization
-------------

.. automodule:: mtap.io.serialization
   :no-members:

.. autoclass:: mtap.io.serialization.SerializationProcessor
   :exclude-members: process

.. autoclass:: mtap.io.serialization.Serializer

Serialization Helpers
^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: mtap.io.serialization.event_to_dict

.. autofunction:: mtap.io.serialization.document_to_dict

.. autofunction:: mtap.io.serialization.label_index_to_dict

Deserialization Helpers
^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: mtap.io.serialization.dict_to_event

.. autofunction:: mtap.io.serialization.dict_to_document

.. autofunction:: mtap.io.serialization.dict_to_label_index

BRAT
----


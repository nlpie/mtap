mtap.serialization
==================

Serialization
-------------
.. automodule:: mtap.serialization
.. autoclass:: SerializationProcessor
   :members:
.. autoclass:: Serializer
   :members:

Built-In Serializers
^^^^^^^^^^^^^^^^^^^^
.. autodata:: JsonSerializer
   :no-value:
.. autodata:: YamlSerializer
   :no-value:
.. autodata:: PickleSerializer
   :no-value:
.. autofunction:: get_serializer

Helpers
^^^^^^^
.. autofunction:: event_to_dict
.. autofunction:: dict_to_event
.. autofunction:: document_to_dict
.. autofunction:: dict_to_document
***************
mtap.processing
***************

.. module:: mtap.processing

Processor Abstract Classes
==========================

.. autoclass:: Processor
   :members:
.. autoclass:: mtap.EventProcessor
   :members:
   :show-inheritance:
.. autoclass:: mtap.DocumentProcessor
   :members:
   :show-inheritance:

Processor Utilities
===================

.. autoclass:: Stopwatch
   :members:

Processor Description Decorators
================================
.. automodule:: mtap.descriptors
.. autofunction:: processor
.. autofunction:: parameter
.. autofunction:: labels
.. autofunction:: label_property
.. autoclass:: ProcessorDescriptor
   :members:
.. autoclass:: ParameterDescriptor
   :members:
.. autoclass:: LabelIndexDescriptor
   :members:
.. autoclass:: LabelPropertyDescriptor
   :members:

Running Services
================
.. autofunction:: mtap.processor_parser
.. autofunction:: mtap.run_processor

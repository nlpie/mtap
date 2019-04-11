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

Discovery and API Gateway
=========================
.. _Consul: https://www.consul.io/

NLP-NEWT has support for service discovery using Consul_. When service discovery is used, the
NLP-NEWT Python and Java SDK can find the events service and processors without having to specify
the IP address.

Starting a consul server
^^^^^^^^^^^^^^^^^^^^^^^^
.. _Homebrew: https://brew.sh/
.. _here: https://www.consul.io/docs/install/index.html

Instructions for installing consul are available here_. You can install using Homebrew_ on mac with
"brew install consul" or using a package manager on like for ubuntu "sudo apt install consul".

To start the consul server run:

.. code-block:: bash

 consul agent -dev -ui


This will start a consul server locally. Note that is in development mode, normally consul runs
servers and clients separately, this runs both the client and the server.

Launching the events service using discovery
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

NLP-NEWT will use the configuration for consul specified in nlpnewt

.. code-block:: bash

 python -m nlpnewt events --register


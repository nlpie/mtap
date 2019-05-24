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
import argparse


def service_parser():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--address', '-a', default="127.0.0.1", metavar="HOST",
                        help='the address to serve the service on')
    parser.add_argument('--port', '-p', type=int, default=0, metavar="PORT",
                        help='the port to serve the service on')
    parser.add_argument('--workers', '-w', type=int, default=10,
                        help='number of worker threads to handle requests')
    parser.add_argument('--register', '-r', action='store_true',
                        help='whether to register the service with the configured service '
                             'discovery')
    parser.add_argument("--config", '-c', default=None,
                        help="path to config file")
    return parser

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
"""A framework for developing NLP pipeline components."""

import os

import pkg_resources
import sys
from distutils.command.clean import clean as _clean
from setuptools import setup, find_packages
from setuptools.command.build_py import build_py as _build_py
from setuptools.command.test import test as _test


def generate_proto(source, require=True):
    """Invokes the grpc_tools protobuf compiler to generate _pb2.py and _pb2_grpc.py files from
    the given .proto file.  Does nothing if the output already exists and is newer than
    the input."""

    if not require and not os.path.exists(source):
        return

    output = source.replace(".proto", "_pb2.py").replace("proto/", "")

    if (not os.path.exists(output) or
            (os.path.exists(source) and
             os.path.getmtime(source) > os.path.getmtime(output))):
        print("Generating %s..." % output)

        if not os.path.exists(source):
            sys.stderr.write("Can't find required file: %s\n" % source)
            sys.exit(-1)

        try:
            import grpc_tools.protoc
        except ImportError:
            sys.stderr.write("Can't find grpcio-tools, install using pip")
            sys.exit(-1)

        proto_include = pkg_resources.resource_filename('grpc_tools', '_proto')
        grpc_tools.protoc.main(["-I.",
                                "-I{}".format(proto_include),
                                "-Ithird_party/api-common-protos-0.1.0",
                                "-Iproto",
                                "--python_out=python",
                                "--grpc_python_out=python",
                                source])


class clean(_clean):
    def run(self):
        # Delete generated files in the code tree.
        for (dirpath, dirnames, filenames) in os.walk("python"):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if filepath.endswith("_pb2.py") or filepath.endswith(".pyc") or \
                        filepath.endswith("_pb2_grpc.py"):
                    os.remove(filepath)
        super(clean, self).run()


class build_py(_build_py):
    def run(self):
        generate_proto('proto/nlpnewt/api/v1/events.proto')
        generate_proto('proto/nlpnewt/api/v1/processing.proto')
        super(build_py, self).run()


class test(_test):
    user_options = [("pytest-args=", "a", "Arguments to pass to pytest")]

    def initialize_options(self):
        _test.initialize_options(self)
        self.pytest_args = ""

    def run_tests(self):
        import shlex

        # import here, cause outside the eggs aren't loaded
        import pytest

        errno = pytest.main(shlex.split(self.pytest_args))
        sys.exit(errno)


setup(
    name='nlpnewt',
    use_scm_version={
        "fallback_version": "development0",
        "write_to": "python/nlpnewt/version.py"
    },
    description='A framework for developing NLP pipeline components.',
    author='University of Minnesota NLP/IE Group',
    author_email='nlp-ie@umn.edu',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='nlp grpc microservices',
    package_dir={'': 'python'},
    packages=find_packages(where='python', exclude=['tests']),
    install_requires=[
        'grpcio>=1.20.0',
        'grpcio-health-checking>=1.20.0',
        'protobuf>=3.7.0',
        'pyyaml',
        'python-consul',
        'googleapis-common-protos',
    ],
    setup_requires=[
        'pytest-runner',
        'grpcio-tools',
        'setuptools_scm',
    ],
    tests_require=[
        'pytest',
        'grpcio-testing',
        'requests'
    ],
    extras_require={
        'grpc_tools': ['grpcio-tools'],
        'tests': ['pytest-runner', 'pytest'],
        'docs': ['sphinx', 'sphinx_rtd_theme']
    },
    cmdclass={
        'clean': clean,
        'build_py': build_py,
        'test': test
    }
)

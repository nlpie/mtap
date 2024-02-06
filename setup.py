#  Copyright 2023 Regents of the University of Minnesota.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
import os
import shutil
import tempfile

import importlib_resources
from setuptools import Command, setup
from setuptools.command.build_py import build_py as _build_py


class protoc(Command):
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import grpc_tools.protoc

        with importlib_resources.as_file(importlib_resources.files('google')) as api_protos, \
                tempfile.TemporaryDirectory() as tempdir:
            shutil.copytree(os.fspath(api_protos), os.path.join(tempdir, 'google'))
            for proto in ['events.proto', 'processing.proto', 'pipeline.proto']:
                grpc_tools.protoc.main([
                    'grpc_tools.protoc',
                    f'-I{tempdir}',
                    '-Iproto/',
                    '--python_out=python/',
                    '--pyi_out=python/',
                    '--grpc_python_out=python/',
                    f'proto/mtap/api/v1/{proto}'
                ])


class build_py(_build_py):
    def run(self):
        self.run_command('protoc')
        super().run()


setup(
    cmdclass={
        "build_py": build_py,
        "protoc": protoc
    }
)

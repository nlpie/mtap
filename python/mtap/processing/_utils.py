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
from pathlib import Path
from typing import Union, Type


def unique_component_id(component_ids, component_id):
    count = component_ids.get(component_id, 0)
    count += 1
    component_ids[component_id] = count
    component_id = component_id + '-' + str(count)
    return component_id


def write_processors_metadata(output_file: Union[str, Path], *processors: Type['EventProcessor']):
    """Writes the processor metadata as yaml to ``output_file``.

    Parameters
    ----------
    output_file: str or Path
        The file to write to.
    processors: vararg type of EventProcessor
        The EventProcessor classes to get metadata from.
    """
    output_file = Path(output_file)
    arr = [processor.metadata for processor in processors]
    from yaml import dump
    try:
        from yaml import CDumper as Dumper
    except ImportError:
        from yaml import Dumper
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open('w') as f:
        dump(arr, f, Dumper=Dumper)

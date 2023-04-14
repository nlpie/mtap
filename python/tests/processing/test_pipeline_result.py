#  Copyright 2020 Regents of the University of Minnesota.
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
#
from datetime import timedelta

import pytest

from mtap.processing import PipelineResult, ComponentResult


def test_component_result():
    result = PipelineResult(
        component_results=[
            ComponentResult(
                identifier='a',
                result_dict={'b': 'c'},
                timing_info={},
                created_indices={}
            )
        ],
        elapsed_time=timedelta(seconds=4)
    )
    assert result.component_result('a').result_dict['b'] == 'c'
    with pytest.raises(KeyError):
        result.component_result('b')

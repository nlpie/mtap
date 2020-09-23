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
import re
from typing import Tuple, Iterable

_word_pattern = re.compile(r'\w+')

__all__ = [
    'word_tokenize'
]


def word_tokenize(text: str, offset: int) -> Iterable[Tuple[int, int]]:
    """Performs tokenization using a word pattern, i.e. matching 0-9 a-z A-Z plus any unicode "word"
    characters.

    Args:
        text (str): The text to tokenize.
        offset (int): An offset to add to any token boundaries.

    Returns:
        An iterable of (start_index: int, end_index: int) tokens.
    """
    for match in _word_pattern.finditer(text):
        yield offset + match.start(), offset + match.end()

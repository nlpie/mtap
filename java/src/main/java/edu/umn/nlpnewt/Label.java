/*
 * Copyright 2019 Regents of the University of Minnesota
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package edu.umn.nlpnewt;

import java.util.Comparator;

public interface Label {
  int getStartIndex();

  int getEndIndex();

  Comparator<Label> POSITION_COMPARATOR = new ByPosition();

  class ByPosition implements Comparator<Label> {
    @Override
    public int compare(Label o1, Label o2) {
      int compare = Integer.compare(o1.getStartIndex(), o2.getStartIndex());
      if (compare != 0) return compare;
      return Integer.compare(o1.getEndIndex(), o2.getEndIndex());
    }
  }

  static void checkIndexRange(int startIndex, int endIndex) {
    if (endIndex < startIndex) {
      throw new IllegalArgumentException("end index: " + endIndex + " is less than start index: " + startIndex);
    }
    if (startIndex < 0) {
      throw new IllegalArgumentException("start index: " + startIndex + " is less than 0. end index: " + endIndex);
    }
  }
}

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

package edu.umn.nlpnewt.internal;

import edu.umn.nlpnewt.Internal;
import edu.umn.nlpnewt.Label;
import edu.umn.nlpnewt.LabelIndex;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.*;

/**
 * Internal implementation of distinct (non-overlapping) label indices.
 * <p>
 * Users should get label indices via {@link edu.umn.nlpnewt.Document#getLabelIndex(String)} or
 * {@link edu.umn.nlpnewt.Newt#standardLabelIndex(List)}.
 *
 * @param <T> label type
 */
@Internal
final class DistinctLabelIndex<T extends Label> extends AbstractLabelIndex<T> {
  DistinctLabelIndex(List<T> labels) {
    super(labels);
  }

  static <L extends Label> @NotNull LabelIndex<L> create(@NotNull List<L> labels) {
    ArrayList<L> copy = new ArrayList<>(labels);
    copy.sort(Label.POSITION_COMPARATOR);
    return new DistinctLabelIndex<>(copy);
  }

  @Override
  public boolean isDistinct() {
    return true;
  }

  int coveringIndex(Label label) {
    return coveringIndex(label, 0, size());
  }

  int coveringIndexFrom(Label label, int fromIndex) {
    return coveringIndex(label, fromIndex, size());
  }

  int coveringIndexTo(Label label, int toIndex) {
    return coveringIndex(label, 0, toIndex);
  }

  int coveringIndex(Label label, int fromIndex, int toIndex) {
    if (labels.isEmpty()) {
      return -1;
    }

    int index = Collections.binarySearch(labels.subList(fromIndex, toIndex), label,
        Comparator.comparingInt(Label::getStartIndex));

    if (index < 0) {
      index = -1 * (index + 1) - 1;
    }

    if (index >= 0 && index < labels.size() && labels.get(index).covers(label)) {
      return index;
    } else {
      return -1;
    }
  }

}

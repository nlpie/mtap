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
 * @param <L> label type
 */
@Internal
final class DistinctLabelIndex<L extends Label>
    extends AbstractCollection<L> implements LabelIndex<L> {

  private final List<L> labels;

  DistinctLabelIndex(List<L> labels) {
    this.labels = labels;
  }

  DistinctLabelIndex(L... labels) {
    this.labels = Arrays.asList(labels);
  }

  static <L extends Label> @NotNull LabelIndex<L> create(@NotNull List<L> labels) {
    ArrayList<L> copy = new ArrayList<>(labels);
    copy.sort((Comparator<Label>) Label::compareLocation);
    return new DistinctLabelIndex<>(copy);
  }

  @Override
  public boolean isDistinct() {
    return true;
  }

  @Override
  public @NotNull LabelIndex<L> covering(int startIndex, int endIndex) {
    return null;
  }

  @Override
  public @NotNull LabelIndex<L> covering(@NotNull Label label) {
    return null;
  }

  @Override
  public @NotNull LabelIndex<L> inside(int startIndex, int endIndex) {
    return null;
  }

  @Override
  public @NotNull LabelIndex<L> inside(@NotNull Label label) {
    return null;
  }

  @Override
  public @NotNull LabelIndex<L> beginsInside(int startIndex, int endIndex) {
    return null;
  }

  @Override
  public @NotNull LabelIndex<L> beginsInside(@NotNull Label label) {
    return null;
  }

  @Override
  public @NotNull LabelIndex<L> ascendingStartIndex() {
    return null;
  }

  @Override
  public @NotNull LabelIndex<L> descendingStartIndex() {
    return null;
  }

  @Override
  public @NotNull LabelIndex<L> ascendingEndIndex() {
    return null;
  }

  @Override
  public @NotNull LabelIndex<L> descendingEndIndex() {
    return null;
  }

  @Nullable
  @Override
  public L first() {
    return null;
  }

  @Nullable
  @Override
  public L last() {
    return null;
  }

  @Override
  public boolean containsSpan(int startIndex, int endIndex) {
    return false;
  }

  @Override
  public boolean containsSpan(@NotNull Label label) {
    return false;
  }

  @Override
  public @NotNull Collection<L> atLocation(int startIndex, int endIndex) {
    return null;
  }

  @Override
  public @NotNull Collection<L> atLocation(@NotNull Label label) {
    return null;
  }

  @Nullable
  @Override
  public L firstAtLocation(int startIndex, int endIndex) {
    return null;
  }

  @Nullable
  @Override
  public L firstAtLocation(@NotNull Label label) {
    return null;
  }

  @Override
  public @NotNull List<L> asList() {
    return null;
  }

  @Override
  public Iterator<L> iterator() {
    return null;
  }

  @Override
  public int size() {
    return labels.size();
  }

  int coveringIndex(Label label, Integer fromIndex, Integer toIndex) {
    if (fromIndex == null) {
      fromIndex = 0;
    }
    if (toIndex == null) {
      toIndex = size();
    }
    if (labels.isEmpty()) {
      return -1;
    }

    List<L> sublist = labels.subList(fromIndex, toIndex);
    int index = Collections.binarySearch(sublist, label, Label::compareStart);

    if (index < 0) {
      index = -1 * (index + 1) - 1;
    }

    if (index >= 0 && index < labels.size() && sublist.get(index).covers(label)) {
      return index + fromIndex;
    } else {
      return -1;
    }
  }

  Collection<L> atLocation(Label label, Integer fromIndex, Integer toIndex) {
    if (fromIndex == null) {
      fromIndex = 0;
    }
    if (toIndex == null) {
      toIndex = size();
    }

    List<L> sublist = labels.subList(fromIndex, toIndex);
    int index = Collections.binarySearch(sublist, label, Label::compareStart);

    if (index >= 0 && sublist.get(index).getEndIndex() == label.getEndIndex()) {
      return Collections.singletonList(sublist.get(index));
    } else {
      return Collections.emptyList();
    }
  }

  int indexOf(Label label, Integer fromIndex, Integer toIndex) {
    if (fromIndex == null) {
      fromIndex = 0;
    }
    if (toIndex == null) {
      toIndex = size();
    }

    List<L> sublist = labels.subList(fromIndex, toIndex);
    int index = Collections.binarySearch(sublist, label, Label::compareStart);

    if (index >= 0 && label.equals(sublist.get(index))) {
      return index + fromIndex;
    } else {
      return -1;
    }
  }

  boolean containsLocation(Label label, Integer fromIndex, Integer toIndex) {
    if (fromIndex == null) {
      fromIndex = 0;
    }
    if (toIndex == null) {
      toIndex = size();
    }

    List<L> sublist = labels.subList(fromIndex, toIndex);
    int index = Collections.binarySearch(sublist, label, Label::compareStart);

    return index >= 0 && sublist.get(index).getEndIndex() == label.getEndIndex();
  }


  // Index of earliest label with a location after the text index "index"
  // or -1 if there is no such index.
  int higherIndex(int textIndex, Integer fromIndex, Integer toIndex) {
    if (fromIndex == null) {
      fromIndex = 0;
    }
    if (toIndex == null) {
      toIndex = size();
    }

    List<L> sublist = labels.subList(fromIndex, toIndex);
    int i = Collections.binarySearch(sublist, Span.of(textIndex), Label::compareStart);
    if (i < 0) {
      i = -1 * (i + 1);
      if (i == sublist.size()) {
        return -1;
      }
    }
    return i + fromIndex;
  }

  // Index of the last label with a location before the text index
  // or -1 if there is no such index.
  int lowerIndex(int textIndex, Integer fromIndex, Integer toIndex) {
    if (fromIndex == null) {
      fromIndex = 0;
    }
    if (toIndex == null) {
      toIndex = size();
    }

    List<L> sublist = labels.subList(fromIndex, toIndex);
    int i = Collections.binarySearch(sublist, Span.of(textIndex),
        Comparator.comparingInt(Label::getEndIndex));

    if (i == -1) {
      return -1;
    }

    if (i < 0) {
      i = -1 * (i + 2);
    }

    return i + fromIndex;
  }

  // Index of the last label with a location that starts before or at the text index
  // or -1 if there is no such index.
  int lowerStart(int textIndex, Integer fromIndex, Integer toIndex) {
    if (fromIndex == null) {
      fromIndex = 0;
    }
    if (toIndex == null) {
      toIndex = size();
    }

    List<L> sublist = labels.subList(fromIndex, toIndex);
    int i = Collections.binarySearch(sublist, Span.of(textIndex), Label::compareStart);

    if (i < 0) {
      i = -1 * (i + 1);
      if (i == 0) {
        return -1;
      }
      i += -1;
    }

    return i + fromIndex;
  }

  abstract class View implements LabelIndex<L> {
    private final int size;
    private final int left;
    private final int right;

    View(int left, int right) {
      if (left == -1 || right == -1 || right < left) {
        this.left = 0;
        this.right = -1;
      } else {
        this.left = left;
        this.right = right;
      }
      size = this.right - this.left + 1;
    }

    abstract int getFirstIndex();

    abstract int getLastIndex();

    abstract LabelIndex<L> updateEnds(int newLeft, int newRight);

    @Override
    public boolean isEmpty() {
      return size == 0;
    }

    @Override
    public @Nullable L firstAtLocation(int startIndex, int endIndex) {
      return null;
    }
  }

}

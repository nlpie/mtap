/*
 * Copyright 2019 Regents of the University of Minnesota.
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

package edu.umn.nlpie.mtap.model;

import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.*;

/**
 * Implementation of distinct (non-overlapping) label indices.
 *
 * @param <L> label type
 */
public class DistinctLabelIndex<L extends Label> extends AbstractLabelIndex<L> {

  private final List<L> labels;

  public DistinctLabelIndex(List<L> labels) {
    this.labels = labels;
  }

  @SafeVarargs
  public DistinctLabelIndex(L... labels) {
    this.labels = Arrays.asList(labels);
  }

  /**
   * Creates a distinct (not capable of handling overlapping labels) label index.
   * <p>
   * The technical definition of distinctness is that all labels should be able to be
   * ordered such that start indices and end indices are strictly increasing.
   *
   * @param labels Label objects to use to create the label index.
   * @param <L>    The label type.
   *
   * @return Label Index object.
   */
  public static <L extends Label> @NotNull LabelIndex<L> create(@NotNull List<L> labels) {
    ArrayList<L> copy = new ArrayList<>(labels);
    copy.sort((Comparator<Label>) Label::compareLocation);
    return new DistinctLabelIndex<>(copy);
  }

  @Override
  public boolean isDistinct() {
    return true;
  }

  @Override
  public @NotNull LabelIndex<L> covering(@NotNull Label label) {
    int index = coveringIndex(label, null, null);
    return new AscendingView(index, index);
  }

  @Override
  public @NotNull LabelIndex<L> inside(int startIndex, int endIndex) {
    return ascendingViewFromBounds(startIndex, endIndex);
  }

  @Override
  public @NotNull LabelIndex<L> beginningInside(int startIndex, int endIndex) {
    int left = higherIndex(startIndex, null, null);
    int right = lowerStart(endIndex - 1, null, null);
    return new AscendingView(left, right);
  }

  @Override
  public @NotNull LabelIndex<L> ascending() {
    return this;
  }

  @Override
  public @NotNull LabelIndex<L> descending() {
    return new DescendingView(0, labels.size() - 1);
  }

  @Nullable
  @Override
  public L first() {
    if (labels.isEmpty()) {
      return null;
    }
    return labels.get(0);
  }

  @Nullable
  @Override
  public L last() {
    if (labels.isEmpty()) {
      return null;
    }
    return labels.get(labels.size() - 1);
  }

  @Override
  public boolean containsSpan(@NotNull Label label) {
    return containsLocation(label, null, null);
  }

  @Override
  public @NotNull List<@NotNull L> atLocation(@NotNull Label label) {
    return atLocation(label, null, null);
  }

  @Override
  public @NotNull List<L> asList() {
    return new AbstractList<L>() {
      @Override
      public L get(int index) {
        return labels.get(index);
      }

      @Override
      public int size() {
        return labels.size();
      }

      @Override
      public int indexOf(Object o) {
        if (!(o instanceof Label)) {
          return -1;
        }
        return DistinctLabelIndex.this.indexOf((Label) o, null, null);
      }

      @Override
      public int lastIndexOf(Object o) {
        return indexOf(o);
      }

      @Override
      public boolean contains(Object o) {
        return indexOf(o) != -1;
      }
    };
  }

  @Override
  public Iterator<L> iterator() {
    return labels.iterator();
  }

  @Override
  public boolean contains(Object o) {
    if (!(o instanceof Label)) {
      return false;
    }
    return indexOf((Label) o, null, null) != -1;
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

  List<L> atLocation(Label label, Integer fromIndex, Integer toIndex) {
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

  abstract class View extends AbstractLabelIndex<L> {
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

    int getLeft() {
      return left;
    }

    int getRight() {
      return right;
    }

    abstract int getFirstIndex();

    abstract int getLastIndex();

    abstract LabelIndex<L> updateEnds(int newLeft, int newRight);

    @Override
    public boolean isDistinct() {
      return true;
    }

    @Override
    public int size() {
      return size;
    }

    @Override
    public @NotNull List<@NotNull L> atLocation(@NotNull Label label) {
      return DistinctLabelIndex.this.atLocation(label, left, right + 1);
    }

    @Override
    public boolean contains(Object o) {
      if (!(o instanceof Label)) {
        return false;
      }
      return indexOf((Label) o, left, right + 1) != -1;
    }

    @Override
    public boolean containsSpan(@NotNull Label label) {
      return containsLocation(label, left, right + 1);
    }

    @Override
    public @NotNull LabelIndex<L> inside(int startIndex, int endIndex) {
      return updateBounds(startIndex, endIndex);
    }

    @Override
    public @NotNull LabelIndex<L> beginningInside(int startIndex, int endIndex) {
      return updateEnds(higherIndex(startIndex, left, right + 1),
          lowerStart(endIndex - 1, left, right + 1));
    }

    @Override
    public @Nullable L first() {
      int firstIndex = getFirstIndex();
      if (0 <= firstIndex && firstIndex < labels.size() && left <= firstIndex && firstIndex <= right) {
        return labels.get(firstIndex);
      }
      return null;
    }

    @Override
    public @Nullable L last() {
      int lastIndex = getLastIndex();
      if (0 <= lastIndex && lastIndex < labels.size() && left <= lastIndex && lastIndex <= right) {
        return labels.get(lastIndex);
      }
      return null;
    }

    @Override
    public @NotNull LabelIndex<L> covering(@NotNull Label label) {
      int index = coveringIndex(label, left, right + 1);
      if (index != -1) {
        return updateEnds(index, index);
      } else {
        return updateEnds(0, -1);
      }
    }

    LabelIndex<L> updateBounds(Integer minTextIndex, Integer maxTextIndex) {
      int newLeft = 0;
      if (minTextIndex != null) {
        newLeft = higherIndex(minTextIndex, left, right + 1);
      }
      int newRight = Integer.MAX_VALUE;
      if (maxTextIndex != null) {
        newRight = lowerIndex(maxTextIndex, left, right + 1);
      }

      if (newLeft == -1) {
        return updateEnds(0, -1);
      }

      return updateEnds(Math.max(left, newLeft), Math.min(right, newRight));
    }
  }

  AscendingView ascendingViewFromBounds(int minTextIndex, int maxTextIndex) {
    int left = higherIndex(minTextIndex, null, null);
    int right = lowerIndex(maxTextIndex, null, null);
    return new AscendingView(left, right);
  }

  class AscendingView extends View {

    AscendingView(Integer left, Integer right) {
      super(left, right);
    }

    @Override
    int getFirstIndex() {
      return getLeft();
    }

    @Override
    int getLastIndex() {
      return getRight();
    }

    @Override
    LabelIndex<L> updateEnds(int newLeft, int newRight) {
      if (newLeft == -1) {
        return new AscendingView(0, -1);
      }
      return new AscendingView(newLeft, newRight);
    }

    @Override
    public @NotNull LabelIndex<L> ascending() {
      return this;
    }

    @Override
    public @NotNull LabelIndex<L> descending() {
      return new DescendingView(getLeft(), getRight());
    }

    @Override
    public @NotNull List<L> asList() {
      return new AscendingListView();
    }

    @Override
    public Iterator<L> iterator() {
      return asList().iterator();
    }

    class AscendingListView extends AbstractList<L> implements RandomAccess {
      @Override
      public L get(int index) {
        if (index < 0 || index >= size()) {
          throw new IndexOutOfBoundsException("Index " + index + " is not in bounds [" + 0 + ", " + size() + ")");
        }
        return labels.get(getFirstIndex() + index);
      }

      @Override
      public boolean contains(Object o) {
        return AscendingView.this.contains(o);
      }

      @Override
      public int indexOf(Object o) {
        if (!(o instanceof Label)) {
          return -1;
        }
        int index = DistinctLabelIndex.this.indexOf((Label) o, getLeft(), getRight() + 1);
        if (index == -1) return -1;
        return index - getLeft();
      }

      @Override
      public int lastIndexOf(Object o) {
        return indexOf(o);
      }

      @Override
      public int size() {
        return AscendingView.this.size();
      }
    }
  }

  class DescendingView extends View {
    DescendingView(int left, int right) {
      super(left, right);
    }

    @Override
    int getFirstIndex() {
      return getRight();
    }

    @Override
    int getLastIndex() {
      return getLeft();
    }

    @Override
    LabelIndex<L> updateEnds(int newLeft, int newRight) {
      if (newLeft == -1) {
        return new DescendingView(0, -1);
      }
      return new DescendingView(newLeft, newRight);
    }


    @Override
    public @NotNull LabelIndex<L> ascending() {
      return new AscendingView(getLeft(), getRight());
    }

    @Override
    public @NotNull LabelIndex<L> descending() {
      return this;
    }

    @Override
    public @NotNull List<@NotNull L> asList() {
      return new DescendingListView();
    }

    @Override
    public @NotNull Iterator<@NotNull L> iterator() {
      return asList().iterator();
    }

    class DescendingListView extends AbstractList<L> implements RandomAccess {
      @Override
      public L get(int index) {
        if (index < 0 || index >= size()) {
          throw new IndexOutOfBoundsException("Index " + index + " is not in bounds [" + 0 + ", " + size() + ")");
        }
        return labels.get(getRight() - index);
      }

      public boolean contains(Object o) {
        return DescendingView.this.contains(o);
      }

      @Override
      public int indexOf(Object o) {
        if (!(o instanceof Label)) {
          return -1;
        }
        int index = DistinctLabelIndex.this.indexOf((Label) o, getLeft(), getRight() + 1);
        if (index == -1) return -1;
        return getRight() - index;
      }

      @Override
      public int lastIndexOf(Object o) {
        return indexOf(o);
      }

      @Override
      public int size() {
        return DescendingView.this.size();
      }
    }
  }

}

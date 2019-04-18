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
 * Internal implementation of standard (overlapping) label indices.
 * <p>
 * Users should get label indices via {@link edu.umn.nlpnewt.Document#getLabelIndex(String)} or
 * {@link edu.umn.nlpnewt.Newt#standardLabelIndex(List)}.
 *
 * @param <L> label type
 */
@Internal
final class StandardLabelIndex<L extends Label> extends AbstractLabelIndex<L> {

  private final List<L> labels;

  StandardLabelIndex(List<L> labels) {
    this.labels = labels;
  }

  static <L extends Label> StandardLabelIndex<L> create(List<L> labels) {
    ArrayList<L> copy = new ArrayList<>(labels);
    copy.sort((Comparator<Label>) Label::compareLocation);
    return new StandardLabelIndex<>(copy);
  }

  @Override
  public boolean isDistinct() {
    return false;
  }

  @Override
  public @NotNull LabelIndex<L> covering(@NotNull Label label) {
    return createAscendingView(null, label.getStartIndex(), label.getEndIndex(), null, null, null);
  }

  @Override
  public @NotNull LabelIndex<L> inside(int startIndex, int endIndex) {
    return createAscendingView(startIndex, endIndex - 1, startIndex, endIndex, null, null);
  }

  @Override
  public @NotNull LabelIndex<L> beginsInside(int startIndex, int endIndex) {
    return createAscendingView(startIndex, endIndex - 1, startIndex, null, null, null);
  }

  @Override
  public @NotNull LabelIndex<L> ascendingStartIndex() {
    return this;
  }

  @Override
  public @NotNull LabelIndex<L> descendingStartIndex() {
    return createAscendingView(null, null, null, null, null, null).descendingStartIndex();
  }

  @Override
  public @NotNull LabelIndex<L> ascendingEndIndex() {
    return this;
  }

  @Override
  public @NotNull LabelIndex<L> descendingEndIndex() {
    return createAscendingView(null, null, null, null, null, null).descendingEndIndex();
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
    return internalContainsLocation(label, null, null);
  }

  @Override
  public @NotNull List<@NotNull L> atLocation(@NotNull Label label) {
    return internalAtLocation(label, null, null);
  }

  @Override
  public @NotNull List<L> asList() {
    return new AsList();
  }

  class AsList extends AbstractList<L> implements RandomAccess {

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
      return internalIndexOf(((Label) o), null, null);
    }

    @Override
    public int lastIndexOf(Object o) {
      if (!(o instanceof Label)) {
        return -1;
      }
      return internalLastIndexOf(((Label) o));
    }
  }

  @Override
  public Iterator<L> iterator() {
    return labels.iterator();
  }

  @Override
  public int size() {
    return labels.size();
  }

  List<@NotNull L> internalAtLocation(Label l, Integer fromIndex, Integer toIndex) {
    if (fromIndex == null) {
      fromIndex = 0;
    }
    if (toIndex == null) {
      toIndex = size();
    }

    List<L> sublist = labels.subList(fromIndex, toIndex);
    int index = Collections.binarySearch(sublist, l, Label::compareLocation);

    if (index < 0) return Collections.emptyList();

    int from = index;
    while (from > 0 && sublist.get(from - 1).locationEquals(l)) {
      from--;
    }

    int to = index;
    while (to < sublist.size() && sublist.get(to).locationEquals(l)) {
      to++;
    }

    return Collections.unmodifiableList(sublist.subList(from, to));
  }

  int internalIndexOf(Label label, Integer fromIndex, Integer toIndex) {
    if (fromIndex == null) fromIndex = 0;
    if (toIndex == null) toIndex = size();

    List<L> subList = labels.subList(fromIndex, toIndex);
    int index = Collections.binarySearch(subList, label, Label::compareLocation);
    if (index < 0) return -1;

    int left = index;
    int found = -1;
    while (left > 0 && subList.get(left - 1).locationEquals(label)) {
      if (label.equals(subList.get(left - 1))) found = left - 1;
      left -= 1;
    }
    // we need to return the very leftmost for indexOf
    if (found != -1) {
      return fromIndex + found;
    }

    int right = index;
    while (right < subList.size() && subList.get(right).locationEquals(label)) {
      if (subList.get(right).equals(label)) return fromIndex + right;
      right += 1;
    }

    return -1;
  }

  int internalLastIndexOf(Label label) {
    int index = Collections.binarySearch(labels, label, Label::compareLocation);

    if (index < 0) return -1;

    int right = index;
    int found = -1;
    while (right < labels.size() && labels.get(right).locationEquals(label)) {
      if (labels.get(right).equals(label)) found = right;
      right += 1;
    }
    // we need to return the very rightmost for lastIndexOf
    if (found != -1) {
      return found;
    }

    int left = index;
    while (left > 0 && labels.get(left - 1).locationEquals(label)) {
      if (label.equals(labels.get(left - 1))) return left - 1;
      left -= 1;
    }

    return -1;
  }

  boolean internalContainsLocation(Label label, Integer fromIndex, Integer toIndex) {
    if (fromIndex == null) fromIndex = 0;
    if (toIndex == null) toIndex = size();
    List<L> subList = labels.subList(fromIndex, toIndex);
    return Collections.binarySearch(subList, label, Label::compareLocation) >= 0;
  }

  int ceilingIndex(int startIndex, int endIndex, Integer fromIndex, Integer toIndex) {
    return ceilingIndex(Span.of(startIndex, endIndex), fromIndex, toIndex);
  }

  int ceilingIndex(Label label, Integer fromIndex, Integer toIndex) {
    if (fromIndex == null) fromIndex = 0;
    if (toIndex == null) toIndex = labels.size();

    List<L> subList = labels.subList(fromIndex, toIndex);
    int index = Collections.binarySearch(subList, label, Label::compareLocation);

    if (index < 0) {
      int insert = -1 * (index + 1);
      if (insert == toIndex) return -1;
      return fromIndex + insert;
    }

    while (index > fromIndex && subList.get(index - 1).locationEquals(label)) {
      index--;
    }

    return fromIndex + index;
  }

  int floorStartAndEnd(int start, int end, Integer fromIndex, Integer toIndex) {
    if (fromIndex == null) fromIndex = 0;
    if (toIndex == null) toIndex = labels.size();

    int index = floorIndex(start, end, fromIndex, toIndex);

    while (index > fromIndex && labels.get(index - 1).getEndIndex() > end) {
      index--;
    }
    return index;
  }

  int floorIndex(int start, int end, Integer fromIndex, Integer toIndex) {
    return floorIndex(Span.of(start, end), fromIndex, toIndex);
  }

  // Greatest index with a location less than or equal to the provided location
  // or -1 if there is no such index.
  int floorIndex(Label label, Integer fromIndex, Integer toIndex) {
    if (fromIndex == null) fromIndex = 0;
    if (toIndex == null) toIndex = labels.size();

    List<L> subList = labels.subList(fromIndex, toIndex);
    int index = Collections.binarySearch(subList, label, Label::compareLocation);

    if (index < 0) {
      int insert = -1 * (index + 1);
      if (insert == fromIndex) return -1;
      return fromIndex + insert - 1;
    }

    while (index < subList.size() - 1 && subList.get(index + 1).locationEquals(label)) {
      index++;
    }
    return fromIndex + index;
  }

  boolean beginsEqual(int firstIndex, int secondIndex) {
    return firstIndex >= 0 && firstIndex < size() && secondIndex >= 0 && secondIndex < size()
        && labels.get(firstIndex).getStartIndex() == labels.get(secondIndex).getStartIndex();
  }

  AscendingView createAscendingView(
      Integer minStart,
      Integer maxStart,
      Integer minEnd,
      Integer maxEnd,
      Integer left,
      Integer right
  ) {
    if (minStart == null) {
      minStart = 0;
    }
    if (maxStart == null) {
      maxStart = Integer.MAX_VALUE;
    }
    if (minEnd == null) {
      minEnd = 0;
    }
    if (maxEnd == null) {
      maxEnd = Integer.MAX_VALUE;
    }
    if (left == null) {
      left = ceilingIndex(minStart, minEnd, null, null);
    }
    if (right == null) {
      right = floorStartAndEnd(maxStart, maxEnd, null, null);
    }
    return new AscendingView(minStart, maxStart, minEnd, maxEnd, left, right);
  }

  abstract class View extends AbstractLabelIndex<L> {

    final int minStart;
    final int maxStart;
    final int minEnd;
    final int maxEnd;
    final int left;
    final int right;

    private int size = -1;

    View(int minStart, int maxStart, int minEnd, int maxEnd, int left, int right) {
      this.minStart = minStart;
      this.maxStart = maxStart;
      this.minEnd = minEnd;
      this.maxEnd = maxEnd;
      if (left >= 0 && left < labels.size() && right >= left) {
        this.left = left;
        this.right = right;
      } else {
        this.left = 0;
        this.right = -1;
      }
    }

    @Override
    public boolean isDistinct() {
      return false;
    }

    abstract int getFirstIndex();

    abstract int getLastIndex();

    private View updateBounds(Integer newMinStart,
                              Integer newMaxStart,
                              Integer newMinEnd,
                              Integer newMaxEnd) {
      if (newMinStart == null) {
        newMinStart = minStart;
      }
      if (newMaxStart == null) {
        newMaxStart = maxStart;
      }
      if (newMinEnd == null) {
        newMinEnd = minEnd;
      }
      if (newMaxEnd == null) {
        newMaxEnd = maxEnd;
      }
      return innerUpdateBounds(Math.max(newMinStart, minStart), Math.min(newMaxStart, maxStart),
          Math.max(newMinEnd, minEnd), Math.min(newMaxEnd, maxEnd));
    }

    abstract View innerUpdateBounds(int newMinStart, int newMaxStart, int newMinEnd, int newMaxEnd);

    abstract View updateEnds(int left, int right);

    abstract int nextIndex(int index);

    abstract int prevIndex(int index);

    boolean insideView(Label l) {
      return minStart <= l.getStartIndex() && l.getStartIndex() <= maxStart
          && minEnd <= l.getEndIndex() && l.getEndIndex() <= maxEnd;
    }

    boolean endsInView(int index) {
      if (index == -1) return false;
      int endIndex = labels.get(index).getEndIndex();
      return minEnd <= endIndex && endIndex <= maxEnd;
    }

    @Override
    public int size() {
      int size = this.size;
      if (size == -1) {
        size = 0;
        int i = getFirstIndex();
        while (i != -1) {
          size++;
          i = nextIndex(i);
        }
        this.size = size;
      }
      return size;
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
    public @NotNull List<@NotNull L> atLocation(@NotNull Label label) {
      if (!insideView(label)) return Collections.emptyList();
      return internalAtLocation(label, left, right + 1);
    }

    @Override
    public boolean contains(Object o) {
      if (!(o instanceof Label)) {
        return false;
      }
      Label label = (Label) o;

      if (!insideView(label)) return false;
      return internalIndexOf(label, left, right + 1) != -1;
    }

    @Override
    public boolean containsSpan(@NotNull Label label) {
      if (!insideView(label)) return false;
      return internalContainsLocation(label, left, right + 1);
    }

    @Override
    public @NotNull LabelIndex<L> inside(int startIndex, int endIndex) {
      return updateBounds(startIndex, endIndex - 1, startIndex, endIndex);
    }

    @Override
    public @NotNull LabelIndex<L> beginsInside(int startIndex, int endIndex) {
      return updateBounds(startIndex, endIndex - 1, null, null);
    }

    @Override
    public @NotNull LabelIndex<L> covering(@NotNull Label label) {
      return updateBounds(null, label.getStartIndex(), label.getEndIndex(), null);
    }

    @Override
    public @NotNull List<@NotNull L> asList() {
      return new ViewList();
    }

    @Override
    public @NotNull Iterator<@NotNull L> iterator() {
      return new ViewIterator(0);
    }

    int nextIndexAscending(int index) {
      while (index < right) {
        if (endsInView(++index)) return index;
      }
      return -1;
    }

    int nextIndexDescending(int index) {
      while (index > left) {
        if (endsInView(--index)) return index;
      }
      return -1;
    }

    int nextBreakAscending(int index) {
      int tmp = index;
      do {
        index = tmp;
        tmp = nextIndexAscending(index);
        if (tmp == -1) {
          break;
        }
      } while (beginsEqual(tmp, index));
      return index;
    }

    int nextAscendingReversing(int index) {
      int tmp = index;
      boolean atBeginning = false;
      if (index == left) {
        atBeginning = true;
      } else {
        tmp = nextIndexDescending(index);
      }

      if (atBeginning || !beginsEqual(tmp, index)) {
        tmp = nextIndexAscending(nextBreakAscending(index));
        if (index != -1) {
          tmp = nextBreakAscending(tmp);
        }
      }
      return tmp;
    }

    int nextBreakDescending(int index) {
      int tmp = index;
      do {
        index = tmp;
        tmp = nextIndexDescending(index);
        if (tmp == -1) {
          break;
        }
      } while (beginsEqual(tmp, index));
      return index;
    }

    int nextDescendingReversing(int index) {
      int tmp = index;
      boolean atEnd = false;
      if (index >= right) {
        atEnd = true;
      } else {
        tmp = nextIndexAscending(index);
      }

      if (atEnd || !beginsEqual(tmp, index)) {
        tmp = nextIndexDescending(nextBreakDescending(index));
        if (tmp != -1) {
          tmp = nextBreakDescending(tmp);
        }
      }
      return tmp;
    }

    class ViewList extends AbstractList<@NotNull L> {
      @Override
      public L get(int index) {
        if (index < 0) {
          throw new IndexOutOfBoundsException("Index less than 0.");
        }
        int ptr = getFirstIndex();
        for (int i = 0; i < index; i++) {
          if (ptr == getLastIndex()) {
            throw new IndexOutOfBoundsException("index: " + index + " is not in bounds.");
          }
          ptr = nextIndex(ptr);
        }
        return labels.get(ptr);
      }

      @Override
      public int size() {
        return View.this.size();
      }

      @Override
      public boolean contains(Object o) {
        return View.this.contains(o);
      }

      @Override
      public @NotNull ListIterator<@NotNull L> listIterator() {
        return new ViewIterator(0);
      }

      @Override
      public @NotNull ListIterator<@NotNull L> listIterator(int index) {
        return new ViewIterator(index);
      }

      @Override
      public @NotNull Iterator<@NotNull L> iterator() {
        return new ViewIterator(0);
      }

      @Override
      public @NotNull List<@NotNull L> subList(int fromIndex, int toIndex) {
        if (fromIndex > toIndex) {
          throw new IllegalArgumentException();
        }
        if (fromIndex < 0) {
          throw new IndexOutOfBoundsException();
        }
        ViewIterator it = new ViewIterator(fromIndex);
        int globalFrom = it.cursor;
        int globalTo = globalFrom;
        while (it.hasNext() && it.nextIndex() < toIndex) {
          globalTo = it.cursor + 1;
          it.next();
        }
        if (it.localIndex != toIndex) {
          throw new IndexOutOfBoundsException("toIndex: " + toIndex + " is not in bounds.");
        }

        return updateEnds(globalFrom, globalTo - 1).asList();
      }
    }

    class ViewIterator implements ListIterator<@NotNull L> {
      int cursor = getFirstIndex();
      int localIndex = 0;

      ViewIterator(int index) {
        if (index < 0) {
          throw new IndexOutOfBoundsException("Index less than 0");
        }

        if (index == size()) {
          cursor = -1;
          localIndex = size();
        } else {
          while (localIndex < index) {
            if (!hasNext()) {
              throw new IndexOutOfBoundsException("index: " + index + " is not in bounds.");
            }
            next();
          }
        }
      }

      @Override
      public boolean hasNext() {
        return localIndex < size;
      }

      @Override
      public @NotNull L next() {
        if (!hasNext()) {
          throw new NoSuchElementException("index: " + localIndex + " is not in bounds.");
        }

        int current = cursor;
        cursor = View.this.nextIndex(cursor);
        localIndex++;
        return labels.get(current);
      }

      @Override
      public boolean hasPrevious() {
        return localIndex > 0;
      }

      @Override
      public @NotNull L previous() {
        if (!hasPrevious()) {
          throw new NoSuchElementException("index: " + (localIndex - 1) + " is not in bounds.");
        }

        if (cursor == -1) {
          cursor = getLastIndex();
        } else {
          cursor = prevIndex(cursor);
        }
        localIndex--;
        return labels.get(cursor);
      }

      @Override
      public int nextIndex() {
        return localIndex;
      }

      @Override
      public int previousIndex() {
        return localIndex - 1;
      }

      @Override
      public void remove() {
        throw new UnsupportedOperationException("Remove not supported.");
      }

      @Override
      public void set(@NotNull L l) {
        throw new UnsupportedOperationException("Set not supported.");
      }

      @Override
      public void add(@NotNull L l) {
        throw new UnsupportedOperationException("Add not supported.");
      }
    }
  }

  class AscendingView extends View {
    private final int firstIndex;
    private final int lastIndex;

    AscendingView(int minStart, int maxStart, int minEnd, int maxEnd, int left, int right) {
      super(minStart, maxStart, minEnd, maxEnd, left, right);
      if (right < left) {
        firstIndex = -1;
        lastIndex = -1;
      } else {
        firstIndex = nextIndex(left - 1);
        lastIndex = prevIndex(right + 1);
      }
    }

    @Override
    int getFirstIndex() {
      return firstIndex;
    }

    @Override
    int getLastIndex() {
      return lastIndex;
    }

    @Override
    View innerUpdateBounds(int newMinStart, int newMaxStart, int newMinEnd, int newMaxEnd) {
      return new AscendingView(
          newMinStart,
          newMaxStart,
          newMinEnd,
          newMaxEnd,
          ceilingIndex(newMinStart, newMinEnd, left, right + 1),
          floorStartAndEnd(newMaxStart, newMaxEnd, left, right + 1));
    }

    @Override
    View updateEnds(int left, int right) {
      return new AscendingView(minStart, maxStart, minEnd, maxEnd, left, right);
    }

    @Override
    int nextIndex(int index) {
      return nextIndexAscending(index);
    }

    @Override
    int prevIndex(int index) {
      return nextIndexDescending(index);
    }

    @Override
    public @NotNull LabelIndex<L> ascendingStartIndex() {
      return this;
    }

    @Override
    public @NotNull LabelIndex<L> descendingStartIndex() {
      return new DescendingReversingView(minStart, maxStart, minEnd, maxEnd, left, right);
    }

    @Override
    public @NotNull LabelIndex<L> ascendingEndIndex() {
      return this;
    }

    @Override
    public @NotNull LabelIndex<L> descendingEndIndex() {
      return new AscendingReversingView(minStart, maxStart, minEnd, maxEnd, left, right);
    }
  }

  class DescendingView extends View {
    private final int firstIndex;
    private final int lastIndex;

    DescendingView(int minStart, int maxStart, int minEnd, int maxEnd, int left, int right) {
      super(minStart, maxStart, minEnd, maxEnd, left, right);
      if (right < left) {
        firstIndex = -1;
        lastIndex = -1;
      } else {
        firstIndex = nextIndex(right + 1);
        lastIndex = prevIndex(left - 1);
      }
    }

    @Override
    int getFirstIndex() {
      return firstIndex;
    }

    @Override
    int getLastIndex() {
      return lastIndex;
    }

    @Override
    View innerUpdateBounds(int newMinStart, int newMaxStart, int newMinEnd, int newMaxEnd) {
      return new DescendingView(
          newMinStart,
          newMaxStart,
          newMinEnd,
          newMaxEnd,
          ceilingIndex(newMinStart, newMinEnd, left, right + 1),
          floorStartAndEnd(newMaxStart, newMaxEnd, left, right + 1)
      );
    }

    @Override
    View updateEnds(int left, int right) {
      return new DescendingView(minStart, maxStart, minEnd, maxEnd, left, right);
    }

    @Override
    int nextIndex(int index) {
      return nextIndexDescending(index);
    }

    @Override
    int prevIndex(int index) {
      return nextIndexAscending(index);
    }

    @Override
    public @NotNull LabelIndex<L> ascendingStartIndex() {
      return new AscendingReversingView(
          minStart,
          maxStart,
          minEnd,
          maxEnd,
          left,
          right
      );
    }

    @Override
    public @NotNull LabelIndex<L> descendingStartIndex() {
      return this;
    }

    @Override
    public @NotNull LabelIndex<L> ascendingEndIndex() {
      return new DescendingReversingView(
          minStart,
          maxStart,
          minEnd,
          maxEnd,
          left,
          right
      );
    }

    @Override
    public @NotNull LabelIndex<L> descendingEndIndex() {
      return this;
    }
  }

  class AscendingReversingView extends View {
    private final int firstIndex;
    private final int lastIndex;

    AscendingReversingView(
        int minStart,
        int maxStart,
        int minEnd,
        int maxEnd,
        int left,
        int right
    ) {
      super(minStart, maxStart, minEnd, maxEnd, left, right);
      if (right < left) {
        firstIndex = -1;
        lastIndex = -1;
      } else {
        firstIndex = nextBreakAscending(left);
        lastIndex = nextBreakDescending(right);
      }
    }

    @Override
    int getFirstIndex() {
      return firstIndex;
    }

    @Override
    int getLastIndex() {
      return lastIndex;
    }

    @Override
    View innerUpdateBounds(int newMinStart, int newMaxStart, int newMinEnd, int newMaxEnd) {
      return new AscendingReversingView(newMinStart, newMaxStart, newMinEnd, newMaxEnd,
          ceilingIndex(newMaxStart, newMinEnd, left, right + 1),
          floorStartAndEnd(newMaxStart, newMaxEnd, left, right + 1));
    }

    @Override
    View updateEnds(int left, int right) {
      return new AscendingReversingView(minStart, maxStart, minEnd, maxEnd, left, right);
    }

    @Override
    int nextIndex(int index) {
      return nextAscendingReversing(index);
    }

    @Override
    int prevIndex(int index) {
      return nextDescendingReversing(index);
    }

    @Override
    public @NotNull LabelIndex<L> ascendingStartIndex() {
      return this;
    }

    @Override
    public @NotNull LabelIndex<L> descendingStartIndex() {
      return new DescendingView(minStart, maxStart, minEnd, maxEnd, left, right);
    }

    @Override
    public @NotNull LabelIndex<L> ascendingEndIndex() {
      return new AscendingView(minStart, maxStart, minEnd, maxEnd, left, right);
    }

    @Override
    public @NotNull LabelIndex<L> descendingEndIndex() {
      return this;
    }
  }

  class DescendingReversingView extends View {

    private final int firstIndex;
    private final int lastIndex;

    DescendingReversingView(
        int minStart,
        int maxStart,
        int minEnd,
        int maxEnd,
        int left,
        int right
    ) {
      super(minStart, maxStart, minEnd, maxEnd, left, right);
      if (right < left) {
        firstIndex = -1;
        lastIndex = -1;
      } else {
        firstIndex = nextBreakDescending(right);
        lastIndex = nextBreakAscending(right);
      }
    }

    @Override
    int getFirstIndex() {
      return firstIndex;
    }

    @Override
    int getLastIndex() {
      return lastIndex;
    }

    @Override
    View innerUpdateBounds(int newMinStart, int newMaxStart, int newMinEnd, int newMaxEnd) {
      return new DescendingReversingView(
          newMinStart,
          newMaxStart,
          newMinEnd,
          newMaxEnd,
          ceilingIndex(newMinStart, newMinEnd, left, right + 1),
          floorStartAndEnd(newMaxStart, newMaxEnd, left, right + 1)
      );
    }

    @Override
    View updateEnds(int left, int right) {
      return new DescendingReversingView(minStart, maxStart, minEnd, maxEnd, left, right);
    }

    @Override
    int nextIndex(int index) {
      return nextDescendingReversing(index);
    }

    @Override
    int prevIndex(int index) {
      return nextAscendingReversing(index);
    }

    @Override
    public @NotNull LabelIndex<L> ascendingStartIndex() {
      return new AscendingView(minStart, maxStart, minEnd, maxEnd, left, right);
    }

    @Override
    public @NotNull LabelIndex<L> descendingStartIndex() {
      return this;
    }

    @Override
    public @NotNull LabelIndex<L> ascendingEndIndex() {
      return this;
    }

    @Override
    public @NotNull LabelIndex<L> descendingEndIndex() {
      return new DescendingView(minStart, maxStart, minEnd, maxEnd, left, right);
    }
  }
}

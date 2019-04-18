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

package edu.umn.nlpnewt.internal;

import edu.umn.nlpnewt.GenericLabel;
import edu.umn.nlpnewt.Label;
import edu.umn.nlpnewt.LabelIndex;
import org.jetbrains.annotations.NotNull;
import org.junit.jupiter.api.Test;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

public class StandardLabelIndexAscendingReversingViewTest {
  LabelIndex<Span> ascendingReversing = new StandardLabelIndex<>(Arrays.asList(
      Span.of(0, 5),
      Span.of(0, 7),
      Span.of(2, 6),
      Span.of(6, 7),
      Span.of(6, 8),
      Span.of(9, 10),
      Span.of(9, 13),
      Span.of(9, 13),
      Span.of(9, 20),
      Span.of(10, 20),
      Span.of(10, 20),
      Span.of(15, 20)
  )).inside(1, 15).descendingEndIndex();

  LabelIndex<Span> empty = ascendingReversing.inside(0, 0);


  @Test
  void isDistinct() {
    assertFalse(ascendingReversing.isDistinct());
  }

  @Test
  void size() {
    assertEquals(6, ascendingReversing.size());
  }

  @Test
  void covering() {
    LabelIndex<Span> covering = ascendingReversing.covering(Span.of(2, 4));
    assertEquals(
        Collections.singletonList(Span.of(2, 6)),
        covering.asList()
    );
  }

  @Test
  void coveringEquals() {
    LabelIndex<Span> covering = ascendingReversing.covering(Span.of(6, 8));
    assertEquals(Collections.singletonList(Span.of(6, 8)), covering.asList());
  }

  @Test
  void coveringEmpty() {
    LabelIndex<Span> covering = ascendingReversing.covering(4, 10);
    assertEquals(0, covering.size());
  }

  @Test
  void emptyCovering() {
    LabelIndex<?> covering = ascendingReversing.covering(4, 10);
    assertEquals(0, covering.size());
  }

  @Test
  void inside() {
    LabelIndex<Span> inside = ascendingReversing.inside(3, 10);

    assertEquals(Arrays.asList(Span.of(6, 8), Span.of(6, 7), Span.of(9, 10)), inside.asList());
  }

  @Test
  void insideBefore() {
    LabelIndex<Span> inside = ascendingReversing.inside(0, 3);
    assertEquals(0, inside.size());
  }

  @Test
  void insideAfter() {
    LabelIndex<Span> inside = ascendingReversing.inside(Span.of(15, 20));
    assertEquals(0, inside.size());
  }

  @Test
  void emptyInside() {
    LabelIndex<?> inside = empty.inside(0, 5);
    assertEquals(Collections.emptyList(), inside.asList());
  }

  @Test
  void insideMany() {
    List<Span> spans = Arrays.asList(
        Span.of(0, 3),
        Span.of(0, 3),
        Span.of(0, 3),
        Span.of(0, 3),
        Span.of(0, 3),
        Span.of(0, 3),
        Span.of(0, 3),
        Span.of(2, 5),
        Span.of(2, 5),
        Span.of(2, 5),
        Span.of(2, 5),
        Span.of(2, 5),
        Span.of(2, 5),
        Span.of(2, 5),
        Span.of(3, 4),
        Span.of(3, 4),
        Span.of(3, 4),
        Span.of(3, 4),
        Span.of(3, 4),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(6, 6),
        Span.of(6, 6),
        Span.of(6, 6),
        Span.of(6, 6),
        Span.of(6, 6),
        Span.of(6, 6),
        Span.of(6, 6),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10)
    );
    LabelIndex<Span> index = new StandardLabelIndex<>(spans).descendingEndIndex();
    LabelIndex<Span> inside = index.inside(3, 6);
    assertEquals(Arrays.asList(
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 4),
        Span.of(3, 4),
        Span.of(3, 4),
        Span.of(3, 4),
        Span.of(3, 4),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6)
    ), inside.asList());
  }

  @Test
  void beginsInside() {
    LabelIndex<Span> beginsInside = ascendingReversing.beginsInside(Span.of(1, 10));
    assertEquals(
        Arrays.asList(
            Span.of(2, 6),
            Span.of(6, 8),
            Span.of(6, 7),
            Span.of(9, 13),
            Span.of(9, 13),
            Span.of(9, 10)
        ),
        beginsInside.asList()
    );
  }

  @Test
  void beginsInsideEmpty() {
    LabelIndex<Span> beginsInside = ascendingReversing.beginsInside(3, 5);
    assertEquals(Collections.emptyList(), beginsInside.asList());
  }

  @Test
  void emptyBeginsInside() {
    LabelIndex<?> beginsInside = empty.beginsInside(0, 5);
    assertEquals(Collections.emptyList(), beginsInside.asList());
  }

  @Test
  void ascendingBegin() {
    LabelIndex<Span> ascendingStartIndex = ascendingReversing.ascendingStartIndex();
    assertSame(ascendingReversing, ascendingStartIndex);
  }

  @Test
  void emptyAscendingBegin() {
    LabelIndex<?> ascendingStartIndex = empty.ascendingStartIndex();
    assertSame(empty, ascendingStartIndex);
  }

  @Test
  void descendingBegin() {
    LabelIndex<Span> descendingStartIndex = ascendingReversing.descendingStartIndex();
    assertEquals(
        Arrays.asList(
            Span.of(9, 13),
            Span.of(9, 13),
            Span.of(9, 10),
            Span.of(6, 8),
            Span.of(6, 7),
            Span.of(2, 6)
        ),
        descendingStartIndex.asList()
    );
  }

  @Test
  void emptyDescendingBegin() {
    LabelIndex<?> descendingStartIndex = empty.descendingStartIndex();
    assertEquals(empty.asList(), descendingStartIndex.asList());
  }

  @Test
  void ascendingEnd() {
    LabelIndex<Span> ascendingEndIndex = ascendingReversing.ascendingEndIndex();
    assertEquals(
        Arrays.asList(
            Span.of(2, 6),
            Span.of(6, 7),
            Span.of(6, 8),
            Span.of(9, 10),
            Span.of(9, 13),
            Span.of(9, 13)
        ),
        ascendingEndIndex.asList()
    );
  }

  @Test
  void emptyAscendingEnd() {
    LabelIndex<?> ascendingEndIndex = empty.ascendingEndIndex();
    assertEquals(empty.asList(), ascendingEndIndex.asList());
  }

  @Test
  void descendingEnd() {
    LabelIndex<Span> descendingEndIndex = ascendingReversing.descendingEndIndex();
    assertSame(ascendingReversing, descendingEndIndex);
  }

  @Test
  void emptyDescendingEnd() {
    LabelIndex<?> descendingEndIndex = empty.descendingEndIndex();
    assertEquals(0, empty.size());
    assertEquals(0, descendingEndIndex.size());
    assertEquals(empty.asList(), descendingEndIndex.asList());
  }

  @Test
  void ascending() {
    LabelIndex<Span> newAscending = ascendingReversing.ascending();
    assertEquals(
        Arrays.asList(
            Span.of(2, 6),
            Span.of(6, 7),
            Span.of(6, 8),
            Span.of(9, 10),
            Span.of(9, 13),
            Span.of(9, 13)
        ),
        newAscending.asList()
    );
  }

  @Test
  void emptyAscending() {
    LabelIndex<?> ascending = empty.ascending();
    assertEquals(empty.asList(), ascending.asList());
  }

  @Test
  void descending() {
    LabelIndex<Span> descending = ascendingReversing.descending();
    assertEquals(Arrays.asList(
        Span.of(9, 13),
        Span.of(9, 13),
        Span.of(9, 10),
        Span.of(6, 8),
        Span.of(6, 7),
        Span.of(2, 6)
    ), descending.asList());
  }

  @Test
  void emptyDescending() {
    LabelIndex<?> descending = empty.descending();
    assertEquals(Collections.emptyList(), descending.asList());
  }

  @Test
  void before() {
    LabelIndex<Span> before = ascendingReversing.before(8);
    assertEquals(Arrays.asList(
        Span.of(2, 6),
        Span.of(6, 8),
        Span.of(6, 7)
    ), before.asList());
  }

  @Test
  void beforeStart() {
    LabelIndex<Span> before = ascendingReversing.before(3);
    assertEquals(Collections.emptyList(), before.asList());
  }

  @Test
  void emptyBefore() {
    LabelIndex<?> before = empty.before(5);
    assertEquals(Collections.emptyList(), before.asList());
  }

  @Test
  void after() {
    LabelIndex<Span> after = ascendingReversing.after(6);
    assertEquals(Arrays.asList(
        Span.of(6, 8),
        Span.of(6, 7),
        Span.of(9, 13),
        Span.of(9, 13),
        Span.of(9, 10)
    ), after.asList());
  }

  @Test
  void afterEnd() {
    LabelIndex<Span> after = ascendingReversing.after(10);
    assertEquals(Collections.emptyList(), after.asList());
  }

  @Test
  void emptyAfter() {
    LabelIndex<?> after = empty.after(2);
    assertEquals(Collections.emptyList(), after.asList());
  }

  @Test
  void emptyFirst() {
    assertNull(empty.first());
  }

  @Test
  void first() {
    assertEquals(Span.of(2, 6), ascendingReversing.first());
  }

  @Test
  void emptyLast() {
    assertNull(empty.last());
  }

  @Test
  void last() {
    assertEquals(Span.of(9, 10), ascendingReversing.last());
  }

  @Test
  void atLocationMultiple() {
    Collection<@NotNull Span> atLocation = ascendingReversing.atLocation(9, 13);
    assertEquals(Arrays.asList(
        Span.of(9, 13),
        Span.of(9, 13)
    ), atLocation);
  }

  @Test
  void atLocationOne() {
    Collection<@NotNull Span> atLocation = ascendingReversing.atLocation(2, 6);
    assertEquals(Collections.singletonList(Span.of(2, 6)), atLocation);
  }

  @Test
  void atLocationDifferentLabel() {
    List<@NotNull Span> atLocation = ascendingReversing.atLocation(GenericLabel.createSpan(2, 6));
    assertEquals(Collections.singletonList(Span.of(2, 6)), atLocation);
  }

  @Test
  void atLocationNone() {
    Collection<@NotNull Span> atLocation = ascendingReversing.atLocation(0, 30);
    assertEquals(Collections.emptyList(), atLocation);
  }

  @Test
  void emptyAtLocation() {
    Collection<?> atLocation = empty.atLocation(0, 0);
    assertEquals(Collections.emptyList(), atLocation);
  }

  @Test
  void atLocationABunch() {
    List<Span> spans = Arrays.asList(
        Span.of(0, 3),
        Span.of(2, 5),
        Span.of(2, Integer.MAX_VALUE),
        Span.of(3, 4),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 6),
        Span.of(4, 0),
        Span.of(6, 10)
    );
    StandardLabelIndex<Span> index = new StandardLabelIndex<>(spans);
    List<@NotNull Span> atLocation = index.atLocation(Span.of(3, 5));
    assertEquals(Arrays.asList(
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5)
    ), atLocation);
  }

  @Test
  void containsTrue() {
    assertTrue(ascendingReversing.contains(Span.of(2, 6)));
  }

  @Test
  void containsNotLabel() {
    assertFalse(ascendingReversing.contains("this is a string"));
  }

  @Test
  void containsNull() {
    assertFalse(ascendingReversing.contains(null));
  }

  @Test
  void containsFalse() {
    assertFalse(ascendingReversing.contains(Span.of(0, 30)));
  }

  @Test
  void emptyContains() {
    assertFalse(empty.contains(Span.of(0, 0)));
  }

  @Test
  void containsSpanTrue() {
    assertTrue(ascendingReversing.containsSpan(2, 6));
  }

  @Test
  void containsSpanFalse() {
    assertFalse(ascendingReversing.containsSpan(0, 30));
  }

  @Test
  void asList() {
    assertEquals(
        Arrays.asList(
            Span.of(2, 6),
            Span.of(6, 8),
            Span.of(6, 7),
            Span.of(9, 13),
            Span.of(9, 13),
            Span.of(9, 10)
        ),
        ascendingReversing.asList());
  }

  @Test
  void emptyAsList() {
    assertEquals(Collections.emptyList(), empty.asList());
  }

  @Test
  void asListIndexOf() {
    assertEquals(3, ascendingReversing.asList().indexOf(Span.of(9, 13)));
  }

  @Test
  void asListIndexOfMany() {
    List<Span> spans = Arrays.asList(
        Span.of(0, 3),
        Span.of(0, 3),
        Span.of(0, 3),
        Span.of(0, 3),
        Span.of(0, 3),
        Span.of(0, 3),
        Span.of(0, 3),
        Span.of(2, 5),
        Span.of(2, 5),
        Span.of(2, 5),
        Span.of(2, 5),
        Span.of(2, 5),
        Span.of(2, 5),
        Span.of(2, 5),
        Span.of(3, 4),
        Span.of(3, 4),
        Span.of(3, 4),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(6, 6),
        Span.of(6, 6),
        Span.of(6, 6),
        Span.of(6, 6),
        Span.of(6, 6),
        Span.of(6, 6),
        Span.of(6, 6),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10)
    );
    LabelIndex<Span> index = new StandardLabelIndex<>(spans).inside(0, 20).descendingEndIndex();
    List<@NotNull Span> asList = index.asList();
    assertEquals(14, asList.indexOf(Span.of(3, 5)));
  }

  @Test
  void asListIndexOfNone() {
    assertEquals(-1, ascendingReversing.asList().indexOf(Span.of(0, 30)));
  }

  @Test
  void asListIndexOfNull() {
    assertEquals(-1, ascendingReversing.asList().indexOf(null));
  }

  @Test
  void asListIndexOfNotLabel() {
    assertEquals(-1, ascendingReversing.asList().indexOf("blah"));
  }

  @Test
  void emptyAsListIndexOf() {
    assertEquals(-1, empty.asList().indexOf(Span.of(9, 13)));
  }

  @Test
  void asListLastIndexOf() {
    assertEquals(4, ascendingReversing.asList().lastIndexOf(Span.of(9, 13)));
  }

  @Test
  void asListLastIndexOfMany() {
    List<Label> spans = Arrays.asList(
        Span.of(0, 3),
        Span.of(0, 3),
        Span.of(0, 3),
        Span.of(0, 3),
        Span.of(0, 3),
        Span.of(0, 3),
        Span.of(0, 3),
        Span.of(2, 5),
        Span.of(2, 5),
        Span.of(2, 5),
        Span.of(2, 5),
        Span.of(2, 5),
        Span.of(2, 5),
        Span.of(2, 5),
        Span.of(3, 4),
        Span.of(3, 4),
        Span.of(3, 4),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        Span.of(3, 5),
        GenericLabel.newBuilder(3, 5).setProperty("foo", "bar").build(),
        Span.of(3, 5),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(5, 6),
        Span.of(6, 6),
        Span.of(6, 6),
        Span.of(6, 6),
        Span.of(6, 6),
        Span.of(6, 6),
        Span.of(6, 6),
        Span.of(6, 6),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10),
        Span.of(6, 10)
    );
    LabelIndex<Label> index = new StandardLabelIndex<>(spans).descendingEndIndex();
    assertEquals(29, index.asList().lastIndexOf(Span.of(3, 5)));
  }

  @Test
  void asListLastIndexOfNone() {
    assertEquals(-1, ascendingReversing.asList().lastIndexOf(Span.of(0, 30)));
  }

  @Test
  void asListLastIndexOfNull() {
    assertEquals(-1, ascendingReversing.asList().lastIndexOf(null));
  }

  @Test
  void asListLastIndexOfNotLabel() {
    assertEquals(-1, ascendingReversing.asList().lastIndexOf("blah"));
  }

  @Test
  void asListContains() {
    List<@NotNull Span> asList = ascendingReversing.asList();
    assertTrue(asList.contains(Span.of(2, 6)));
  }

  @Test
  void asListContainsFalse() {
    List<@NotNull Span> asList = ascendingReversing.asList();
    assertFalse(asList.contains(Span.of(0, 30)));
  }

  @Test
  void emptyAsListContains() {
    List<@NotNull Span> asList = empty.asList();
    assertFalse(asList.contains(Span.of(2, 6)));
  }

  @Test
  void asListGet() {
    List<@NotNull Span> asList = ascendingReversing.asList();
    assertEquals(Span.of(6, 7), asList.get(2));
  }

  @Test
  void asListGetFirst() {
    List<@NotNull Span> asList = ascendingReversing.asList();
    assertEquals(Span.of(2, 6), asList.get(0));
  }

  @Test
  void asListGetLast() {
    List<@NotNull Span> asList = ascendingReversing.asList();
    assertEquals(Span.of(9, 10), asList.get(5));
  }

  @Test
  void asListGetBefore() {
    List<@NotNull Span> asList = ascendingReversing.asList();
    assertThrows(IndexOutOfBoundsException.class, () -> asList.get(-1));
  }

  @Test
  void asListGetAfter() {
    List<@NotNull Span> asList = ascendingReversing.asList();
    assertThrows(IndexOutOfBoundsException.class, () -> asList.get(6));
  }

  @Test
  void emptyAsListGet() {
    List<@NotNull Span> asList = empty.asList();
    assertThrows(IndexOutOfBoundsException.class, () -> asList.get(0));
  }

  @Test
  void asListSubList() {
    List<@NotNull Span> sublist = ascendingReversing.asList().subList(0, 6);
    assertEquals(
        Arrays.asList(
            Span.of(2, 6),
            Span.of(6, 8),
            Span.of(6, 7),
            Span.of(9, 13),
            Span.of(9, 13),
            Span.of(9, 10)
        ),
        sublist
    );
  }

  @Test
  void asListSubListBounds() {
    assertThrows(IndexOutOfBoundsException.class, () -> ascendingReversing.asList().subList(-1, 6));
    assertThrows(IndexOutOfBoundsException.class, () -> ascendingReversing.asList().subList(0, 7));
    assertThrows(IllegalArgumentException.class, () -> ascendingReversing.asList().subList(5, 4));
  }

  @Test
  void asListEmptySubList() {
    List<@NotNull Span> subList = ascendingReversing.asList().subList(3, 3);
    assertEquals(Collections.emptyList(), subList);
  }

  @Test
  void emptyAsListSublist() {
    List<@NotNull Span> subList = empty.asList().subList(0, 0);
    assertEquals(Collections.emptyList(), subList);
  }

  @Test
  void asListIterator() {
    Iterator<@NotNull Span> it = ascendingReversing.asList().iterator();
    assertTrue(it.hasNext());
    assertEquals(Span.of(2, 6), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(6, 8), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(6, 7), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(9, 13), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(9, 13), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(9, 10), it.next());
    assertFalse(it.hasNext());
    assertThrows(NoSuchElementException.class, it::next);
  }

  @Test
  void emptyAsListIterator() {
    Iterator<@NotNull Span> it = empty.asList().iterator();
    assertFalse(it.hasNext());
    assertThrows(NoSuchElementException.class, it::next);
  }

  @Test
  void asListListIteratorOutOfBounds() {
    List<@NotNull Span> asList = ascendingReversing.asList();
    assertThrows(IndexOutOfBoundsException.class, () -> asList.listIterator(7));
    assertThrows(IndexOutOfBoundsException.class, () -> asList.listIterator(-1));
  }

  @Test
  void asListListIterator() {
    ListIterator<@NotNull Span> it = ascendingReversing.asList().listIterator();
    assertTrue(it.hasNext());
    assertEquals(0, it.nextIndex());
    assertEquals(Span.of(2, 6), it.next());
    assertTrue(it.hasNext());
    assertEquals(1, it.nextIndex());
    assertEquals(Span.of(6, 8), it.next());
    assertTrue(it.hasNext());
    assertEquals(2, it.nextIndex());
    assertEquals(Span.of(6, 7), it.next());
    assertTrue(it.hasNext());
    assertEquals(3, it.nextIndex());
    assertEquals(Span.of(9, 13), it.next());
    assertTrue(it.hasNext());
    assertEquals(4, it.nextIndex());
    assertEquals(Span.of(9, 13), it.next());
    assertTrue(it.hasNext());
    assertEquals(5, it.nextIndex());
    assertEquals(Span.of(9, 10), it.next());
    assertFalse(it.hasNext());
    assertThrows(NoSuchElementException.class, it::next);

    assertTrue(it.hasPrevious());
    assertEquals(5, it.previousIndex());
    assertEquals(Span.of(9, 10), it.previous());

    assertTrue(it.hasPrevious());
    assertEquals(4, it.previousIndex());
    assertEquals(Span.of(9, 13), it.previous());

    assertTrue(it.hasPrevious());
    assertEquals(3, it.previousIndex());
    assertEquals(Span.of(9, 13), it.previous());

    assertTrue(it.hasPrevious());
    assertEquals(2, it.previousIndex());
    assertEquals(Span.of(6, 7), it.previous());

    assertTrue(it.hasPrevious());
    assertEquals(1, it.previousIndex());
    assertEquals(Span.of(6, 8), it.previous());

    assertTrue(it.hasPrevious());
    assertEquals(0, it.previousIndex());
    assertEquals(Span.of(2, 6), it.previous());

    assertFalse(it.hasPrevious());
    assertThrows(NoSuchElementException.class, it::previous);
  }

  @Test
  void iterator() {
    Iterator<@NotNull Span> it = ascendingReversing.iterator();
    assertTrue(it.hasNext());
    assertEquals(Span.of(2, 6), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(6, 8), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(6, 7), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(9, 13), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(9, 13), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(9, 10), it.next());
    assertFalse(it.hasNext());
    assertThrows(NoSuchElementException.class, it::next);
  }

  @Test
  void emptyIterator() {
    Iterator<@NotNull Span> it = empty.iterator();
    assertFalse(it.hasNext());
    assertThrows(NoSuchElementException.class, it::next);
  }
}

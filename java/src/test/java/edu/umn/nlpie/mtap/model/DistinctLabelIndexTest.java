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
import org.junit.jupiter.api.Test;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

class DistinctLabelIndexTest {
  DistinctLabelIndex<Span> tested = new DistinctLabelIndex<>(
      Span.of(null, 0, 3),
      Span.of(null, 3, 5),
      Span.of(null, 6, 10),
      Span.of(null, 11, 15),
      Span.of(null, 16, 20)
  );

  DistinctLabelIndex<?> empty = new DistinctLabelIndex<>();

  @Test
  void createSorts() {
    LabelIndex<Span> created = DistinctLabelIndex.create(Arrays.asList(
        Span.of(null, 6, 10),
        Span.of(null, 3, 5),
        Span.of(null, 11, 15),
        Span.of(null, 16, 20),
        Span.of(null, 0, 3)
    ));
    assertEquals(tested.asList(), created.asList());
  }

  @Test
  void isDistinct() {
    assertTrue(tested.isDistinct());
  }

  @Test
  void higherIndexTwoEqual() {
    assertEquals(1, tested.higherIndex(3, null, null));
  }

  @Test
  void higherIndexBeginEquals() {
    assertEquals(2, tested.higherIndex(6, 1, 3));
  }

  @Test
  void higherIndexInside() {
    assertEquals(3, tested.higherIndex(7, 1, 4));
  }

  @Test
  void higherIndexEndEquals() {
    assertEquals(2, tested.higherIndex(5, 1, 3));
  }

  @Test
  void higherIndexBeforeFirst() {
    assertEquals(1, tested.higherIndex(2, 1, 3));
  }

  @Test
  void higherIndexAfterEnd() {
    assertEquals(-1, tested.higherIndex(16, 1, 3));
  }

  @Test
  void lowerIndexTwoEqual() {
    assertEquals(0, tested.lowerIndex(3, null, null));
  }

  @Test
  void lowerIndexBeginEquals() {
    assertEquals(1, tested.lowerIndex(6, 1, 3));
  }

  @Test
  void lowerIndexEndEquals() {
    assertEquals(1, tested.lowerIndex(5, 1, 3));
  }

  @Test
  void lowerIndexInside() {
    assertEquals(1, tested.lowerIndex(7, 1, 3));
  }

  @Test
  void lowerIndexBeforeFirst() {
    assertEquals(-1, tested.lowerIndex(2, 1, 3));
  }

  @Test
  void lowerIndexAfterEnd() {
    assertEquals(2, tested.lowerIndex(16, 1, 3));
  }

  @Test
  void lowerStartTwoEqual() {
    assertEquals(0, tested.lowerStart(0, null, null));
  }

  @Test
  void lowerStartBeginEquals() {
    assertEquals(2, tested.lowerStart(6, 1, 3));
  }

  @Test
  void lowerStartEndEquals() {
    assertEquals(2, tested.lowerStart(10, 1, 3));
  }

  @Test
  void lowerStartInside() {
    assertEquals(2, tested.lowerStart(7, 1, 4));
  }

  @Test
  void lowerStartBeforeFirst() {
    assertEquals(-1, tested.lowerStart(2, 1, 4));
  }

  @Test
  void lowerStartAfterEnd() {
    assertEquals(3, tested.lowerStart(21, 1, 4));
  }

  @Test
  void covering() {
    LabelIndex<Span> covering = tested.covering(Span.of(null, 6, 10));

    assertEquals(1, covering.size());

    Iterator<@NotNull Span> it = covering.iterator();
    assertEquals(it.next(), Span.of(null, 6, 10));
    assertFalse(it.hasNext());
  }

  @Test
  void coveringIndices() {
    LabelIndex<Span> covering = tested.covering(6, 10);

    assertEquals(1, covering.size());

    Iterator<@NotNull Span> it = covering.iterator();
    assertEquals(it.next(), Span.of(null, 6, 10));
    assertFalse(it.hasNext());
  }

  @Test
  void coveringOfEmpty() {
    LabelIndex<?> covering = empty.covering(Span.of(null, 4, 10));

    assertEquals(0, covering.size());
  }

  @Test
  void testCoveringEmptyResult() {
    LabelIndex<Span> covering = tested.covering(Span.of(null, 4, 10));

    assertEquals(0, covering.size());

    Iterator<@NotNull Span> it = covering.iterator();
    assertFalse(it.hasNext());
  }

  @Test
  void emptyInside() {
    LabelIndex<?> inside = empty.inside(10, 20);

    assertEquals(0, inside.size());
  }

  @Test
  void inside() {
    LabelIndex<Span> inside = tested.inside(1, 16);
    assertEquals(Arrays.asList(
        Span.of(null, 3, 5), Span.of(null, 6, 10), Span.of(null, 11, 15)
    ), inside.asList());
  }

  @Test
  void insideLabel() {
    LabelIndex<Span> inside = tested.inside(Span.of(null, 1, 16));
    assertEquals(Arrays.asList(
        Span.of(null, 3, 5), Span.of(null, 6, 10), Span.of(null, 11, 15)
    ), inside.asList());
  }

  @Test
  void insideBefore() {
    LabelIndex<Span> inside = tested.inside(0, 2);

    assertEquals(0, inside.size());

    assertFalse(inside.iterator().hasNext());
  }

  @Test
  void insideAfter() {
    LabelIndex<Span> inside = tested.inside(21, 25);

    assertEquals(0, inside.size());

    assertFalse(inside.iterator().hasNext());
  }

  @Test
  void insideEqualBounds() {
    LabelIndex<Span> inside = tested.inside(6, 10);

    assertEquals(1, inside.size());
    Iterator<@NotNull Span> it = inside.iterator();
    assertTrue(it.hasNext());
    assertEquals(Span.of(null, 6, 10), it.next());
  }

  @Test
  void beginsInsideOverlap() {
    LabelIndex<Span> beginsInside = tested.beginningInside(1, 7);

    assertEquals(Arrays.asList(Span.of(null, 3, 5), Span.of(null, 6, 10)), beginsInside.asList());
  }

  @Test
  void beginsInsideTouching() {
    LabelIndex<Span> beginsInside = tested.beginningInside(0, 6);

    assertEquals(Arrays.asList(Span.of(null, 0, 3), Span.of(null, 3, 5)), beginsInside.asList());
  }

  @Test
  void descending() {
    LabelIndex<Span> descending = tested.descending();

    assertEquals(Arrays.asList(
        Span.of(null, 16, 20),
        Span.of(null, 11, 15),
        Span.of(null, 6, 10),
        Span.of(null, 3, 5),
        Span.of(null, 0, 3)
    ), descending.asList());
  }

  @Test
  void ascending() {
    LabelIndex<Span> ascending = tested.ascending();
    assertSame(tested, ascending);
  }

  @Test
  void before() {
    LabelIndex<Span> before = tested.before(10);

    assertEquals(Arrays.asList(
        Span.of(null, 0, 3),
        Span.of(null, 3, 5),
        Span.of(null, 6, 10)
    ), before.asList());
  }

  @Test
  void beforeLabel() {
    LabelIndex<Span> before = tested.before(Span.of(null, 10, 13));

    assertEquals(Arrays.asList(
        Span.of(null, 0, 3),
        Span.of(null, 3, 5),
        Span.of(null, 6, 10)
    ), before.asList());
  }

  @Test
  void beforeBeginning() {
    LabelIndex<Span> before = tested.before(0);

    assertEquals(0, before.size());
  }

  @Test
  void beforeBeginningLabel() {
    LabelIndex<Span> before = tested.before(Span.of(null, 0, 3));
    assertEquals(0, before.size());
  }

  @Test
  void beforeEnd() {
    LabelIndex<Span> before = tested.before(20);
    assertEquals(tested.asList(), before.asList());
  }

  @Test
  void beforeEndLabel() {
    LabelIndex<Span> before = tested.before(Span.of(null, 20, 25));
    assertEquals(tested.asList(), before.asList());
  }

  @Test
  void after() {
    LabelIndex<Span> after = tested.after(4);

    assertEquals(Arrays.asList(
        Span.of(null, 6, 10), Span.of(null, 11, 15), Span.of(null, 16, 20)
    ), after.asList());
  }

  @Test
  void afterLabel() {
    LabelIndex<Span> after = tested.after(Span.of(null, 0, 4));
    assertEquals(Arrays.asList(
        Span.of(null, 6, 10), Span.of(null, 11, 15), Span.of(null, 16, 20)
    ), after.asList());
  }

  @Test
  void afterBegin() {
    LabelIndex<Span> after = tested.after(0);

    assertEquals(5, after.size());
    assertEquals(tested.asList(), after.asList());
  }

  @Test
  void afterEnd() {
    LabelIndex<Span> after = tested.after(19);
    assertEquals(0, after.size());
  }

  @Test
  void afterEmpty() {
    LabelIndex<?> after = empty.after(0);

    assertEquals(0, after.size());
  }

  @Test
  void firstEmpty() {
    DistinctLabelIndex<Label> labels = new DistinctLabelIndex<>();
    assertNull(labels.first());
  }

  @Test
  void first() {
    assertEquals(Span.of(null, 0, 3), tested.first());
  }

  @Test
  void lastEmpty() {
    DistinctLabelIndex<Label> labels = new DistinctLabelIndex<>();
    assertNull(labels.last());
  }

  @Test
  void last() {
    assertEquals(Span.of(null, 16, 20), tested.last());
  }

  @Test
  void containsNull() {
    assertFalse(tested.contains(null));
  }

  @SuppressWarnings("unlikely-arg-type")
  @Test
  void containsNotLabel() {
    assertFalse(tested.contains("blub"));
  }

  @Test
  void containsFalse() {
    assertFalse(tested.contains(Span.of(null, 7, 10)));
  }

  @SuppressWarnings("unlikely-arg-type")
  @Test
  void containsDifferentLabel() {
    GenericLabel genericLabel = GenericLabel.withSpan(11, 15).setProperty("blah", 1)
        .build();
    assertFalse(tested.contains(genericLabel));
  }

  @Test
  void contains() {
    assertTrue(tested.contains(Span.of(null, 11, 15)));
  }

  @Test
  void emptyContains() {
    assertFalse(empty.contains(Span.of(null, 3, 5)));
  }

  @Test
  void iterator() {
    Iterator<Span> it = tested.iterator();
    assertTrue(it.hasNext());
    assertEquals(Span.of(null, 0, 3), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(null, 3, 5), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(null, 6, 10), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(null, 11, 15), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(null, 16, 20), it.next());
    assertFalse(it.hasNext());
    assertThrows(NoSuchElementException.class, it::next);
  }

  @Test
  void containsSpanTrue() {
    assertTrue(tested.containsSpan(Span.of(null, 3, 5)));
  }

  @Test
  void containsSpanFalse() {
    assertFalse(tested.containsSpan(Span.of(null, 7, 14)));
  }

  @Test
  void containsSpanFalseEqualBegin() {
    assertFalse(tested.containsSpan(3, 4));
  }

  @Test
  void emptyContainsSpan() {
    assertFalse(empty.containsSpan(Span.of(null, 3, 4)));
  }

  @Test
  void atLocation() {
    Collection<@NotNull Span> atLocation = tested.atLocation(3, 5);

    assertEquals(1, atLocation.size());

    Iterator<@NotNull Span> it = atLocation.iterator();
    assertTrue(it.hasNext());
    assertEquals(Span.of(null, 3, 5), it.next());
  }

  @Test
  void atLocationNone() {
    Collection<@NotNull Span> atLocation = tested.atLocation(0, 5);
    assertEquals(0, atLocation.size());
    assertFalse(atLocation.iterator().hasNext());
  }

  @Test
  void emptyAtLocation() {
    Collection<?> atLocation = empty.atLocation(0, 3);
    assertEquals(0, atLocation.size());
    assertFalse(atLocation.iterator().hasNext());
  }

  @Test
  void firstAtLocationNone() {
    Span span = tested.firstAtLocation(0, 5);
    assertNull(span);
  }

  @Test
  void firstAtLocation() {
    Span firstAtLocation = tested.firstAtLocation(3, 5);
    assertEquals(Span.of(null, 3, 5), firstAtLocation);
  }

  @Test
  void firstAtLocationLabel() {
    Span span = tested.firstAtLocation(Span.of(null, 3, 5));
    assertEquals(Span.of(null, 3, 5), span);
  }

  @Test
  void firstAtLocationLabelNone() {
    Span first = tested.firstAtLocation(Span.of(null, 0, 5));
    assertNull(first);
  }

  @Test
  void backwardFrom() {
    LabelIndex<Span> backwardFrom = tested.backwardFrom(10);

    assertEquals(Arrays.asList(
        Span.of(null, 6, 10),
        Span.of(null, 3, 5),
        Span.of(null, 0, 3)
    ), backwardFrom.asList());
  }

  @Test
  void backwardFromLabel() {
    LabelIndex<Span> backwardFrom = tested.backwardFrom(Span.of(null, 10, 15));
    assertEquals(Arrays.asList(
        Span.of(null, 6, 10),
        Span.of(null, 3, 5),
        Span.of(null, 0, 3)
    ), backwardFrom.asList());
  }

  @Test
  void asList() {
    List<Span> asList = tested.asList();

    assertEquals(Arrays.asList(
        Span.of(null, 0, 3),
        Span.of(null, 3, 5),
        Span.of(null, 6, 10),
        Span.of(null, 11, 15),
        Span.of(null, 16, 20)),
        asList);
  }

  @Test
  void emptyAsList() {
    List<?> asList = empty.asList();
    assertEquals(Collections.emptyList(), asList);
  }

  @Test
  void asListIndexOf() {
    List<?> asList = tested.asList();
    assertEquals(2, asList.indexOf(Span.of(null, 6, 10)));
  }

  @Test
  void asListIndexOfNone() {
    List<Span> asList = tested.asList();
    assertEquals(-1, asList.indexOf(Span.of(null, 6, 11)));
  }

  @SuppressWarnings("unlikely-arg-type")
  @Test
  void asListIndexOfNotLabel() {
    List<Span> asList = tested.asList();
    assertEquals(-1, asList.indexOf("foo"));
  }

  @Test
  void emptyAsListIndexOf() {
    List<?> asList = empty.asList();
    assertEquals(-1, asList.indexOf(Span.of(null, 6, 10)));
  }

  @Test
  void asListLastIndexOf() {
    List<Span> asList = tested.asList();
    assertEquals(1, asList.lastIndexOf(Span.of(null, 3, 5)));
  }

  @Test
  void emptyAsListLastIndexOf() {
    List<?> asList = empty.asList();
    assertEquals(-1, asList.lastIndexOf(Span.of(null, 3, 5)));
  }

  @Test
  void asListContains() {
    assertTrue(tested.asList().contains(Span.of(null, 11, 15)));
  }

  @Test
  void emptyAsListContains() {
    assertFalse(empty.asList().contains(Span.of(null, 3, 5)));
  }

  @Test
  void asListContainsNull() {
    assertFalse(tested.asList().contains(null));
  }

  @SuppressWarnings("unlikely-arg-type")
  @Test
  void asListContainsNotLabel() {
    assertFalse(tested.asList().contains("blub"));
  }

  @Test
  void asListContainsFalse() {
    assertFalse(tested.asList().contains(Span.of(null, 7, 10)));
  }

  @SuppressWarnings("unlikely-arg-type")
  @Test
  void asListContainsDifferentLabel() {
    GenericLabel genericLabel = GenericLabel.withSpan(11, 15).setProperty("blah", 1)
        .build();
    assertFalse(tested.asList().contains(genericLabel));
  }
}
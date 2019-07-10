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

package edu.umn.nlpnewt.model;

import org.jetbrains.annotations.NotNull;
import org.junit.jupiter.api.Test;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

public class DistinctLabelIndexAscendingViewTest {
  LabelIndex<Span> ascending = new DistinctLabelIndex<>(
      Span.of(0, 3),
      Span.of(3, 5),
      Span.of(6, 10),
      Span.of(11, 15),
      Span.of(16, 20),
      Span.of(21, 25)).inside(0, 20);

  LabelIndex<Span> emptyAscending = ascending.inside(0, 2);

  @Test
  void isDistinct() {
    assertTrue(ascending.isDistinct());
  }


  @Test
  void viewSize() {
    assertEquals(5, ascending.size());
  }

  @Test
  void emptyViewSize() {
    assertEquals(0, emptyAscending.size());
  }

  @Test
  void ascendingFirst() {
    assertEquals(Span.of(0, 3), ascending.first());
  }

  @Test
  void emptyAscendingFirst() {
    assertNull(emptyAscending.first());
  }

  @Test
  void ascendingLast() {
    assertEquals(Span.of(16, 20), ascending.last());
  }

  @Test
  void emptyAscendingLast() {
    assertNull(emptyAscending.last());
  }

  @Test
  void atLocation() {
    Collection<@NotNull Span> atLocation = ascending.atLocation(Span.of(16, 20));
    assertEquals(1, atLocation.size());
    assertEquals(Span.of(16, 20), atLocation.iterator().next());
  }

  @Test
  void atLocationNotInsideView() {
    Collection<@NotNull Span> atLocation = ascending.atLocation(Span.of(21, 25));
    assertEquals(0, atLocation.size());
  }

  @Test
  void atLocationEmpty() {
    Collection<@NotNull Span> atLocation = ascending.atLocation(0, 0);
    assertEquals(0, atLocation.size());
  }

  @Test
  void emptyAtLocation() {
    assertEquals(0, emptyAscending.atLocation(0, 3).size());
  }

  @Test
  void containsNull() {
    assertFalse(ascending.contains(null));
  }

  @Test
  void containsNotLabel() {
    assertFalse(ascending.contains("blub"));
  }

  @Test
  void containsFalse() {
    assertFalse(ascending.contains(Span.of(7, 10)));
  }

  @Test
  void containsDifferentLabel() {
    GenericLabel genericLabel = GenericLabel.newBuilder(11, 15).setProperty("blah", 1)
        .build();
    assertFalse(ascending.contains(genericLabel));
  }

  @Test
  void contains() {
    assertTrue(ascending.contains(Span.of(11, 15)));
  }

  @Test
  void emptyContains() {
    assertFalse(emptyAscending.contains(Span.of(3, 5)));
  }

  @Test
  void containsSpanTrue() {
    assertTrue(ascending.containsSpan(Span.of(3, 5)));
  }

  @Test
  void containsSpanFalse() {
    assertFalse(ascending.containsSpan(Span.of(7, 14)));
  }

  @Test
  void containsSpanFalseEqualBegin() {
    assertFalse(ascending.containsSpan(3, 4));
  }

  @Test
  void emptyContainsSpan() {
    assertFalse(emptyAscending.containsSpan(Span.of(3, 4)));
  }

  @Test
  void before() {
    LabelIndex<Span> before = ascending.before(10);
    assertEquals(3, before.size());
    assertEquals(Arrays.asList(
        Span.of(0, 3),
        Span.of(3, 5),
        Span.of(6, 10)
    ), before.asList());
  }

  @Test
  void beforeEmpty() {
    LabelIndex<Span> before = ascending.before(2);
    assertEquals(0, before.size());
  }

  @Test
  void emptyBefore() {
    LabelIndex<Span> before = emptyAscending.before(10);
    assertEquals(0, before.size());
  }

  @Test
  void after() {
    LabelIndex<Span> after = ascending.after(6);
    assertEquals(3, after.size());
    assertEquals(Arrays.asList(
        Span.of(6, 10), Span.of(11, 15), Span.of(16, 20)
    ), after.asList());
  }

  @Test
  void afterEmpty() {
    LabelIndex<Span> after = ascending.after(19);
    assertEquals(0, after.size());
  }

  @Test
  void emptyAfter() {
    LabelIndex<Span> after = emptyAscending.after(6);
    assertEquals(0, after.size());
  }

  @Test
  void inside() {
    LabelIndex<Span> inside = ascending.inside(3, 20);
    assertEquals(Arrays.asList(
        Span.of(3, 5), Span.of(6, 10), Span.of(11, 15), Span.of(16, 20)
    ), inside.asList());
  }

  @Test
  void insideEmpty() {
    LabelIndex<Span> inside = ascending.inside(7, 10);
    assertEquals(Collections.emptyList(), inside.asList());
  }

  @Test
  void emptyInside() {
    LabelIndex<Span> inside = emptyAscending.inside(3, 20);
    assertEquals(Collections.emptyList(), inside.asList());
  }

  @Test
  void beginsInside() {
    LabelIndex<Span> beginsInside = ascending.beginningInside(Span.of(4, 22));
    assertEquals(Arrays.asList(
        Span.of(6, 10), Span.of(11, 15), Span.of(16, 20)
    ), beginsInside.asList());
  }

  @Test
  void emptyBeginsInside() {
    LabelIndex<Span> beginsInside = emptyAscending.beginningInside(4, 22);
    assertEquals(Collections.emptyList(), beginsInside.asList());
  }

  @Test
  void covering() {
    LabelIndex<Span> covering = ascending.covering(Span.of(7, 10));
    assertEquals(Collections.singletonList(Span.of(6, 10)), covering.asList());
  }

  @Test
  void coveringEmpty() {
    LabelIndex<Span> covering = ascending.covering(Span.of(7, 12));
    assertEquals(Collections.emptyList(), covering.asList());
  }

  @Test
  void ascending() {
    LabelIndex<Span> newAscending = ascending.ascending();
    assertSame(ascending, newAscending);
  }

  @Test
  void descending() {
    LabelIndex<Span> descending = ascending.descending();
    assertEquals(Arrays.asList(
        Span.of(16, 20), Span.of(11, 15), Span.of(6, 10), Span.of(3, 5), Span.of(0, 3)),
        descending.asList()
    );
  }

  @Test
  void listGet() {
    Span span = ascending.asList().get(2);
    assertEquals(Span.of(6, 10), span);
  }

  @Test
  void listGetBeforeZero() {
    assertThrows(IndexOutOfBoundsException.class, () -> ascending.asList().get(-1));
  }

  @Test
  void listGetAfter() {
    assertThrows(IndexOutOfBoundsException.class, () -> ascending.asList().get(5));
  }

  @Test
  void offsetListGet() {
    Span span = ascending.inside(3, 15).asList().get(2);
    assertEquals(Span.of(11, 15), span);
  }

  @Test
  void listContainsNull() {
    assertFalse(ascending.asList().contains(null));
  }

  @Test
  void listContainsNotLabel() {
    assertFalse(ascending.asList().contains("blub"));
  }

  @Test
  void listContainsFalse() {
    assertFalse(ascending.asList().contains(Span.of(7, 10)));
  }

  @Test
  void listContainsDifferentLabel() {
    GenericLabel genericLabel = GenericLabel.newBuilder(11, 15).setProperty("blah", 1)
        .build();
    assertFalse(ascending.asList().contains(genericLabel));
  }

  @Test
  void listContains() {
    assertTrue(ascending.asList().contains(Span.of(11, 15)));
  }

  @Test
  void emptyAsListContains() {
    assertFalse(emptyAscending.asList().contains(Span.of(3, 5)));
  }

  @Test
  void asListIndexOf() {
    assertEquals(1, ascending.asList().indexOf(Span.of(3, 5)));
  }

  @Test
  void offsetAsListIndexOf() {
    assertEquals(0, ascending.inside(3, 15).asList().indexOf(Span.of(3, 5)));
  }

  @Test
  void asListIndexOfFalse() {
    assertEquals(-1, ascending.inside(3, 15).asList().indexOf(Span.of(3, 6)));
  }

  @Test
  void asListIndexOfNotLabel() {
    assertEquals(-1, ascending.inside(3, 15).asList().indexOf("huh"));
  }

  @Test
  void emptyAsListIndexOf() {
    assertEquals(-1, emptyAscending.asList().indexOf(Span.of(3, 5)));
  }

  @Test
  void asListLastIndexOf() {
    assertEquals(2, ascending.asList().lastIndexOf(Span.of(6, 10)));
  }

  @Test
  void offsetAsListLastIndexOf() {
    assertEquals(1, ascending.inside(3, 15).asList().lastIndexOf(Span.of(6, 10)));
  }

  @Test
  void asListLastIndexOfFalse() {
    assertEquals(-1, ascending.inside(3, 15).asList().lastIndexOf(Span.of(3, 6)));
  }

  @Test
  void asListLastIndexOfNotLabel() {
    assertEquals(-1, ascending.inside(3, 15).asList().lastIndexOf("huh"));
  }

  @Test
  void emptyAsListLastIndexOf() {
    assertEquals(-1, emptyAscending.asList().lastIndexOf(Span.of(3, 5)));
  }

  @Test
  void iterator() {
    Iterator<@NotNull Span> it = ascending.iterator();
    assertTrue(it.hasNext());
    assertEquals(Span.of(0, 3), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(3, 5), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(6, 10), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(11, 15), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(16, 20), it.next());
    assertFalse(it.hasNext());
    assertThrows(NoSuchElementException.class, it::next);
  }
}


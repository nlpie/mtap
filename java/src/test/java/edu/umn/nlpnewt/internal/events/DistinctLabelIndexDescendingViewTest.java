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

package edu.umn.nlpnewt.internal.events;

import edu.umn.nlpnewt.GenericLabel;
import edu.umn.nlpnewt.LabelIndex;
import edu.umn.nlpnewt.internal.events.DistinctLabelIndex;
import edu.umn.nlpnewt.internal.events.Span;
import org.jetbrains.annotations.NotNull;
import org.junit.jupiter.api.Test;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

public class DistinctLabelIndexDescendingViewTest {
  LabelIndex<Span> descending = new DistinctLabelIndex<>(
      Span.of(0, 3),
      Span.of(3, 5),
      Span.of(6, 10),
      Span.of(11, 15),
      Span.of(16, 20),
      Span.of(21, 25)).inside(3, 20).descending();

  LabelIndex<Span> emptyDescending = descending.inside(0, 2);

  @Test
  void isDistinct() {
    assertTrue(descending.isDistinct());
  }


  @Test
  void viewSize() {
    assertEquals(4, descending.size());
  }

  @Test
  void emptyViewSize() {
    assertEquals(0, emptyDescending.size());
  }

  @Test
  void ascendingFirst() {
    assertEquals(Span.of(16, 20), descending.first());
  }

  @Test
  void emptyAscendingFirst() {
    assertNull(emptyDescending.first());
  }

  @Test
  void ascendingLast() {
    assertEquals(Span.of(3, 5), descending.last());
  }

  @Test
  void emptyAscendingLast() {
    assertNull(emptyDescending.last());
  }

  @Test
  void atLocation() {
    Collection<@NotNull Span> atLocation = descending.atLocation(Span.of(16, 20));
    assertEquals(1, atLocation.size());
    assertEquals(Span.of(16, 20), atLocation.iterator().next());
  }

  @Test
  void atLocationNotInsideView() {
    Collection<@NotNull Span> atLocation = descending.atLocation(Span.of(21, 25));
    assertEquals(0, atLocation.size());
  }

  @Test
  void atLocationEmpty() {
    Collection<@NotNull Span> atLocation = descending.atLocation(0, 0);
    assertEquals(0, atLocation.size());
  }

  @Test
  void emptyAtLocation() {
    assertEquals(0, emptyDescending.atLocation(0, 3).size());
  }

  @Test
  void containsNull() {
    assertFalse(descending.contains(null));
  }

  @Test
  void containsNotLabel() {
    assertFalse(descending.contains("blub"));
  }

  @Test
  void containsFalse() {
    assertFalse(descending.contains(Span.of(7, 10)));
  }

  @Test
  void containsDifferentLabel() {
    GenericLabel genericLabel = GenericLabel.newBuilder(11, 15).setProperty("blah", 1)
        .build();
    assertFalse(descending.contains(genericLabel));
  }

  @Test
  void contains() {
    assertTrue(descending.contains(Span.of(11, 15)));
  }

  @Test
  void emptyContains() {
    assertFalse(emptyDescending.contains(Span.of(3, 5)));
  }

  @Test
  void containsSpanTrue() {
    assertTrue(descending.containsSpan(Span.of(3, 5)));
  }

  @Test
  void containsSpanFalse() {
    assertFalse(descending.containsSpan(Span.of(7, 14)));
  }

  @Test
  void containsSpanFalseEqualBegin() {
    assertFalse(descending.containsSpan(3, 4));
  }

  @Test
  void emptyContainsSpan() {
    assertFalse(emptyDescending.containsSpan(Span.of(3, 4)));
  }

  @Test
  void before() {
    LabelIndex<Span> before = descending.before(10);
    assertEquals(Arrays.asList(
        Span.of(6, 10),
        Span.of(3, 5)
    ), before.asList());
  }

  @Test
  void beforeEmpty() {
    LabelIndex<Span> before = descending.before(2);
    assertEquals(0, before.size());
  }

  @Test
  void emptyBefore() {
    LabelIndex<Span> before = emptyDescending.before(10);
    assertEquals(0, before.size());
  }

  @Test
  void after() {
    LabelIndex<Span> after = descending.after(6);
    assertEquals(3, after.size());
    assertEquals(Arrays.asList(
        Span.of(16, 20), Span.of(11, 15), Span.of(6, 10)
    ), after.asList());
  }

  @Test
  void afterEmpty() {
    LabelIndex<Span> after = descending.after(19);
    assertEquals(0, after.size());
  }

  @Test
  void emptyAfter() {
    LabelIndex<Span> after = emptyDescending.after(6);
    assertEquals(0, after.size());
  }

  @Test
  void inside() {
    LabelIndex<Span> inside = descending.inside(3, 20);
    assertEquals(Arrays.asList(
        Span.of(16, 20), Span.of(11, 15), Span.of(6, 10), Span.of(3, 5)
    ), inside.asList());
  }

  @Test
  void insideEmpty() {
    LabelIndex<Span> inside = descending.inside(7, 10);
    assertEquals(Collections.emptyList(), inside.asList());
  }

  @Test
  void emptyInside() {
    LabelIndex<Span> inside = emptyDescending.inside(3, 20);
    assertEquals(Collections.emptyList(), inside.asList());
  }

  @Test
  void beginsInside() {
    LabelIndex<Span> beginsInside = descending.beginningInside(Span.of(4, 22));
    assertEquals(Arrays.asList(
        Span.of(16, 20), Span.of(11, 15), Span.of(6, 10)
    ), beginsInside.asList());
  }

  @Test
  void emptyBeginsInside() {
    LabelIndex<Span> beginsInside = emptyDescending.beginningInside(4, 22);
    assertEquals(Collections.emptyList(), beginsInside.asList());
  }

  @Test
  void covering() {
    LabelIndex<Span> covering = descending.covering(Span.of(7, 10));
    assertEquals(Collections.singletonList(Span.of(6, 10)), covering.asList());
  }

  @Test
  void coveringEmpty() {
    LabelIndex<Span> covering = descending.covering(Span.of(7, 12));
    assertEquals(Collections.emptyList(), covering.asList());
  }

  @Test
  void ascending() {
    LabelIndex<Span> newAscending = descending.ascending();
    assertEquals(Arrays.asList(
        Span.of(3, 5), Span.of(6, 10), Span.of(11, 15), Span.of(16, 20)
    ), newAscending.asList());
  }

  @Test
  void emptyAscending() {
    LabelIndex<Span> ascending = emptyDescending.ascending();
    assertEquals(Collections.emptyList(), ascending.asList());
  }

  @Test
  void descendingEndIndex() {
    LabelIndex<Span> newDescending = descending.descending();
    assertSame(descending, newDescending);
  }

  @Test
  void forwardFrom() {
    LabelIndex<Span> forwardFrom = descending.forwardFrom(6);
    assertEquals(Arrays.asList(
        Span.of(6, 10), Span.of(11, 15), Span.of(16, 20)
    ), forwardFrom.asList());
  }

  @Test
  void forwardFromLabel() {
    LabelIndex<Span> forwardFrom = descending.forwardFrom(Span.of(5, 6));
    assertEquals(Arrays.asList(
        Span.of(6, 10), Span.of(11, 15), Span.of(16, 20)
    ), forwardFrom.asList());
  }

  @Test
  void listGet() {
    Span span = descending.asList().get(1);
    assertEquals(Span.of(11, 15), span);
  }

  @Test
  void listGetBeforeZero() {
    assertThrows(IndexOutOfBoundsException.class, () -> descending.asList().get(-1));
  }

  @Test
  void listGetAfter() {
    assertThrows(IndexOutOfBoundsException.class, () -> descending.asList().get(4));
  }

  @Test
  void listContainsNull() {
    assertFalse(descending.asList().contains(null));
  }

  @Test
  void listContainsNotLabel() {
    assertFalse(descending.asList().contains("blub"));
  }

  @Test
  void listContainsFalse() {
    assertFalse(descending.asList().contains(Span.of(7, 10)));
  }

  @Test
  void listContainsDifferentLabel() {
    GenericLabel genericLabel = GenericLabel.newBuilder(11, 15).setProperty("blah", 1)
        .build();
    assertFalse(descending.asList().contains(genericLabel));
  }

  @Test
  void listContains() {
    assertTrue(descending.asList().contains(Span.of(11, 15)));
  }

  @Test
  void emptyAsListContains() {
    assertFalse(emptyDescending.asList().contains(Span.of(3, 5)));
  }

  @Test
  void asListIndexOf() {
    assertEquals(3, descending.asList().indexOf(Span.of(3, 5)));
  }

  @Test
  void asListIndexOfFalse() {
    assertEquals(-1, descending.inside(3, 15).asList().indexOf(Span.of(3, 6)));
  }

  @Test
  void asListIndexOfNotLabel() {
    assertEquals(-1, descending.inside(3, 15).asList().indexOf("huh"));
  }

  @Test
  void emptyAsListIndexOf() {
    assertEquals(-1, emptyDescending.asList().indexOf(Span.of(3, 5)));
  }

  @Test
  void asListLastIndexOf() {
    assertEquals(2, descending.asList().lastIndexOf(Span.of(6, 10)));
  }

  @Test
  void asListLastIndexOfFalse() {
    assertEquals(-1, descending.inside(3, 15).asList().lastIndexOf(Span.of(3, 6)));
  }

  @Test
  void asListLastIndexOfNotLabel() {
    assertEquals(-1, descending.inside(3, 15).asList().lastIndexOf("huh"));
  }

  @Test
  void emptyAsListLastIndexOf() {
    assertEquals(-1, emptyDescending.asList().lastIndexOf(Span.of(3, 5)));
  }

  @Test
  void iterator() {
    Iterator<@NotNull Span> it = descending.iterator();
    assertTrue(it.hasNext());
    assertEquals(Span.of(16, 20), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(11, 15), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(6, 10), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(3, 5), it.next());
    assertFalse(it.hasNext());
    assertThrows(NoSuchElementException.class, it::next);
  }
}

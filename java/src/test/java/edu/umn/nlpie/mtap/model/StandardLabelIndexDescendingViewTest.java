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

public class StandardLabelIndexDescendingViewTest {
  LabelIndex<Span> descending = new StandardLabelIndex<>(Arrays.asList(
      Span.of(null, 0, 5),
      Span.of(null, 0, 7),
      Span.of(null, 2, 6),
      Span.of(null, 6, 7),
      Span.of(null, 6, 8),
      Span.of(null, 9, 10),
      Span.of(null, 9, 13),
      Span.of(null, 9, 13),
      Span.of(null, 9, 20),
      Span.of(null, 10, 20),
      Span.of(null, 10, 20),
      Span.of(null, 15, 20)
  )).inside(1, 15).descending();

  LabelIndex<Span> empty = descending.inside(0, 0);


  @Test
  void isDistinct() {
    assertFalse(descending.isDistinct());
  }

  @Test
  void size() {
    assertEquals(6, descending.size());
  }

  @Test
  void covering() {
    LabelIndex<Span> covering = descending.covering(Span.of(null, 2, 4));
    assertEquals(
        Collections.singletonList(Span.of(null, 2, 6)),
        covering.asList()
    );
  }

  @Test
  void coveringEquals() {
    LabelIndex<Span> covering = descending.covering(Span.of(null, 6, 8));
    assertEquals(Collections.singletonList(Span.of(null, 6, 8)), covering.asList());
  }

  @Test
  void coveringEmpty() {
    LabelIndex<Span> covering = descending.covering(4, 10);
    assertEquals(0, covering.size());
  }

  @Test
  void emptyCovering() {
    LabelIndex<?> covering = descending.covering(4, 10);
    assertEquals(0, covering.size());
  }

  @Test
  void inside() {
    LabelIndex<Span> inside = descending.inside(3, 10);

    assertEquals(Arrays.asList(Span.of(null, 9, 10), Span.of(null, 6, 8), Span.of(null, 6, 7)), inside.asList());
  }

  @Test
  void insideBefore() {
    LabelIndex<Span> inside = descending.inside(0, 3);
    assertEquals(0, inside.size());
  }

  @Test
  void insideAfter() {
    LabelIndex<Span> inside = descending.inside(Span.of(null, 15, 20));
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
        Span.of(null, 0, 3),
        Span.of(null, 0, 3),
        Span.of(null, 0, 3),
        Span.of(null, 0, 3),
        Span.of(null, 0, 3),
        Span.of(null, 0, 3),
        Span.of(null, 0, 3),
        Span.of(null, 2, 5),
        Span.of(null, 2, 5),
        Span.of(null, 2, 5),
        Span.of(null, 2, 5),
        Span.of(null, 2, 5),
        Span.of(null, 2, 5),
        Span.of(null, 2, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 6, 6),
        Span.of(null, 6, 6),
        Span.of(null, 6, 6),
        Span.of(null, 6, 6),
        Span.of(null, 6, 6),
        Span.of(null, 6, 6),
        Span.of(null, 6, 6),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10)
    );
    LabelIndex<Span> index = new StandardLabelIndex<>(spans).descending();
    LabelIndex<Span> inside = index.inside(3, 6);
    assertEquals(Arrays.asList(
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5)
    ), inside.asList());
  }

  @Test
  void beginsInside() {
    LabelIndex<Span> beginsInside = descending.beginningInside(Span.of(null, 1, 10));
    assertEquals(Arrays.asList(
        Span.of(null, 9, 13),
        Span.of(null, 9, 13),
        Span.of(null, 9, 10),
        Span.of(null, 6, 8),
        Span.of(null, 6, 7),
        Span.of(null, 2, 6)),
        beginsInside.asList()
    );
  }

  @Test
  void beginsInsideEmpty() {
    LabelIndex<Span> beginsInside = descending.beginningInside(3, 5);
    assertEquals(Collections.emptyList(), beginsInside.asList());
  }

  @Test
  void emptyBeginsInside() {
    LabelIndex<?> beginsInside = empty.beginningInside(0, 5);
    assertEquals(Collections.emptyList(), beginsInside.asList());
  }

  @Test
  void ascending() {
    LabelIndex<Span> newAscending = descending.ascending();
    assertEquals(
        Arrays.asList(
            Span.of(null, 2, 6),
            Span.of(null, 6, 7),
            Span.of(null, 6, 8),
            Span.of(null, 9, 10),
            Span.of(null, 9, 13),
            Span.of(null, 9, 13)
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
    LabelIndex<Span> newDescending = descending.descending();
    assertSame(descending, newDescending);
  }

  @Test
  void emptyDescending() {
    LabelIndex<?> descending = empty.descending();
    assertEquals(Collections.emptyList(), descending.asList());
  }

  @Test
  void before() {
    LabelIndex<Span> before = descending.before(8);
    assertEquals(Arrays.asList(
        Span.of(null, 6, 8),
        Span.of(null, 6, 7),
        Span.of(null, 2, 6)
    ), before.asList());
  }

  @Test
  void beforeStart() {
    LabelIndex<Span> before = descending.before(3);
    assertEquals(Collections.emptyList(), before.asList());
  }

  @Test
  void emptyBefore() {
    LabelIndex<?> before = empty.before(5);
    assertEquals(Collections.emptyList(), before.asList());
  }

  @Test
  void after() {
    LabelIndex<Span> after = descending.after(6);
    assertEquals(Arrays.asList(
        Span.of(null, 9, 13),
        Span.of(null, 9, 13),
        Span.of(null, 9, 10),
        Span.of(null, 6, 8),
        Span.of(null, 6, 7)
    ), after.asList());
  }

  @Test
  void afterEnd() {
    LabelIndex<Span> after = descending.after(10);
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
    assertEquals(Span.of(null, 9, 13), descending.first());
  }

  @Test
  void emptyLast() {
    assertNull(empty.last());
  }

  @Test
  void last() {
    assertEquals(Span.of(null, 2, 6), descending.last());
  }

  @Test
  void atLocationMultiple() {
    Collection<@NotNull Span> atLocation = descending.atLocation(9, 13);
    assertEquals(Arrays.asList(
        Span.of(null, 9, 13),
        Span.of(null, 9, 13)
    ), atLocation);
  }

  @Test
  void atLocationOne() {
    Collection<@NotNull Span> atLocation = descending.atLocation(2, 6);
    assertEquals(Collections.singletonList(Span.of(null, 2, 6)), atLocation);
  }

  @Test
  void atLocationDifferentLabel() {
    List<@NotNull Span> atLocation = descending.atLocation(GenericLabel.createSpan(2, 6));
    assertEquals(Collections.singletonList(Span.of(null, 2, 6)), atLocation);
  }

  @Test
  void atLocationNone() {
    Collection<@NotNull Span> atLocation = descending.atLocation(0, 30);
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
        Span.of(null, 0, 3),
        Span.of(null, 2, 5),
        Span.of(null, 2, Integer.MAX_VALUE),
        Span.of(null, 3, 4),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 6),
        Span.of(null, 4, 0),
        Span.of(null, 6, 10)
    );
    LabelIndex<Span> index = new StandardLabelIndex<>(spans).descending();
    List<@NotNull Span> atLocation = index.atLocation(Span.of(null, 3, 5));
    assertEquals(Arrays.asList(
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5)
    ), atLocation);
  }

  @Test
  void containsTrue() {
    assertTrue(descending.contains(Span.of(null, 2, 6)));
  }

  @Test
  void containsNotLabel() {
    assertFalse(descending.contains("this is a string"));
  }

  @Test
  void containsNull() {
    assertFalse(descending.contains(null));
  }

  @Test
  void containsFalse() {
    assertFalse(descending.contains(Span.of(null, 0, 30)));
  }

  @Test
  void emptyContains() {
    assertFalse(empty.contains(Span.of(null, 0, 0)));
  }

  @Test
  void containsSpanTrue() {
    assertTrue(descending.containsSpan(2, 6));
  }

  @Test
  void containsSpanFalse() {
    assertFalse(descending.containsSpan(0, 30));
  }

  @Test
  void asList() {
    assertEquals(Arrays.asList(
        Span.of(null, 9, 13),
        Span.of(null, 9, 13),
        Span.of(null, 9, 10),
        Span.of(null, 6, 8),
        Span.of(null, 6, 7),
        Span.of(null, 2, 6)
    ), descending.asList());
  }

  @Test
  void emptyAsList() {
    assertEquals(Collections.emptyList(), empty.asList());
  }

  @Test
  void asListIndexOf() {
    assertEquals(0, descending.asList().indexOf(Span.of(null, 9, 13)));
  }

  @Test
  void asListIndexOfMany() {
    List<Span> spans = Arrays.asList(
        Span.of(null, 0, 3),
        Span.of(null, 0, 3),
        Span.of(null, 0, 3),
        Span.of(null, 0, 3),
        Span.of(null, 0, 3),
        Span.of(null, 0, 3),
        Span.of(null, 0, 3),
        Span.of(null, 2, 5),
        Span.of(null, 2, 5),
        Span.of(null, 2, 5),
        Span.of(null, 2, 5),
        Span.of(null, 2, 5),
        Span.of(null, 2, 5),
        Span.of(null, 2, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 6, 6),
        Span.of(null, 6, 6),
        Span.of(null, 6, 6),
        Span.of(null, 6, 6),
        Span.of(null, 6, 6),
        Span.of(null, 6, 6),
        Span.of(null, 6, 6),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10)
    );
    LabelIndex<Span> index = new StandardLabelIndex<>(spans).descending();
    assertEquals(38, index.asList().indexOf(Span.of(null, 3, 5)));
  }

  @Test
  void asListIndexOfNone() {
    assertEquals(-1, descending.asList().indexOf(Span.of(null, 0, 30)));
  }

  @Test
  void asListIndexOfNull() {
    assertEquals(-1, descending.asList().indexOf(null));
  }

  @Test
  void asListIndexOfNotLabel() {
    assertEquals(-1, descending.asList().indexOf("blah"));
  }

  @Test
  void emptyAsListIndexOf() {
    assertEquals(-1, empty.asList().indexOf(Span.of(null, 9, 13)));
  }

  @Test
  void asListLastIndexOf() {
    assertEquals(1, descending.asList().lastIndexOf(Span.of(null, 9, 13)));
  }

  @Test
  void asListLastIndexOfMany() {
    List<Label> spans = Arrays.asList(
        Span.of(null, 0, 3),
        Span.of(null, 0, 3),
        Span.of(null, 0, 3),
        Span.of(null, 0, 3),
        Span.of(null, 0, 3),
        Span.of(null, 0, 3),
        Span.of(null, 0, 3),
        Span.of(null, 2, 5),
        Span.of(null, 2, 5),
        Span.of(null, 2, 5),
        Span.of(null, 2, 5),
        Span.of(null, 2, 5),
        Span.of(null, 2, 5),
        Span.of(null, 2, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        Span.of(null, 3, 5),
        GenericLabel.withSpan(3, 5).setProperty("foo", "bar").build(),
        Span.of(null, 3, 5),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 5, 6),
        Span.of(null, 6, 6),
        Span.of(null, 6, 6),
        Span.of(null, 6, 6),
        Span.of(null, 6, 6),
        Span.of(null, 6, 6),
        Span.of(null, 6, 6),
        Span.of(null, 6, 6),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10),
        Span.of(null, 6, 10)
    );
    LabelIndex<Label> index = new StandardLabelIndex<>(spans).descending();
    assertEquals(53, index.asList().lastIndexOf(Span.of(null, 3, 5)));
  }

  @Test
  void asListLastIndexOfNone() {
    assertEquals(-1, descending.asList().lastIndexOf(Span.of(null, 0, 30)));
  }

  @Test
  void asListLastIndexOfNull() {
    assertEquals(-1, descending.asList().lastIndexOf(null));
  }

  @Test
  void asListLastIndexOfNotLabel() {
    assertEquals(-1, descending.asList().lastIndexOf("blah"));
  }

  @Test
  void asListContains() {
    List<@NotNull Span> asList = descending.asList();
    assertTrue(asList.contains(Span.of(null, 2, 6)));
  }

  @Test
  void asListContainsFalse() {
    List<@NotNull Span> asList = descending.asList();
    assertFalse(asList.contains(Span.of(null, 0, 30)));
  }

  @Test
  void emptyAsListContains() {
    List<@NotNull Span> asList = empty.asList();
    assertFalse(asList.contains(Span.of(null, 2, 6)));
  }

  @Test
  void asListGet() {
    List<@NotNull Span> asList = descending.asList();
    assertEquals(Span.of(null, 9, 10), asList.get(2));
  }

  @Test
  void asListGetFirst() {
    List<@NotNull Span> asList = descending.asList();
    assertEquals(Span.of(null, 9, 13), asList.get(0));
  }

  @Test
  void asListGetLast() {
    List<@NotNull Span> asList = descending.asList();
    assertEquals(Span.of(null, 2, 6), asList.get(5));
  }

  @Test
  void asListGetBefore() {
    List<@NotNull Span> asList = descending.asList();
    assertThrows(IndexOutOfBoundsException.class, () -> asList.get(-1));
  }

  @Test
  void asListGetAfter() {
    List<@NotNull Span> asList = descending.asList();
    assertThrows(IndexOutOfBoundsException.class, () -> asList.get(6));
  }

  @Test
  void emptyAsListGet() {
    List<@NotNull Span> asList = empty.asList();
    assertThrows(IndexOutOfBoundsException.class, () -> asList.get(0));
  }

  @Test
  void asListSubList() {
    List<@NotNull Span> sublist = descending.asList().subList(0, 6);
    assertEquals(Arrays.asList(
        Span.of(null, 9, 13),
        Span.of(null, 9, 13),
        Span.of(null, 9, 10),
        Span.of(null, 6, 8),
        Span.of(null, 6, 7),
        Span.of(null, 2, 6)
    ), sublist);
  }

  @Test
  void asListSubListBounds() {
    assertThrows(IndexOutOfBoundsException.class, () -> descending.asList().subList(-1, 6));
    assertThrows(IndexOutOfBoundsException.class, () -> descending.asList().subList(0, 7));
    assertThrows(IllegalArgumentException.class, () -> descending.asList().subList(5, 4));
  }

  @Test
  void asListEmptySubList() {
    List<@NotNull Span> subList = descending.asList().subList(3, 3);
    assertEquals(Collections.emptyList(), subList);
  }

  @Test
  void emptyAsListSublist() {
    List<@NotNull Span> subList = empty.asList().subList(0, 0);
    assertEquals(Collections.emptyList(), subList);
  }

  @Test
  void asListIterator() {
    Iterator<@NotNull Span> it = descending.asList().iterator();
    assertTrue(it.hasNext());
    assertEquals(Span.of(null, 9, 13), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(null, 9, 13), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(null, 9, 10), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(null, 6, 8), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(null, 6, 7), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(null, 2, 6), it.next());
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
    List<@NotNull Span> asList = descending.asList();
    assertThrows(IndexOutOfBoundsException.class, () -> asList.listIterator(7));
    assertThrows(IndexOutOfBoundsException.class, () -> asList.listIterator(-1));
  }

  @Test
  void asListListIterator() {
    ListIterator<@NotNull Span> it = descending.asList().listIterator();
    assertTrue(it.hasNext());
    assertEquals(0, it.nextIndex());
    assertEquals(Span.of(null, 9, 13), it.next());
    assertTrue(it.hasNext());
    assertEquals(1, it.nextIndex());
    assertEquals(Span.of(null, 9, 13), it.next());
    assertTrue(it.hasNext());
    assertEquals(2, it.nextIndex());
    assertEquals(Span.of(null, 9, 10), it.next());
    assertTrue(it.hasNext());
    assertEquals(3, it.nextIndex());
    assertEquals(Span.of(null, 6, 8), it.next());
    assertTrue(it.hasNext());
    assertEquals(4, it.nextIndex());
    assertEquals(Span.of(null, 6, 7), it.next());
    assertTrue(it.hasNext());
    assertEquals(5, it.nextIndex());
    assertEquals(Span.of(null, 2, 6), it.next());
    assertFalse(it.hasNext());
    assertThrows(NoSuchElementException.class, it::next);

    assertTrue(it.hasPrevious());
    assertEquals(5, it.previousIndex());
    assertEquals(Span.of(null, 2, 6), it.previous());

    assertTrue(it.hasPrevious());
    assertEquals(4, it.previousIndex());
    assertEquals(Span.of(null, 6, 7), it.previous());

    assertTrue(it.hasPrevious());
    assertEquals(3, it.previousIndex());
    assertEquals(Span.of(null, 6, 8), it.previous());

    assertTrue(it.hasPrevious());
    assertEquals(2, it.previousIndex());
    assertEquals(Span.of(null, 9, 10), it.previous());

    assertTrue(it.hasPrevious());
    assertEquals(1, it.previousIndex());
    assertEquals(Span.of(null, 9, 13), it.previous());

    assertTrue(it.hasPrevious());
    assertEquals(0, it.previousIndex());
    assertEquals(Span.of(null, 9, 13), it.previous());

    assertFalse(it.hasPrevious());
    assertThrows(NoSuchElementException.class, it::previous);
  }

  @Test
  void iterator() {
    Iterator<@NotNull Span> it = descending.iterator();
    assertTrue(it.hasNext());
    assertEquals(Span.of(null, 9, 13), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(null, 9, 13), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(null, 9, 10), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(null, 6, 8), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(null, 6, 7), it.next());
    assertTrue(it.hasNext());
    assertEquals(Span.of(null, 2, 6), it.next());
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

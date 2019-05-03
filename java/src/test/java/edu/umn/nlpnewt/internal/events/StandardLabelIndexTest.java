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
import edu.umn.nlpnewt.Label;
import edu.umn.nlpnewt.LabelIndex;
import edu.umn.nlpnewt.internal.events.Span;
import edu.umn.nlpnewt.internal.events.StandardLabelIndex;
import org.jetbrains.annotations.NotNull;
import org.junit.jupiter.api.Test;

import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class StandardLabelIndexTest {
  LabelIndex<Span> tested = new StandardLabelIndex<>(Arrays.asList(
      Span.of(0, 5),
      Span.of(0, 7),
      Span.of(2, 6),
      Span.of(6, 7),
      Span.of(6, 8),
      Span.of(9, 10),
      Span.of(9, 13),
      Span.of(9, 13)
  ));

  LabelIndex<?> empty = new StandardLabelIndex<>(Collections.emptyList());

  @Test
  void createSort() {
    StandardLabelIndex<Span> sorted = StandardLabelIndex.create(Arrays.asList(
        Span.of(9, 13),
        Span.of(0, 7),
        Span.of(6, 8),
        Span.of(6, 7),
        Span.of(9, 10),
        Span.of(9, 13),
        Span.of(0, 5),
        Span.of(2, 6)
    ));
    assertEquals(tested.asList(), sorted.asList());
  }

  @Test
  void isDistinct() {
    assertFalse(tested.isDistinct());
  }

  @Test
  void size() {
    assertEquals(8, tested.size());
  }

  @Test
  void covering() {
    LabelIndex<Span> covering = tested.covering(Span.of(2, 4));
    assertEquals(
        Arrays.asList(
            Span.of(0, 5), Span.of(0, 7), Span.of(2, 6)
        ),
        covering.asList()
    );
  }

  @Test
  void coveringEquals() {
    LabelIndex<Span> covering = tested.covering(Span.of(6, 8));
    assertEquals(Collections.singletonList(Span.of(6, 8)), covering.asList());
  }

  @Test
  void coveringEmpty() {
    LabelIndex<Span> covering = tested.covering(4, 10);
    assertEquals(0, covering.size());
  }

  @Test
  void emptyCovering() {
    LabelIndex<?> covering = empty.covering(4, 10);
    assertEquals(0, covering.size());
  }

  @Test
  void inside() {
    LabelIndex<Span> inside = tested.inside(1, 8);

    assertEquals(Arrays.asList(Span.of(2, 6), Span.of(6, 7), Span.of(6, 8)), inside.asList());
  }

  @Test
  void insideBefore() {
    LabelIndex<Span> inside = tested.inside(0, 3);
    assertEquals(0, inside.size());
  }

  @Test
  void insideAfter() {
    LabelIndex<Span> inside = tested.inside(Span.of(15, 20));
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
    StandardLabelIndex<Span> index = new StandardLabelIndex<>(spans);
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
    LabelIndex<Span> beginsInside = tested.beginningInside(Span.of(1, 10));
    assertEquals(Arrays.asList(
        Span.of(2, 6),
        Span.of(6, 7),
        Span.of(6, 8),
        Span.of(9, 10),
        Span.of(9, 13),
        Span.of(9, 13)),
        beginsInside.asList()
    );
  }

  @Test
  void beginsInsideEmpty() {
    LabelIndex<Span> beginsInside = tested.beginningInside(3, 5);
    assertEquals(Collections.emptyList(), beginsInside.asList());
  }

  @Test
  void emptyBeginsInside() {
    LabelIndex<?> beginsInside = empty.beginningInside(0, 5);
    assertEquals(Collections.emptyList(), beginsInside.asList());
  }

  @Test
  void ascending() {
    LabelIndex<Span> ascending = tested.ascending();
    assertSame(tested, ascending);
    assertEquals(tested.asList(), ascending.asList());
  }

  @Test
  void emptyAscending() {
    LabelIndex<?> ascending = empty.ascending();
    assertSame(empty, ascending);
    assertEquals(empty.asList(), ascending.asList());
  }

  @Test
  void descending() {
    LabelIndex<Span> descending = tested.descending();
    assertEquals(Arrays.asList(
        Span.of(9, 13),
        Span.of(9, 13),
        Span.of(9, 10),
        Span.of(6, 8),
        Span.of(6, 7),
        Span.of(2, 6),
        Span.of(0, 7),
        Span.of(0, 5)
    ), descending.asList());
  }

  @Test
  void emptyDescending() {
    LabelIndex<?> descending = empty.descending();
    assertEquals(Collections.emptyList(), descending.asList());
  }

  @Test
  void before() {
    LabelIndex<Span> before = tested.before(8);
    assertEquals(Arrays.asList(
        Span.of(0, 5),
        Span.of(0, 7),
        Span.of(2, 6),
        Span.of(6, 7),
        Span.of(6, 8)
    ), before.asList());
  }

  @Test
  void beforeStart() {
    LabelIndex<Span> before = tested.before(3);
    assertEquals(Collections.emptyList(), before.asList());
  }

  @Test
  void emptyBefore() {
    LabelIndex<?> before = empty.before(5);
    assertEquals(Collections.emptyList(), before.asList());
  }

  @Test
  void after() {
    LabelIndex<Span> after = tested.after(2);
    assertEquals(Arrays.asList(
        Span.of(2, 6),
        Span.of(6, 7),
        Span.of(6, 8),
        Span.of(9, 10),
        Span.of(9, 13),
        Span.of(9, 13)
    ), after.asList());
  }

  @Test
  void afterEnd() {
    LabelIndex<Span> after = tested.after(10);
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
    assertEquals(Span.of(0, 5), tested.first());
  }

  @Test
  void emptyLast() {
    assertNull(empty.last());
  }

  @Test
  void last() {
    assertEquals(Span.of(9, 13), tested.last());
  }

  @Test
  void atLocationMultiple() {
    Collection<@NotNull Span> atLocation = tested.atLocation(9, 13);
    assertEquals(Arrays.asList(
        Span.of(9, 13),
        Span.of(9, 13)
    ), atLocation);
  }

  @Test
  void atLocationOne() {
    Collection<@NotNull Span> atLocation = tested.atLocation(2, 6);
    assertEquals(Collections.singletonList(Span.of(2, 6)), atLocation);
  }

  @Test
  void atLocationDifferentLabel() {
    List<@NotNull Span> atLocation = tested.atLocation(GenericLabel.createSpan(2, 6));
    assertEquals(Collections.singletonList(Span.of(2, 6)), atLocation);
  }

  @Test
  void atLocationNone() {
    Collection<@NotNull Span> atLocation = tested.atLocation(0, 30);
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
    assertTrue(tested.contains(Span.of(2, 6)));
  }

  @Test
  void containsNotLabel() {
    assertFalse(tested.contains("this is a string"));
  }

  @Test
  void containsNull() {
    assertFalse(tested.contains(null));
  }

  @Test
  void containsFalse() {
    assertFalse(tested.contains(Span.of(0, 30)));
  }

  @Test
  void emptyContains() {
    assertFalse(empty.contains(Span.of(0, 0)));
  }

  @Test
  void containsSpanTrue() {
    assertTrue(tested.containsSpan(2, 6));
  }

  @Test
  void containsSpanFalse() {
    assertFalse(tested.containsSpan(0, 30));
  }

  @Test
  void asList() {
    assertEquals(Arrays.asList(
        Span.of(0, 5),
        Span.of(0, 7),
        Span.of(2, 6),
        Span.of(6, 7),
        Span.of(6, 8),
        Span.of(9, 10),
        Span.of(9, 13),
        Span.of(9, 13)
    ), tested.asList());
  }

  @Test
  void emptyAsList() {
    assertEquals(Collections.emptyList(), empty.asList());
  }

  @Test
  void asListIndexOf() {
    assertEquals(6, tested.asList().indexOf(Span.of(9, 13)));
  }

  @Test
  void asListIndexOfPushForward() {
    List<Label> labels = Arrays.asList(
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
        Span.of(3, 5)
    );
    StandardLabelIndex<Label> index = new StandardLabelIndex<>(labels);
    assertEquals(14, index.asList().indexOf(GenericLabel.newBuilder(3, 5).setProperty("foo", "bar").build()));
  }

  @Test
  void asListIndexOfNotFound() {
    List<Label> labels = Arrays.asList(
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
    );
    StandardLabelIndex<Label> index = new StandardLabelIndex<>(labels);
    assertEquals(-1, index.asList().indexOf(GenericLabel.newBuilder(3, 5).setProperty("foo", "bar").build()));

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
    StandardLabelIndex<Span> index = new StandardLabelIndex<>(spans);
    assertEquals(14, index.asList().indexOf(Span.of(3, 5)));
  }

  @Test
  void asListIndexOfNone() {
    assertEquals(-1, tested.asList().indexOf(Span.of(0, 30)));
  }

  @Test
  void asListIndexOfNull() {
    assertEquals(-1, tested.asList().indexOf(null));
  }

  @Test
  void asListIndexOfNotLabel() {
    assertEquals(-1, tested.asList().indexOf("blah"));
  }

  @Test
  void emptyAsListIndexOf() {
    assertEquals(-1, empty.asList().indexOf(Span.of(9, 13)));
  }

  @Test
  void asListLastIndexOf() {
    assertEquals(7, tested.asList().lastIndexOf(Span.of(9, 13)));
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
    StandardLabelIndex<Label> index = new StandardLabelIndex<>(spans);
    assertEquals(29, index.asList().lastIndexOf(Span.of(3, 5)));
  }

  @Test
  void asListLastIndexOfBackUp() {
    List<Label> labels = Arrays.asList(
        Span.of(3, 5),
        GenericLabel.newBuilder(3, 5).setProperty("foo", "bar").build(),
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
    );
    StandardLabelIndex<Label> index = new StandardLabelIndex<>(labels);
    assertEquals(1, index.asList().lastIndexOf(GenericLabel.newBuilder(3, 5).setProperty("foo", "bar").build()));
  }

  @Test
  void asListLastIndexOfNone() {
    assertEquals(-1, tested.asList().lastIndexOf(Span.of(0, 30)));
  }

  @Test
  void asListLastIndexOfNull() {
    assertEquals(-1, tested.asList().lastIndexOf(null));
  }

  @Test
  void asListLastIndexOfNotLabel() {
    assertEquals(-1, tested.asList().lastIndexOf("blah"));
  }

  @Test
  void asListLastIndexOfNotFound() {
    List<Label> labels = Arrays.asList(
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
    );
    StandardLabelIndex<Label> index = new StandardLabelIndex<>(labels);
    assertEquals(-1, index.asList().lastIndexOf(
        GenericLabel.newBuilder(3, 5).setProperty("foo", "bar").build()));
  }

  @Test
  void asListContains() {
    List<@NotNull Span> asList = tested.asList();
    assertTrue(asList.contains(Span.of(2, 6)));
  }

  @Test
  void asListContainsFalse() {
    List<@NotNull Span> asList = tested.asList();
    assertFalse(asList.contains(Span.of(0, 30)));
  }
}
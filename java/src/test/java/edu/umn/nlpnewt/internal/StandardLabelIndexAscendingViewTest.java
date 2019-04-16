package edu.umn.nlpnewt.internal;

import edu.umn.nlpnewt.GenericLabel;
import edu.umn.nlpnewt.Label;
import edu.umn.nlpnewt.LabelIndex;
import org.jetbrains.annotations.NotNull;
import org.junit.jupiter.api.Test;

import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.junit.jupiter.api.Assertions.assertFalse;

public class StandardLabelIndexAscendingViewTest {
  LabelIndex<Span> ascending = new StandardLabelIndex<>(Arrays.asList(
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
  )).inside(1, 15);

  LabelIndex<Span> empty = ascending.inside(0, 0);


  @Test
  void isDistinct() {
    assertFalse(ascending.isDistinct());
  }

  @Test
  void size() {
    assertEquals(6, ascending.size());
  }

  @Test
  void covering() {
    LabelIndex<Span> covering = ascending.covering(Span.of(2, 4));
    assertEquals(
        Collections.singletonList(Span.of(2, 6)),
        covering.asList()
    );
  }

  @Test
  void coveringEquals() {
    LabelIndex<Span> covering = ascending.covering(Span.of(6, 8));
    assertEquals(Collections.singletonList(Span.of(6, 8)), covering.asList());
  }

  @Test
  void coveringEmpty() {
    LabelIndex<Span> covering = ascending.covering(4, 10);
    assertEquals(0, covering.size());
  }

  @Test
  void emptyCovering() {
    LabelIndex<?> covering = ascending.covering(4, 10);
    assertEquals(0, covering.size());
  }

  @Test
  void inside() {
    LabelIndex<Span> inside = ascending.inside(3, 10);

    assertEquals(Arrays.asList(Span.of(6, 7), Span.of(6, 8), Span.of(9, 10)), inside.asList());
  }

  @Test
  void insideBefore() {
    LabelIndex<Span> inside = ascending.inside(0, 3);
    assertEquals(0, inside.size());
  }

  @Test
  void insideAfter() {
    LabelIndex<Span> inside = ascending.inside(Span.of(15, 20));
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
    LabelIndex<Span> index = new StandardLabelIndex<>(spans).inside(0, 10);
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
    LabelIndex<Span> beginsInside = ascending.beginsInside(Span.of(1, 10));
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
    LabelIndex<Span> beginsInside = ascending.beginsInside(3, 5);
    assertEquals(Collections.emptyList(), beginsInside.asList());
  }

  @Test
  void emptyBeginsInside() {
    LabelIndex<?> beginsInside = empty.beginsInside(0, 5);
    assertEquals(Collections.emptyList(), beginsInside.asList());
  }

  @Test
  void ascendingBegin() {
    LabelIndex<Span> ascendingStartIndex = ascending.ascendingStartIndex();
    assertSame(ascending, ascendingStartIndex);
  }

  @Test
  void emptyAscendingBegin() {
    LabelIndex<?> ascendingStartIndex = empty.ascendingStartIndex();
    assertSame(empty, ascendingStartIndex);
  }

  @Test
  void descendingBegin() {
    LabelIndex<Span> descendingStartIndex = ascending.descendingStartIndex();
    assertEquals(Arrays.asList(
        Span.of(9, 10),
        Span.of(9, 13),
        Span.of(9, 13),
        Span.of(6, 7),
        Span.of(6, 8),
        Span.of(2, 6)
    ), descendingStartIndex.asList());
  }

  @Test
  void emptyDescendingBegin() {
    LabelIndex<?> descendingStartIndex = empty.descendingStartIndex();
    assertEquals(empty.asList(), descendingStartIndex.asList());
  }

  @Test
  void ascendingEnd() {
    LabelIndex<Span> ascendingEndIndex = ascending.ascendingEndIndex();
    assertSame(ascending, ascendingEndIndex);
  }

  @Test
  void emptyAscendingEnd() {
    LabelIndex<?> ascendingEndIndex = empty.ascendingEndIndex();
    assertEquals(empty.asList(), ascendingEndIndex.asList());
  }

  @Test
  void descendingEnd() {
    LabelIndex<Span> descendingEndIndex = ascending.descendingEndIndex();
    assertEquals(Arrays.asList(
        Span.of(2, 6),
        Span.of(6, 8),
        Span.of(6, 7),
        Span.of(9, 13),
        Span.of(9, 13),
        Span.of(9, 10)
    ), descendingEndIndex.asList());
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
    LabelIndex<Span> newAscending = ascending.ascending();
    assertSame(ascending, newAscending);
    assertEquals(ascending.asList(), newAscending.asList());
  }

  @Test
  void emptyAscending() {
    LabelIndex<?> ascending = empty.ascending();
    assertSame(empty, ascending);
    assertEquals(empty.asList(), ascending.asList());
  }

  @Test
  void descending() {
    LabelIndex<Span> descending = ascending.descending();
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
    LabelIndex<Span> before = ascending.before(8);
    assertEquals(Arrays.asList(
        Span.of(2, 6),
        Span.of(6, 7),
        Span.of(6, 8)
    ), before.asList());
  }

  @Test
  void beforeStart() {
    LabelIndex<Span> before = ascending.before(3);
    assertEquals(Collections.emptyList(), before.asList());
  }

  @Test
  void emptyBefore() {
    LabelIndex<?> before = empty.before(5);
    assertEquals(Collections.emptyList(), before.asList());
  }

  @Test
  void after() {
    LabelIndex<Span> after = ascending.after(6);
    assertEquals(Arrays.asList(
        Span.of(6, 7),
        Span.of(6, 8),
        Span.of(9, 10),
        Span.of(9, 13),
        Span.of(9, 13)
    ), after.asList());
  }

  @Test
  void afterEnd() {
    LabelIndex<Span> after = ascending.after(10);
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
    assertEquals(Span.of(2, 6), ascending.first());
  }

  @Test
  void emptyLast() {
    assertNull(empty.last());
  }

  @Test
  void last() {
    assertEquals(Span.of(9, 13), ascending.last());
  }

  @Test
  void atLocationMultiple() {
    Collection<@NotNull Span> atLocation = ascending.atLocation(9, 13);
    assertEquals(Arrays.asList(
        Span.of(9, 13),
        Span.of(9, 13)
    ), atLocation);
  }

  @Test
  void atLocationOne() {
    Collection<@NotNull Span> atLocation = ascending.atLocation(2, 6);
    assertEquals(Collections.singletonList(Span.of(2, 6)), atLocation);
  }

  @Test
  void atLocationDifferentLabel() {
    List<@NotNull Span> atLocation = ascending.atLocation(GenericLabel.createSpan(2, 6));
    assertEquals(Collections.singletonList(Span.of(2, 6)), atLocation);
  }

  @Test
  void atLocationNone() {
    Collection<@NotNull Span> atLocation = ascending.atLocation(0, 30);
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
    assertTrue(ascending.contains(Span.of(2, 6)));
  }

  @Test
  void containsNotLabel() {
    assertFalse(ascending.contains("this is a string"));
  }

  @Test
  void containsNull() {
    assertFalse(ascending.contains(null));
  }

  @Test
  void containsFalse() {
    assertFalse(ascending.contains(Span.of(0, 30)));
  }

  @Test
  void emptyContains() {
    assertFalse(empty.contains(Span.of(0, 0)));
  }

  @Test
  void containsSpanTrue() {
    assertTrue(ascending.containsSpan(2, 6));
  }

  @Test
  void containsSpanFalse() {
    assertFalse(ascending.containsSpan(0, 30));
  }

  @Test
  void asList() {
    assertEquals(Arrays.asList(
        Span.of(2, 6),
        Span.of(6, 7),
        Span.of(6, 8),
        Span.of(9, 10),
        Span.of(9, 13),
        Span.of(9, 13)
    ), ascending.asList());
  }

  @Test
  void emptyAsList() {
    assertEquals(Collections.emptyList(), empty.asList());
  }

  @Test
  void asListIndexOf() {
    assertEquals(4, ascending.asList().indexOf(Span.of(9, 13)));
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
    LabelIndex<Span> index = new StandardLabelIndex<>(spans).inside(0, 20);
    assertEquals(14, index.asList().indexOf(Span.of(3, 5)));
  }

  @Test
  void asListIndexOfNone() {
    assertEquals(-1, ascending.asList().indexOf(Span.of(0, 30)));
  }

  @Test
  void asListIndexOfNull() {
    assertEquals(-1, ascending.asList().indexOf(null));
  }

  @Test
  void asListIndexOfNotLabel() {
    assertEquals(-1, ascending.asList().indexOf("blah"));
  }

  @Test
  void emptyAsListIndexOf() {
    assertEquals(-1, empty.asList().indexOf(Span.of(9, 13)));
  }

  @Test
  void asListLastIndexOf() {
    assertEquals(5, ascending.asList().lastIndexOf(Span.of(9, 13)));
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
    LabelIndex<Label> index = new StandardLabelIndex<>(spans).inside(0, 20);
    assertEquals(29, index.asList().lastIndexOf(Span.of(3, 5)));
  }

  @Test
  void asListLastIndexOfNone() {
    assertEquals(-1, ascending.asList().lastIndexOf(Span.of(0, 30)));
  }

  @Test
  void asListLastIndexOfNull() {
    assertEquals(-1, ascending.asList().lastIndexOf(null));
  }

  @Test
  void asListLastIndexOfNotLabel() {
    assertEquals(-1, ascending.asList().lastIndexOf("blah"));
  }

  @Test
  void asListContains() {
    List<@NotNull Span> asList = ascending.asList();
    assertTrue(asList.contains(Span.of(2, 6)));
  }

  @Test
  void asListContainsFalse() {
    List<@NotNull Span> asList = ascending.asList();
    assertFalse(asList.contains(Span.of(0, 30)));
  }
}

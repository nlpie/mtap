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

import java.util.Collection;
import java.util.List;

/**
 * An immutable collection of labels ordered by their location in text. By default sorts by
 * ascending {@link Label#getStartIndex()} and then by ascending {@link Label#getEndIndex()}.
 *
 * @param <L> The label type.
 */
public interface LabelIndex<L extends Label> extends Collection<@NotNull L> {
  /**
   * Returns whether or not the index is distinct.
   * <p>
   * Index distinctness is based on whether the labels in the index can overlap or cannot overlap.
   * In the case of distinct, non-overlapping labels optimization can be made to the
   * process of searching for labels, as well as iteration over and size computation of sub-indices.
   *
   * @return Returns {@code true} if the index is distinct, {@code false} if the index is not
   * distinct.
   */
  boolean isDistinct();

  // -----------
  //  Filtering
  // -----------

  /**
   * The collection of labels that contain the text that starts at {@code startIndex} and ends at
   * {@code endIndex}.
   *
   * @param startIndex The start index inclusive for the span.
   * @param endIndex   The end index exclusive for the span.
   *
   * @return A view of the labels in this index that contain that span.
   */
  @NotNull LabelIndex<L> covering(int startIndex, int endIndex);

  /**
   * The collection of labels that contain the span of text covered by {@code label}.
   *
   * @param label A label that specifies a span of text.
   *
   * @return A view of the labels in this index that contain that span.
   */
  @NotNull LabelIndex<L> covering(@NotNull Label label);

  /**
   * The collection of labels that are entirely contained in the span of text that starts at
   * {@code startIndex} and ends at {@code endIndex}.
   *
   * @param startIndex The start index of the span of text.
   * @param endIndex   The end index of the span of text.
   *
   * @return A view of the labels in this index that are inside that span.
   */
  @NotNull LabelIndex<L> inside(int startIndex, int endIndex);

  /**
   * The collection of labels that are entirely contained in the span of text covered by
   * {@code label}.
   *
   * @param label A label that specifies a span of text.
   *
   * @return A view of the labels in this index that are inside that span.
   */
  @NotNull LabelIndex<L> inside(@NotNull Label label);

  /**
   * A Label index of all labels that begin inside the span of text that starts at
   * {@code startIndex} and ends at {@code endIndex}.
   *
   * @param startIndex The start index of the span of text.
   * @param endIndex   The end index of the span of text.
   *
   * @return A view of the labels in this index that begin inside that span.
   */
  @NotNull LabelIndex<L> beginningInside(int startIndex, int endIndex);

  /**
   * A Label index of all labels that begin inside the span of text covered by {@code label}.
   *
   * @param label A label that specifies a span of text.
   *
   * @return A view of the labels in this index that begin inside that span.
   */
  @NotNull LabelIndex<L> beginningInside(@NotNull Label label);

  /**
   * A label index of all labels that begin before {@code index}.
   *
   * @param index An index that indicates the end of which labels should be included.
   *
   * @return A view of the labels in this index that come before the index.
   */
  default @NotNull LabelIndex<L> before(int index) {
    return inside(0, index);
  }

  /**
   * A label index of all the labels that occur before {@code label} starts.
   *
   * @param label A label that indicates the end of which labels should be included.
   *
   * @return A view of the labels in this index that come before the start of the label.
   */
  default @NotNull LabelIndex<L> before(@NotNull Label label) {
    return before(label.getStartIndex());
  }

  /**
   * A label index of all labels that begin after {@code index}.
   *
   * @param index An index that indicates the start of which labels should be included.
   *
   * @return A view of the labels in this index that start after the end of the index.
   */
  default @NotNull LabelIndex<L> after(int index) {
    return inside(index, Integer.MAX_VALUE);
  }

  /**
   * A label index of all labels that begin after {@code label} ends.
   *
   * @param label A label whose end indicates the start of all labels to include.
   *
   * @return A view of the labels in this index that come after the end of the label.
   */
  default @NotNull LabelIndex<L> after(@NotNull Label label) {
    return after(label.getEndIndex());
  }

  // ----------
  //  Ordering
  // ----------

  /**
   * This label index sorted according to ascending start and end index.
   *
   * @return A sorted view of this label index.
   */
  @NotNull LabelIndex<L> ascending();

  /**
   * This label index sorted according to descending start and end index.
   *
   * @return A sorted view of this label index.
   */
  @NotNull LabelIndex<L> descending();


  // ------------------------
  //  Ordering and filtering
  // ------------------------

  /**
   * A label index consisting of all the labels sorted ascending forward from {@code index}.
   *
   * @param index The start of the labels to include.
   *
   * @return A sorted view of this label index forward from the index.
   */
  default @NotNull LabelIndex<L> forwardFrom(int index) {
    return after(index).ascending();
  }

  /**
   * A label index consisting of all the labels sorted ascending forward from {@code label}.
   *
   * @param label A label whose end indicates the start of labels to include.
   *
   * @return A sorted view of this label index forward from the label.
   */
  default @NotNull LabelIndex<L> forwardFrom(@NotNull Label label) {
    return after(label).ascending();
  }

  /**
   * A label consisting of all the labels sorted descending backward from {@code index}.
   *
   * @param index The upper bound of labels to include.
   *
   * @return A sorted view of this label index backward from the index.
   */
  default @NotNull LabelIndex<L> backwardFrom(int index) {
    return before(index).descending();
  }

  /**
   * A label consisting of all the labels sorted descending backward from {@code label}.
   *
   * @param label A label whose start indicates the upper bound of labels to include.
   *
   * @return A sorted view of this label index backward from the label.
   */
  default @NotNull LabelIndex<L> backwardFrom(@NotNull Label label) {
    return before(label).descending();
  }

  // ---------
  //  Queries
  // ---------

  /**
   * The first label in this label index according to current sort order, if it exists or
   * else {@code null}.
   *
   * @return A label object or {@code null}.
   */
  @Nullable L first();

  /**
   * The last label in this label index according to current sort order, if it exists, or else
   * {@code null}.
   *
   * @return A label object or {@code null}.
   */
  @Nullable L last();

  /**
   * Whether this label index contains a label that starts at {@code startIndex} and ends at
   * {@code endIndex}.
   *
   * @param startIndex The start index of the span to search for.
   * @param endIndex   The end index of the span to search for.
   *
   * @return {@code true} if found, {@code false} otherwise.
   */
  boolean containsSpan(int startIndex, int endIndex);

  /**
   * Whether this label index contains a label with a span that matches that of {@code label}.
   *
   * @param label The label that specifies the span.
   *
   * @return {@code true} if found, {@code false} otherwise.
   */
  boolean containsSpan(@NotNull Label label);

  /**
   * The collection of all labels in this index that start at {@code startIndex} and end at
   * {@code endIndex}.
   *
   * @param startIndex The start index of the span to search for.
   * @param endIndex   The end index of the span to search for.
   *
   * @return A list, maybe empty, of all the labels with that span.
   */
  @NotNull List<@NotNull L> atLocation(int startIndex, int endIndex);

  /**
   * The collection of all labels in this index that match the span of {@code label}.
   *
   * @param label The label that specifies the span to look for.
   *
   * @return A list, maybe empty, of all the labels with that span.
   */
  @NotNull List<@NotNull L> atLocation(@NotNull Label label);

  /**
   * The first label added to the label index that starts at {@code startIndex} and ends at
   * {@code endIndex}.
   *
   * @param startIndex The start index of the span to search for.
   * @param endIndex   The end index of the span to search for.
   *
   * @return The first label occurring at that span, or {@code null} if none exist.
   */
  @Nullable L firstAtLocation(int startIndex, int endIndex);

  /**
   * The first label added to the label index that covers the same span of text as {@code label}.
   *
   * @param label The label that specifies the span to look for.
   *
   * @return The first label occurring at that span, or {@code null} if none exist.
   */
  @Nullable L firstAtLocation(@NotNull Label label);

  // -------
  //  Views
  // -------

  /**
   * An unmodifiable list view of this label index.
   *
   * @return View of all the labels in this label index.
   */
  @NotNull List<@NotNull L> asList();
}

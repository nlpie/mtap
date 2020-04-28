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

import java.util.Set;

/**
 * An interface for a span of text that has been determined to have some specific meaning or
 * function.
 */
public interface Label {

  /**
   * The document that the label appears on.
   *
   * @return A document object or {@code null}.
   */
  @Nullable Document getDocument();

  /**
   * Sets the document that the label appears on.
   *
   * @param document The Document object that this label appears on.
   */
  void setDocument(@Nullable Document document);

  /**
   * The name of the label index this label appears in.
   *
   * @return A string or {@code null}.
   */
  @Nullable String getLabelIndexName();

  /**
   * Sets the name of the label index.
   *
   * @param labelIndexName String identifier name for the label index.
   */
  void setLabelIndexName(@Nullable String labelIndexName);

  /**
   * Returns the label-index unique identifier / index of the label.
   *
   * @return An integer object or {@code null}.
   */
  @Nullable Integer getIdentifier();

  /**
   * Sets the unique identifier for the label.
   *
   * @param identifier The unique identifier / index of the label.
   */
  void setIdentifier(@Nullable Integer identifier);

  /**
   * The index of the first character included in the label.
   *
   * @return Integer index.
   */
  int getStartIndex();

  /**
   * Exclusive end index. The index of the first character not included after the label.
   *
   * @return Integer index.
   */
  int getEndIndex();

  /**
   * Retrieves the portion of the document text covered by this label.
   *
   * @return A string of the document text covered by the label.
   * @throws IllegalStateException If this label doesn't have an associated document it will fail.
   */
  default @NotNull String getText() {
    Document document = getDocument();
    if (document == null) {
      throw new IllegalStateException("Attempting to retrieve text from label without associated document.");
    }
    return document.getText().substring(getStartIndex(), getEndIndex());
  }

  /**
   * Returns the length (in number of characters) of the Label.
   *
   * @return Integer length of the label.
   */
  default int length() {
    return getEndIndex() - getStartIndex();
  }

  /**
   * Whether the span of text covered by this label is the same as the span of text covered by the
   * other label.
   *
   * @param other The other label to check for location equivalence.
   * @return {@code true} if the other label's location equals the location of this label,
   * {@code false} otherwise.
   */
  default boolean locationEquals(@NotNull Label other) {
    return getStartIndex() == other.getStartIndex() && getEndIndex() == other.getEndIndex();
  }

  /**
   * Whether the span of text covered by this label includes the span of text starting at
   * {@code startIndex} and ending at {@code endIndex}.
   *
   * @param startIndex The start index of the text.
   * @param endIndex   The end index of the text.
   * @return {@code true} if the span is covered by this label, {@code false} otherwise.
   */
  default boolean covers(int startIndex, int endIndex) {
    return getStartIndex() <= startIndex && endIndex <= getEndIndex();
  }

  /**
   * Whether the span of text covered by this label includes the span of text covered by the
   * other label.
   *
   * @param other The other label to check.
   * @return {@code true} if the other label's location is inside the location of this label,
   * {@code false} otherwise.
   */
  default boolean covers(@NotNull Label other) {
    return covers(other.getStartIndex(), other.getEndIndex());
  }

  /**
   * Whether this label is inside the span starting with {@code startIndex} and ending with
   * {@code endIndex}.
   *
   * @param startIndex The start index inclusive of the span.
   * @param endIndex   The end index exclusive of the span.
   * @return {@code true} if this label is inside the span.
   */
  default boolean isInside(int startIndex, int endIndex) {
    return startIndex <= getStartIndex() && getEndIndex() <= endIndex;
  }

  /**
   * Compares this label to another label by their locations, i.e. first by start index then by
   * end index.
   *
   * @param other The other label.
   * @return Result of two natural order comparisons, first of the start indices, then if start
   * indices are the same of the end indices.
   */
  default int compareLocation(@NotNull Label other) {
    int compare = Integer.compare(getStartIndex(), other.getStartIndex());
    if (compare != 0) return compare;
    return Integer.compare(getEndIndex(), other.getEndIndex());
  }

  /**
   * Compares this label to another label by their start indices.
   *
   * @param other The other label.
   * @return Natural ordering comparison value.
   */
  default int compareStart(@NotNull Label other) {
    return Integer.compare(getStartIndex(), other.getStartIndex());
  }

  /**
   * Used to add any memory address identifiers for labels that this label references to a list
   * to wait on before uploading this label.
   *
   * @param referenceIds The collection of references.
   */
  default void  collectFloatingReferences(Set<Integer> referenceIds) {

  }
}

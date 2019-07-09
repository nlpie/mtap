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

/**
 * An interface for a span of text that has been determined to have some specific meaning or
 * function.
 */
public interface Label {

  /**
   * A precondition check that checks whether the indices are valid for a label. Can be used by
   * implementing classes for validation of labels.
   *
   * @param startIndex The start index of the label.
   * @param endIndex   The end index of the label.
   */
  static void checkIndexRange(int startIndex, int endIndex) {
    if (endIndex < startIndex) {
      throw new IllegalArgumentException("end index: " + endIndex + " is less than start index: " + startIndex);
    }
    if (startIndex < 0) {
      throw new IllegalArgumentException("start index: " + startIndex + " is less than 0. end index: " + endIndex);
    }
  }

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
   * Whether the span of text covered by this label is the same as the span of text covered by the
   * other label.
   *
   * @param other The other label to check for location equivalence.
   *
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
   *
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
   * @param endIndex The end index exclusive of the span.
   * @return {@code true} if this label is inside the span.
   */
  default boolean isInside(int startIndex, int endIndex) {
    return startIndex <= getStartIndex() && getEndIndex() <= endIndex;
  }

  /**
   * Returns the text that is covered by the label from {@code string}.
   *
   * @param string The string to retrieve covered text.
   *
   * @return A {@link CharSequence} view of the covered text in the string.
   */
  default @NotNull CharSequence coveredText(@NotNull String string) {
    return string.subSequence(getStartIndex(), getEndIndex());
  }

  /**
   * Returns the document text that is covered by the label from {@code document}.
   *
   * @param document The document to retrieve covered text.
   *
   * @return A {@link CharSequence} view of the covered text in the string.
   */
  default @NotNull CharSequence coveredText(@NotNull Document document) {
    return coveredText(document.getText());
  }

  default int compareLocation(@NotNull Label other) {
    int compare = Integer.compare(getStartIndex(), other.getStartIndex());
    if (compare != 0) return compare;
    return Integer.compare(getEndIndex(), other.getEndIndex());
  }


  default int compareStart(@NotNull Label other) {
    return Integer.compare(getStartIndex(), other.getStartIndex());
  }
}

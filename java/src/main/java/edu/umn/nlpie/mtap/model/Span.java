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

import edu.umn.nlpie.mtap.Internal;
import org.jetbrains.annotations.Nullable;

import java.util.Objects;

@Internal
final class Span implements Label {

  private final int startIndex;
  private final int endIndex;

  private @Nullable Document document;

  private Span(@Nullable Document document, int startIndex, int endIndex) {
    this.document = document;
    this.startIndex = startIndex;
    this.endIndex = endIndex;
  }

  static Span of(@Nullable Document document, int startIndex, int endIndex) {
    return new Span(document, startIndex, endIndex);
  }

  static Span of(@Nullable Document document, int index) {
    return new Span(document, index, index);
  }

  @Override
  public @Nullable Document getDocument() {
    return document;
  }

  @Override
  public void setDocument(@Nullable Document document) {
    this.document = document;
  }

  @Override
  public @Nullable String getLabelIndexName() {
    throw new UnsupportedOperationException();
  }

  @Override
  public void setLabelIndexName(@Nullable String labelIndexName) {
    throw new UnsupportedOperationException();
  }

  @Override
  public @Nullable Integer getIdentifier() {
    throw new UnsupportedOperationException();
  }

  @Override
  public void setIdentifier(@Nullable Integer identifier) {
    throw new UnsupportedOperationException();
  }

  @Override
  public int getStartIndex() {
    return startIndex;
  }

  @Override
  public int getEndIndex() {
    return endIndex;
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) return true;
    if (o == null || getClass() != o.getClass()) return false;
    Span span = (Span) o;
    return startIndex == span.startIndex &&
        endIndex == span.endIndex;
  }

  @Override
  public int hashCode() {
    return Objects.hash(startIndex, endIndex);
  }

  @Override
  public String toString() {
    return "Span{" +
        "startIndex=" + startIndex +
        ", endIndex=" + endIndex +
        '}';
  }
}

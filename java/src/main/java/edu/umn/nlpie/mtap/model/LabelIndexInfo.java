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

import java.util.Objects;

/**
 * Information about a label index on a document.
 */
public final class LabelIndexInfo {
  /**
   * The type of label index.
   */
  public enum LabelIndexType {
    /**
     * Not set or not known.
     */
    UNKNOWN,
    /**
     * JSON / generic label index.
     */
    GENERIC,
    /**
     * Other / custom protobuf index.
     */
    CUSTOM
  }

  private final String indexName;

  private final LabelIndexType type;

  /**
   * Creates a new object containing information about a label index.
   *
   * @param indexName The index name of the LabeIndex.
   * @param type The type of the label index.
   */
  public LabelIndexInfo(@NotNull String indexName, @NotNull LabelIndexType type) {
    this.indexName = Objects.requireNonNull(indexName);
    this.type = Objects.requireNonNull(type);
  }

  /**
   * The name of the label index.
   *
   * @return String label index name
   */
  public @NotNull String getIndexName() {
    return indexName;
  }

  /**
   * The type of the label index.
   *
   * @return The type of labels.
   */
  public @NotNull LabelIndexType getType() {
    return type;
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) return true;
    if (o == null || getClass() != o.getClass()) return false;
    LabelIndexInfo that = (LabelIndexInfo) o;
    return indexName.equals(that.indexName) &&
        type == that.type;
  }

  @Override
  public int hashCode() {
    return Objects.hash(indexName, type);
  }

  @Override
  public String toString() {
    return "LabelIndexInfo{" +
        "indexName='" + indexName + '\'' +
        ", type=" + type +
        '}';
  }
}

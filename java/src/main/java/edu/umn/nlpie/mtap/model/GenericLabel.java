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

import edu.umn.nlpie.mtap.common.AbstractJsonObject;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.Map;

/**
 * A generalized, dynamic label on text which can contain arbitrary key-value items.
 * <p>
 * {@inheritDoc}
 * <p>
 * This class can be subclassed for convenience, for example:
 * <pre>
 *   {@code
 *   public class PosTag extends GenericLabel {
 *     private PosTag(JsonObject jsonObject) {
 *       super(jsonObject);
 *     }
 *
 *     public String getTag() {
 *       return getStringValue("tag");
 *     }
 *
 *     public static PosTag create(int startIndex, int endIndex, String tag) {
 *       GenericLabel label = GenericLabel.newBuilder(startIndex, endIndex)
 *           .setProperty("tag", tag)
 *           .build();
 *       return new PosTag(label);
 *     }
 *   }
 *   }
 * </pre>
 */
public class GenericLabel extends AbstractJsonObject implements Label {

  /**
   * Reserved property key for {@link #getStartIndex()}.
   */
  public static final String START_INDEX_KEY = "start_index";

  /**
   * Reserved property key for {@link #getEndIndex()}.
   */
  public static final String END_INDEX_KEY = "end_index";

  private GenericLabel(Map<@NotNull String, @Nullable Object> backingMap) {
    super(backingMap);
  }

  /**
   * Creates a generic label by copying {@code jsonObject}.
   *
   * @param abstractJsonObject The json object to copy.
   */
  public GenericLabel(AbstractJsonObject abstractJsonObject) {
    super(abstractJsonObject);
  }

  /**
   * Creates a generic label that indicates a span of text.
   *
   * @param startIndex The start index of the span.
   * @param endIndex   The exclusive end index.
   * @return Immutable finalized generic label that indicates the span.
   */
  public static GenericLabel createSpan(int startIndex, int endIndex) {
    return new Builder(startIndex, endIndex).build();
  }

  /**
   * Creates a Builder that can be used to create a generic label.
   *
   * @param startIndex The start index of the label.
   * @param endIndex   The end index of the label.
   * @return Builder object that can be used to add other properties to the label.
   */
  public static Builder withSpan(int startIndex, int endIndex) {
    return new Builder(startIndex, endIndex);
  }

  /**
   * Creates a Builder that can be used to create a generic label from the span of another label.
   *
   * @param label The label to take a start index and end index from.
   * @return Builder object that can be used to add other properties to the label.
   */
  public static Builder withSpan(Label label) {
    return new Builder(label.getStartIndex(), label.getEndIndex());
  }

  /**
   * A precondition check that checks whether the indices are valid for a label. Can be used by
   * implementing classes for validation of labels.
   *
   * @param startIndex The start index of the label.
   * @param endIndex   The end index of the label.
   */
  public static void checkIndexRange(int startIndex, int endIndex) {
    if (endIndex < startIndex) {
      throw new IllegalArgumentException("end index: " + endIndex + " is less than start index: " + startIndex);
    }
    if (startIndex < 0) {
      throw new IllegalArgumentException("start index: " + startIndex + " is less than 0. end index: " + endIndex);
    }
  }

  @Override
  public int getStartIndex() {
    return getNumberValue(START_INDEX_KEY).intValue();
  }

  @Override
  public int getEndIndex() {
    return getNumberValue(END_INDEX_KEY).intValue();
  }

  /**
   * A newBuilder for generic label objects. Provides all the functionality of the json object newBuilder.
   */
  public static class Builder extends AbstractJsonObject.AbstractBuilder<Builder, GenericLabel> {

    private final int startIndex;

    private final int endIndex;

    /**
     * Default constructor. The {@code startIndex} and {@code endIndex} are required properties
     * of generic labels.
     *
     * @param startIndex The inclusive start index of the label.
     * @param endIndex   The exclusive end index of the label.
     */
    public Builder(int startIndex, int endIndex) {
      this.startIndex = startIndex;
      this.endIndex = endIndex;
    }

    /**
     * Builds a generic label from the properties that have been added to this newBuilder.
     *
     * @return Immutable finalized generic label that contains properties that have been added to
     * this newBuilder.
     */
    @Override
    public GenericLabel build() {
      checkIndexRange(startIndex, endIndex);
      setProperty(START_INDEX_KEY, startIndex);
      setProperty(END_INDEX_KEY, endIndex);
      return new GenericLabel(backingMap);
    }
  }
}

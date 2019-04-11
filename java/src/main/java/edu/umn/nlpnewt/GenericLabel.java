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
package edu.umn.nlpnewt;

import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.Map;

/**
 * A generalized, dynamic label on text which can contain arbitrary key-value items. Convention is
 * to use snake_case key identifiers.
 * <p>
 * This class can be subclassed for convenience:
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
 *       GenericLabel label = GenericLabel.builder(startIndex, endIndex)
 *           .setProperty("tag", tag)
 *           .build();
 *       return new PosTag(label);
 *     }
 *   }
 *   }
 * </pre>
 */
public class GenericLabel extends JsonObject implements Label {

  public static final String START_INDEX_KEY = "start_index";

  public static final String END_INDEX_KEY = "end_index";

  protected GenericLabel(Map<@NotNull String, @Nullable Object> backingMap) {
    super(backingMap);
  }

  public GenericLabel(JsonObject jsonObject) {
    super(jsonObject);
  }

  @Override
  public int getStartIndex() {
    return getNumberValue(START_INDEX_KEY).intValue();
  }

  @Override
  public int getEndIndex() {
    return getNumberValue(END_INDEX_KEY).intValue();
  }

  public static GenericLabel create(int startIndex, int endIndex) {
    return new Builder(startIndex, endIndex).build();
  }

  public static Builder builder(int startIndex, int endIndex) {
    return new Builder(startIndex, endIndex);
  }

  public static class Builder extends JsonObject.AbstractBuilder<Builder, GenericLabel> {
    private final int startIndex;
    private final int endIndex;

    public Builder(int startIndex, int endIndex) {
      this.startIndex = startIndex;
      this.endIndex = endIndex;
    }

    public GenericLabel build() {
      Label.checkIndexRange(startIndex, endIndex);
      setProperty(START_INDEX_KEY, startIndex);
      setProperty(END_INDEX_KEY, endIndex);
      return new GenericLabel(backingMap);
    }
  }
}

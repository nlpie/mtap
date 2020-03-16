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
import edu.umn.nlpie.mtap.common.JsonObject;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.*;

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
  private static final List<String> RESERVED_FIELDS = Arrays.asList(
      "document",
      "location",
      "text",
      "identifier",
      "start_index",
      "end_index",
      "label_index_name",
      "fields",
      "reference_field_ids",
      "reference_cache"
  );

  private final Map<@NotNull String, Object> referenceCache;

  private final JsonObject referenceFieldIds;

  private final int startIndex;

  private final int endIndex;

  private @Nullable Document document;
  private @Nullable String labelIndexName;
  private @Nullable Integer identifier;

  private GenericLabel(
      Map<@NotNull String, @Nullable Object> backingMap,
      Map<@NotNull String, @NotNull Object> referenceCache,
      @Nullable JsonObject referenceFieldIds,
      int startIndex,
      int endIndex
  ) {
    super(backingMap);
    for (String key : backingMap.keySet()) {
      if (RESERVED_FIELDS.contains(key)) {
        throw new IllegalStateException("Field key name '" + key + "' is reserved.");
      }
    }
    this.referenceCache = referenceCache;
    this.referenceFieldIds = referenceFieldIds;
    this.startIndex = startIndex;
    this.endIndex = endIndex;
  }

  /**
   * Creates a generic label by copying {@code jsonObject}.
   *
   * @param abstractJsonObject The json object to copy.
   */
  public GenericLabel(@NotNull AbstractJsonObject abstractJsonObject,
                      Map<@NotNull String, @NotNull Object> referenceCache,
                      @Nullable JsonObject referenceFieldIds,
                      int startIndex,
                      int endIndex) {
    super(abstractJsonObject);
    for (String key : abstractJsonObject.keySet()) {
      if (RESERVED_FIELDS.contains(key)) {
        throw new IllegalStateException("Field key name '" + key + "' is reserved.");
      }
    }
    this.referenceCache = referenceCache;
    this.referenceFieldIds = referenceFieldIds;
    this.startIndex = startIndex;
    this.endIndex = endIndex;
  }

  @Override
  public int getStartIndex() {
    return startIndex;
  }

  @Override
  public int getEndIndex() {
    return endIndex;
  }

  @Nullable
  @Override
  public Document getDocument() {
    return document;
  }

  public void setDocument(@Nullable Document document) {
    this.document = document;
  }

  @Nullable
  @Override
  public String getLabelIndexName() {
    return labelIndexName;
  }

  public void setLabelIndexName(@Nullable String labelIndexName) {
    this.labelIndexName = labelIndexName;
  }

  @Nullable
  @Override
  public Integer getIdentifier() {
    return identifier;
  }

  public void setIdentifier(@Nullable Integer identifier) {
    this.identifier = identifier;
  }

  public <L extends Label> L getLabelValue(String key) {
    // TODO: implement this.
    return null;
  }

  public <L extends Label> List<L> getLabelListValue(String key) {
    // TODO: implement this.
    return null;
  }

  public <L extends Label> Map<String, L> getLabelMapValue(String key) {
    // TODO: implement this.
    return null;
  }

  public Object getReferentialValue(String key) {
    // TODO: implement this.
    return null;
  }

  public JsonObject getReferenceFieldIds() {
    return referenceFieldIds;
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

  public static void checkReferenceValues(Object value, Deque<Object> parents) {
    if (value instanceof Map) {
      checkForReferenceCycle(value, parents);
      Map<?, ?> map = (Map<?, ?>) value;
      parents.push(value);
      for (Map.Entry<?, ?> entry : map.entrySet()) {
        Object key = entry.getKey();
        Object val = entry.getValue();
        if (!(key instanceof String)) {
          throw new IllegalArgumentException("Nested maps must have keys of String type.");
        }
        checkReferenceValues(val, parents);
      }
      parents.pop();
    } else if (value instanceof List) {
      checkForReferenceCycle(value, parents);
      List<?> list = (List<?>) value;
      parents.push(list);
      for (Object o : list) {
        checkReferenceValues(o, parents);
      }
      parents.pop();
    } else if (!(value instanceof Label)) {
      throw new IllegalArgumentException("Value type cannot be represented in json: \""
          + value.getClass().getName() + "\". Valid types are Java primitive objects, " +
          " lists of objects of valid types, and maps of strings to objects of valid types");
    }
  }

  /**
   * A newBuilder for generic label objects. Provides all the functionality of the json object newBuilder.
   */
  public static class Builder extends AbstractJsonObject.AbstractBuilder<Builder, GenericLabel> {

    protected final Map<@NotNull String, Object> referenceCache = new HashMap<>();

    private final int startIndex;

    private final int endIndex;

    private @Nullable JsonObject referenceFieldIds;

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

    public Builder withReference(String fieldName, Object object) {
      checkReferenceValues(object, new LinkedList<>());
      this.referenceCache.put(fieldName, object);
      return this;
    }

    public Builder withReferences(Map<@NotNull String, Object> references) {
      for (Entry<String, ?> entry : references.entrySet()) {
        checkReferenceValues(entry.getValue(), new LinkedList<>());
      }
      this.referenceCache.putAll(references);
      return this;
    }

    public Builder withReferenceFieldIds(JsonObject referenceFieldIds) {
      this.referenceFieldIds = referenceFieldIds;
      return this;
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
      return new GenericLabel(backingMap, referenceCache, referenceFieldIds, startIndex, endIndex);
    }
  }
}

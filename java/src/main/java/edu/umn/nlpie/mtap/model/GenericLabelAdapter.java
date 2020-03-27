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
import edu.umn.nlpie.mtap.api.v1.EventsOuterClass;
import edu.umn.nlpie.mtap.common.JsonObjectImpl;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static edu.umn.nlpie.mtap.api.v1.EventsOuterClass.*;

@Internal
final class GenericLabelAdapter implements ProtoLabelAdapter<GenericLabel> {

  /**
   * The adapter that is used to map distinct labels to and from the protobuf serialization format.
   */
  public static final ProtoLabelAdapter<GenericLabel> DISTINCT_ADAPTER = new GenericLabelAdapter(true);

  /**
   * The adapter that is used to map standard/non-distinct labels to and from the protobuf
   * serialization format.
   */
  public static final ProtoLabelAdapter<GenericLabel> NOT_DISTINCT_ADAPTER = new GenericLabelAdapter(false);

  private final boolean isDistinct;

  GenericLabelAdapter(boolean isDistinct) {
    this.isDistinct = isDistinct;
  }

  @NotNull
  @Override
  public Class<GenericLabel> getLabelType() {
    return GenericLabel.class;
  }

  @Override
  public @NotNull LabelIndex<GenericLabel> createIndexFromResponse(@NotNull GetLabelsResponse response, @Nullable Document document) {
    GenericLabels genericLabels = response.getGenericLabels();
    boolean isDistinct = genericLabels.getIsDistinct();

    List<GenericLabel> labels = new ArrayList<>();
    for (EventsOuterClass.GenericLabel genericLabel : genericLabels.getLabelsList()) {
      JsonObjectImpl.Builder fieldsBuilder = new JsonObjectImpl.Builder();
      fieldsBuilder.copyStruct(genericLabel.getFields());
      JsonObjectImpl.Builder referenceFieldIdsBuilder = new JsonObjectImpl.Builder();
      referenceFieldIdsBuilder.copyStruct(genericLabel.getReferenceIds());
      labels.add(new GenericLabel(fieldsBuilder.build(), new HashMap<>(),
          referenceFieldIdsBuilder.build(),
          genericLabel.getStartIndex(), genericLabel.getEndIndex()));
    }

    return isDistinct ? new DistinctLabelIndex<>(labels) : new StandardLabelIndex<>(labels);
  }

  @Override
  public LabelIndex<GenericLabel> createLabelIndex(List<@NotNull GenericLabel> labels) {
    if (isDistinct) {
      return new DistinctLabelIndex<>(labels);
    } else {
      return new StandardLabelIndex<>(labels);
    }
  }

  @Override
  public void addToMessage(@NotNull List<@NotNull GenericLabel> labels,
                           @NotNull AddLabelsRequest.Builder builder) {
    GenericLabels.Builder genericLabelsBuilder = builder.getGenericLabelsBuilder();
    genericLabelsBuilder.setIsDistinct(isDistinct);
    storeReferences(labels);
    for (GenericLabel label : labels) {
      EventsOuterClass.GenericLabel.Builder genericLabelBuilder = genericLabelsBuilder.addLabelsBuilder();
      label.copyToStruct(genericLabelBuilder.getFieldsBuilder());
      assert label.getReferenceFieldIds() != null;
      label.getReferenceFieldIds().copyToStruct(genericLabelBuilder.getReferenceIdsBuilder());
      genericLabelBuilder.setStartIndex(label.getStartIndex());
      genericLabelBuilder.setEndIndex(label.getEndIndex());
      Integer identifier = label.getIdentifier();
      if (identifier == null) {
        throw new IllegalArgumentException("Labels are not static, they do not have identifiers.");
      }
      genericLabelBuilder.setIdentifier(identifier);
    }
  }

  private void storeReferences(@NotNull List<@NotNull GenericLabel> labels) {
    for (GenericLabel label : labels) {
      JsonObjectImpl.Builder builder = JsonObjectImpl.newBuilder();
      for (Map.Entry<String, Object> entry : label.getReferenceCache().entrySet()) {
        Object o = convertToReference(entry.getValue());
        builder.setProperty(entry.getKey(), o);
      }
      JsonObjectImpl jsonObject = builder.build();
      label.setReferenceFieldIds(jsonObject);
    }
  }

  public static @Nullable Object convertToReference(@Nullable Object ref) {
    if (ref == null) {
      return null;
    }
    if (ref instanceof Label) {
      Label label = (Label) ref;
      return String.format("%s:%s", label.getLabelIndexName(), label.getIdentifier());
    }
    if (ref instanceof Map) {
      Map<?, ?> map = (Map<?, ?>) ref;
      JsonObjectImpl.Builder child = JsonObjectImpl.newBuilder();
      for (Map.Entry<?, ?> entry : map.entrySet()) {
        Object childKey = entry.getKey();
        if (!(childKey instanceof String)) {
          throw new IllegalArgumentException("Reference maps must only contain string keys.");
        }
        Object o = convertToReference(entry.getValue());
        child.put(((String) childKey), o);
      }
      return child.build();
    }
    if (ref instanceof List) {
      ArrayList<Object> copy = new ArrayList<>();
      for (Object o : (List<?>) ref) {
        Object o2 = convertToReference(o);
        copy.add(o2);
      }
      return copy;
    }
    throw new IllegalArgumentException("Reference unsupported type: " + ref.getClass());
  }
}

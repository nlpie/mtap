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

import com.google.protobuf.Struct;
import edu.umn.nlpie.mtap.Internal;
import edu.umn.nlpie.mtap.common.JsonObjectImpl;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.*;

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
    JsonLabels jsonLabels = response.getJsonLabels();
    boolean isDistinct = jsonLabels.getIsDistinct();

    List<GenericLabel> labels = new ArrayList<>();
    for (Struct struct : jsonLabels.getLabelsList()) {
      JsonObjectImpl.Builder builder = new JsonObjectImpl.Builder();
      builder.copyStruct(struct);
      labels.add(new GenericLabel(builder.build(), document));
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
    JsonLabels.Builder jsonLabelsBuilder = builder.getJsonLabelsBuilder();
    jsonLabelsBuilder.setIsDistinct(isDistinct);
    for (GenericLabel label : labels) {
      label.copyToStruct(jsonLabelsBuilder.addLabelsBuilder());
    }
  }
}

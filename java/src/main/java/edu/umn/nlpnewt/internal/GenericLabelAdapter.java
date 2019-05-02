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
package edu.umn.nlpnewt.internal;

import com.google.protobuf.Struct;
import edu.umn.nlpnewt.*;
import org.jetbrains.annotations.NotNull;

import java.util.*;

import static edu.umn.nlpnewt.api.v1.EventsOuterClass.*;

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
  public @NotNull LabelIndex<GenericLabel> createIndexFromResponse(@NotNull GetLabelsResponse response) {
    JsonLabels jsonLabels = response.getJsonLabels();

    List<GenericLabel> labels = new ArrayList<>();
    for (Struct struct : jsonLabels.getLabelsList()) {
      JsonObject.Builder builder = new JsonObject.Builder();
      builder.copyStruct(struct);
      labels.add(new GenericLabel(builder.build()));
    }

    return isDistinct ? Newt.distinctLabelIndex(labels) : Newt.standardLabelIndex(labels);
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
                           AddLabelsRequest.@NotNull Builder builder) {
    JsonLabels.Builder jsonLabelsBuilder = builder.getJsonLabelsBuilder();
    jsonLabelsBuilder.setIsDistinct(isDistinct);
    for (GenericLabel label : labels) {
      label.copyToStruct(jsonLabelsBuilder.addLabelsBuilder());
    }
  }
}

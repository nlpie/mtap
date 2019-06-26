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

import com.google.protobuf.Struct;
import com.google.protobuf.Value;
import edu.umn.nlpnewt.GenericLabel;
import edu.umn.nlpnewt.LabelIndex;
import edu.umn.nlpnewt.api.v1.EventsOuterClass.AddLabelsRequest;
import edu.umn.nlpnewt.api.v1.EventsOuterClass.GetLabelsResponse;
import edu.umn.nlpnewt.api.v1.EventsOuterClass.JsonLabels;
import org.junit.jupiter.api.Test;

import java.util.Arrays;

import static edu.umn.nlpnewt.GenericLabelAdapter.DISTINCT_ADAPTER;
import static edu.umn.nlpnewt.GenericLabelAdapter.NOT_DISTINCT_ADAPTER;
import static org.junit.jupiter.api.Assertions.*;

class GenericLabelAdapterTest {
  @Test
  void createIndexFromResponse() {
    GetLabelsResponse response = GetLabelsResponse.newBuilder()
        .setJsonLabels(
            JsonLabels.newBuilder()
                .addLabels(
                    Struct.newBuilder()
                        .putFields("start_index", Value.newBuilder().setNumberValue(0).build())
                        .putFields("end_index", Value.newBuilder().setNumberValue(10).build())
                        .build()
                )
                .addLabels(
                    Struct.newBuilder()
                        .putFields("start_index", Value.newBuilder().setNumberValue(10).build())
                        .putFields("end_index", Value.newBuilder().setNumberValue(20).build())
                        .build()
                )
                .setIsDistinct(true)
                .build()
        )
        .build();

    LabelIndex<GenericLabel> index = NOT_DISTINCT_ADAPTER.createIndexFromResponse(response);
    assertEquals(Arrays.asList(GenericLabel.newBuilder(0, 10).build(),
        GenericLabel.newBuilder(10, 20).build()), index.asList());
    assertTrue(index.isDistinct());
  }

  @Test
  void createLabelIndexDistinct() {
    LabelIndex<GenericLabel> index = DISTINCT_ADAPTER.createLabelIndex(Arrays.asList(GenericLabel.newBuilder(0, 10).build(),
        GenericLabel.newBuilder(10, 20).build()));
    assertTrue(index.isDistinct());
  }

  @Test
  void createLabelIndexStandard() {
    LabelIndex<GenericLabel> index = NOT_DISTINCT_ADAPTER.createLabelIndex(
        Arrays.asList(GenericLabel.newBuilder(0, 10).build(),
            GenericLabel.newBuilder(10, 20).build()));
    assertFalse(index.isDistinct());
  }

  @Test
  void addToMessage() {
    AddLabelsRequest.Builder builder = AddLabelsRequest.newBuilder();
    NOT_DISTINCT_ADAPTER.addToMessage(Arrays.asList(GenericLabel.newBuilder(0, 10).build(),
        GenericLabel.newBuilder(10, 20).build()), builder);
    AddLabelsRequest request = builder.build();
    JsonLabels jsonLabels = request.getJsonLabels();
    assertFalse(jsonLabels.getIsDistinct());
    assertEquals(2, jsonLabels.getLabelsCount());
    assertEquals(10, jsonLabels.getLabels(0).getFieldsOrThrow("end_index").getNumberValue());
    assertEquals(20, jsonLabels.getLabels(1).getFieldsOrThrow("end_index").getNumberValue());
  }

  @Test
  void getLabelType() {
    assertEquals(GenericLabel.class, DISTINCT_ADAPTER.getLabelType());
  }
}

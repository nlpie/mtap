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

import edu.umn.nlpie.mtap.ExperimentalApi;
import edu.umn.nlpie.mtap.api.v1.EventsOuterClass;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.List;

/**
 * Performs adaptation of label objects so that they can be uploaded to an events service.
 *
 * @param <L> Label type
 */
@ExperimentalApi
public interface ProtoLabelAdapter<L extends Label> {

  /**
   * The class of the type of label that will be adapted.
   *
   * @return Class object.
   */
  @NotNull Class<L> getLabelType();

  /**
   * Creates a label index from a response message from the events service.
   *
   * @param response The response message from the events service.
   *
   * @return A label index containing all of the labels in the response.
   */
  @NotNull LabelIndex<L> createIndexFromResponse(
      @NotNull EventsOuterClass.GetLabelsResponse response
  );

  /**
   * Creates a label index from the list of labels.
   *
   * @param labels The list of labels.
   *
   * @return A label index containing all of the labels in the list.
   */
  LabelIndex<L> createLabelIndex(List<@NotNull L> labels);

  /**
   * Adds the labels to an add labels request message.
   *
   * @param labels  The labels to add to the message.
   * @param builder The builder to add the labels to.
   */
  void addToMessage(
      @NotNull List<@NotNull L> labels,
      @NotNull EventsOuterClass.AddLabelsRequest.Builder builder
  );
}

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

import edu.umn.nlpnewt.api.v1.EventsOuterClass;
import org.jetbrains.annotations.NotNull;

import java.util.List;

@ExperimentalApi
public interface ProtoLabelAdapter<L extends Label> {
  @NotNull Class<L> getLabelType();

  @NotNull LabelIndex<L> createIndexFromResponse(@NotNull EventsOuterClass.GetLabelsResponse response);

  LabelIndex<L> createLabelIndex(List<@NotNull L> labels);

  void addToMessage(@NotNull List<@NotNull L> labels,
                    @NotNull EventsOuterClass.AddLabelsRequest.Builder builder);
}

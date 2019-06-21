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

package edu.umn.nlpnewt.internal.events;

import com.google.protobuf.ByteString;
import edu.umn.nlpnewt.*;
import org.jetbrains.annotations.NotNull;

import java.util.Collection;
import java.util.Collections;
import java.util.List;
import java.util.Map;

@Internal
interface EventsClient extends AutoCloseable {
  void openEvent(@NotNull String eventID, boolean onlyCreateNew);

  void closeEvent(@NotNull String eventID);

  @NotNull Map<String, String> getAllMetadata(@NotNull String eventID);

  void addMetadata(@NotNull String eventID, @NotNull String key, @NotNull String value);

  @NotNull Collection<String> getAllBinaryDataNames(@NotNull String eventID);

  void addBinaryData(@NotNull String eventID,
                     @NotNull String binaryDataName,
                     @NotNull byte[] bytes);

  byte[] getBinaryData(@NotNull String eventID,
                       @NotNull String binaryDataName);

  @NotNull Collection<String> getAllDocumentNames(@NotNull String eventID);

  void addDocument(@NotNull String eventID,
                   @NotNull String documentName,
                   @NotNull String text);

  @NotNull String getDocumentText(@NotNull String eventID, @NotNull String documentName);

  @NotNull List<@NotNull LabelIndexInfo> getLabelIndicesInfos(@NotNull String eventID,
                                                              @NotNull String documentName);

  <L extends Label> void addLabels(@NotNull String eventID,
                                   @NotNull String documentName,
                                   @NotNull String indexName,
                                   @NotNull List<L> labels,
                                   @NotNull ProtoLabelAdapter<L> adapter);

  <L extends Label> @NotNull LabelIndex<L> getLabels(@NotNull String eventID,
                                                     @NotNull String documentName,
                                                     @NotNull String indexName,
                                                     @NotNull ProtoLabelAdapter<L> adapter);

  @Override
  void close();
}

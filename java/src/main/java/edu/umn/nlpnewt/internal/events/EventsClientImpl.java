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

import edu.umn.nlpnewt.*;
import edu.umn.nlpnewt.api.v1.EventsGrpc;
import edu.umn.nlpnewt.api.v1.EventsOuterClass;
import io.grpc.ManagedChannel;
import org.jetbrains.annotations.NotNull;

import java.util.Collection;
import java.util.List;
import java.util.Map;

@Internal
public class EventsClientImpl implements EventsClient, AutoCloseable {

  private final EventsGrpc.EventsBlockingStub stub;
  private final ManagedChannel channel;

  EventsClientImpl(ManagedChannel channel) {
    stub = EventsGrpc.newBlockingStub(channel);
    this.channel = channel;
  }

  @Override
  public void openEvent(@NotNull String eventID, boolean onlyCreateNew) {
    EventsOuterClass.OpenEventRequest request = EventsOuterClass.OpenEventRequest.newBuilder()
        .setEventId(eventID)
        .setOnlyCreateNew(onlyCreateNew)
        .build();
    //noinspection ResultOfMethodCallIgnored
    stub.openEvent(request);
  }

  @Override
  public void closeEvent(@NotNull String eventID) {
    EventsOuterClass.CloseEventRequest request = EventsOuterClass.CloseEventRequest.newBuilder()
        .setEventId(eventID)
        .build();
    //noinspection ResultOfMethodCallIgnored
    stub.closeEvent(request);
  }

  @Override
  @NotNull
  public Map<String, String> getAllMetadata(@NotNull String eventID) {
    EventsOuterClass.GetAllMetadataRequest request = EventsOuterClass.GetAllMetadataRequest.newBuilder()
        .setEventId(eventID)
        .build();
    EventsOuterClass.GetAllMetadataResponse response = stub.getAllMetadata(request);
    return response.getMetadataMap();
  }

  @Override
  public void addMetadata(@NotNull String eventID, @NotNull String key, @NotNull String value) {
    EventsOuterClass.AddMetadataRequest req = EventsOuterClass.AddMetadataRequest.newBuilder()
        .setEventId(eventID)
        .setKey(key)
        .setValue(value)
        .build();
    //noinspection ResultOfMethodCallIgnored
    stub.addMetadata(req);
  }

  @Override
  @NotNull
  public Collection<String> getAllDocuments(@NotNull String eventID) {
    EventsOuterClass.GetAllDocumentNamesRequest request = EventsOuterClass.GetAllDocumentNamesRequest
        .newBuilder()
        .setEventId(eventID)
        .build();
    EventsOuterClass.GetAllDocumentNamesResponse response = stub.getAllDocumentNames(request);
    return response.getDocumentNamesList();
  }

  @Override
  public void addDocument(@NotNull String eventID,
                          @NotNull String documentName,
                          @NotNull String text) {
    EventsOuterClass.AddDocumentRequest request = EventsOuterClass.AddDocumentRequest.newBuilder()
        .setEventId(eventID)
        .setDocumentName(documentName)
        .setText(text)
        .build();
    //noinspection ResultOfMethodCallIgnored
    stub.addDocument(request);
  }

  @Override
  @NotNull
  public String getDocumentText(@NotNull String eventID, @NotNull String documentName) {
    EventsOuterClass.GetDocumentTextRequest request = EventsOuterClass.GetDocumentTextRequest.newBuilder()
        .setEventId(eventID)
        .setDocumentName(documentName)
        .build();
    EventsOuterClass.GetDocumentTextResponse response = stub.getDocumentText(request);
    return response.getText();
  }

  @Override
  public <L extends Label> void addLabels(@NotNull String eventID,
                                          @NotNull String documentName,
                                          @NotNull String indexName,
                                          @NotNull List<L> labels,
                                          @NotNull ProtoLabelAdapter<L> adapter) {
    EventsOuterClass.AddLabelsRequest.Builder requestBuilder = EventsOuterClass.AddLabelsRequest.newBuilder()
        .setEventId(eventID)
        .setDocumentName(documentName)
        .setIndexName(indexName);
    adapter.addToMessage(labels, requestBuilder);
    EventsOuterClass.AddLabelsRequest request = requestBuilder.build();

    //noinspection ResultOfMethodCallIgnored
    stub.addLabels(request);
  }

  @Override
  public <L extends Label> @NotNull LabelIndex<L> getLabels(@NotNull String eventID,
                                                            @NotNull String documentName,
                                                            @NotNull String indexName,
                                                            @NotNull ProtoLabelAdapter<L> adapter) {
    EventsOuterClass.GetLabelsRequest request = EventsOuterClass.GetLabelsRequest.newBuilder()
        .setEventId(eventID)
        .setDocumentName(documentName)
        .setIndexName(indexName)
        .build();
    EventsOuterClass.GetLabelsResponse response = stub.getLabels(request);
    return adapter.createIndexFromResponse(response);
  }

  @Override
  public void close() {
    channel.shutdown();
  }
}

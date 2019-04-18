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

import edu.umn.nlpnewt.*;
import edu.umn.nlpnewt.api.v1.EventsGrpc;
import edu.umn.nlpnewt.api.v1.EventsOuterClass.*;
import edu.umn.nlpnewt.api.v1.Labels;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.Collection;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Internal
final class NewtEventsImpl implements EventsClient {

  private final EventsGrpc.EventsBlockingStub stub;
  private final ManagedChannel channel;


  private NewtEventsImpl(ManagedChannel channel) {
    stub = EventsGrpc.newBlockingStub(channel);
    this.channel = channel;
  }

  static NewtEventsImpl create(Config config, @Nullable String address) {
    ManagedChannel channel;
    if (address == null) {
      String consulHost = config.getStringValue("consul.host");
      int consulPort = config.getIntegerValue("consul.port");
      channel = ManagedChannelBuilder
          .forTarget("consul://" + consulHost + ":" + consulPort + "/" + Newt.EVENTS_SERVICE_NAME)
          .usePlaintext()
          .nameResolverFactory(ConsulNameResolver.Factory.create())
          .build();
    } else {
      channel = ManagedChannelBuilder.forTarget(address).usePlaintext().build();
    }
    return new NewtEventsImpl(channel);
  }

  @Override
  @NotNull
  public Event openEvent(@Nullable String eventID) {
    if (eventID == null) {
      eventID = UUID.randomUUID().toString();
    }
    OpenEventRequest request = OpenEventRequest.newBuilder()
        .setEventId(eventID)
        .setOnlyCreateNew(false)
        .build();
    OpenEventResponse response = stub.openEvent(request);
    return new EventImpl(this, eventID);
  }

  @Override
  @NotNull
  public Event createEvent(@Nullable String eventID) {
    if (eventID == null) {
      eventID = UUID.randomUUID().toString();
    }
    OpenEventRequest request = OpenEventRequest.newBuilder()
        .setEventId(eventID)
        .setOnlyCreateNew(true)
        .build();
    //noinspection ResultOfMethodCallIgnored
    stub.openEvent(request);
    return new EventImpl(this, eventID);
  }

  @Override
  public void closeEvent(@NotNull String eventID) {
    CloseEventRequest request = CloseEventRequest.newBuilder()
        .setEventId(eventID)
        .build();
    //noinspection ResultOfMethodCallIgnored
    stub.closeEvent(request);
  }

  @Override
  @NotNull
  public Map<String, String> getAllMetadata(@NotNull String eventID) {
    GetAllMetadataRequest request = GetAllMetadataRequest.newBuilder()
        .setEventId(eventID)
        .build();
    GetAllMetadataResponse response = stub.getAllMetadata(request);
    return response.getMetadataMap();
  }

  @Override
  public void addMetadata(@NotNull String eventID, @NotNull String key, @NotNull String value) {
    AddMetadataRequest req = AddMetadataRequest.newBuilder()
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
    GetAllDocumentNamesRequest request = GetAllDocumentNamesRequest
        .newBuilder()
        .setEventId(eventID)
        .build();
    GetAllDocumentNamesResponse response = stub.getAllDocumentNames(request);
    return response.getDocumentNamesList();
  }

  @Override
  public void addDocument(@NotNull String eventID,
                          @NotNull String documentName,
                          @NotNull String text) {
    AddDocumentRequest request = AddDocumentRequest.newBuilder()
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
    GetDocumentTextRequest request = GetDocumentTextRequest.newBuilder()
        .setEventId(eventID)
        .setDocumentName(documentName)
        .build();
    GetDocumentTextResponse response = stub.getDocumentText(request);
    return response.getText();
  }

  @Override
  public <L extends Label> void addLabels(@NotNull String eventID,
                                          @NotNull String documentName,
                                          @NotNull String indexName,
                                          @NotNull List<L> labels,
                                          @NotNull ProtoLabelAdapter<L> adapter) {
    AddLabelsRequest.Builder requestBuilder = AddLabelsRequest.newBuilder()
        .setEventId(eventID)
        .setDocumentName(documentName)
        .setIndexName(indexName);
    adapter.addToMessage(labels, requestBuilder);
    AddLabelsRequest request = requestBuilder.build();

    //noinspection ResultOfMethodCallIgnored
    stub.addLabels(request);
  }

  @Override
  public <L extends Label> @NotNull LabelIndex<L> getLabels(@NotNull String eventID,
                                                            @NotNull String documentName,
                                                            @NotNull String indexName,
                                                            @NotNull ProtoLabelAdapter<L> adapter) {
    GetLabelsRequest request = GetLabelsRequest.newBuilder()
        .setEventId(eventID)
        .setDocumentName(documentName)
        .setIndexName(indexName)
        .build();
    GetLabelsResponse response = stub.getLabels(request);
    return adapter.createIndexFromResponse(response);
  }

  @Override
  public @NotNull LabelIndex<GenericLabel> getLabels(@NotNull String eventID,
                                                     @NotNull String documentName,
                                                     @NotNull String indexName) {
    GetLabelsRequest request = GetLabelsRequest.newBuilder()
        .setEventId(eventID)
        .setDocumentName(documentName)
        .setIndexName(indexName)
        .build();
    GetLabelsResponse response = stub.getLabels(request);
    Labels.JsonLabels jsonLabels = response.getJsonLabels();
    if (jsonLabels.getIsDistinct()) {
      return GenericLabelAdapter.DISTINCT_ADAPTER.createIndexFromResponse(response);
    } else {
      return GenericLabelAdapter.NOT_DISTINCT_ADAPTER.createIndexFromResponse(response);
    }
  }

  @Override
  public void close() {
    channel.shutdown();
  }
}

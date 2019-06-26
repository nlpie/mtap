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

import com.google.protobuf.ByteString;
import edu.umn.nlpnewt.*;
import edu.umn.nlpnewt.api.v1.EventsGrpc;
import edu.umn.nlpnewt.api.v1.EventsOuterClass.*;
import io.grpc.ManagedChannel;
import org.jetbrains.annotations.NotNull;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Map;

@Internal
public class EventsClient implements AutoCloseable {

  private final EventsGrpc.EventsBlockingStub stub;
  private final ManagedChannel channel;

  public EventsClient(ManagedChannel channel) {
    stub = EventsGrpc.newBlockingStub(channel);
    this.channel = channel;
  }

  public void openEvent(@NotNull String eventID, boolean onlyCreateNew) {
    OpenEventRequest request = OpenEventRequest.newBuilder()
        .setEventId(eventID)
        .setOnlyCreateNew(onlyCreateNew)
        .build();
    //noinspection ResultOfMethodCallIgnored
    stub.openEvent(request);
  }

  public void closeEvent(@NotNull String eventID) {
    CloseEventRequest request = CloseEventRequest.newBuilder()
        .setEventId(eventID)
        .build();
    //noinspection ResultOfMethodCallIgnored
    stub.closeEvent(request);
  }

  @NotNull
  public Map<String, String> getAllMetadata(@NotNull String eventID) {
    GetAllMetadataRequest request = GetAllMetadataRequest.newBuilder()
        .setEventId(eventID)
        .build();
    GetAllMetadataResponse response = stub.getAllMetadata(request);
    return response.getMetadataMap();
  }

  public void addMetadata(@NotNull String eventID, @NotNull String key, @NotNull String value) {
    AddMetadataRequest req = AddMetadataRequest.newBuilder()
        .setEventId(eventID)
        .setKey(key)
        .setValue(value)
        .build();
    //noinspection ResultOfMethodCallIgnored
    stub.addMetadata(req);
  }

  public @NotNull Collection<String> getAllBinaryDataNames(@NotNull String eventID) {
    GetAllBinaryDataNamesRequest request = GetAllBinaryDataNamesRequest.newBuilder()
        .setEventId(eventID)
        .build();
    GetAllBinaryDataNamesResponse response = stub.getAllBinaryDataNames(request);
    return response.getBinaryDataNamesList();
  }

  public void addBinaryData(@NotNull String eventID, @NotNull String binaryDataName, @NotNull byte[] bytes) {
    AddBinaryDataRequest request = AddBinaryDataRequest.newBuilder()
        .setEventId(eventID)
        .setBinaryDataName(binaryDataName)
        .setBinaryData(ByteString.copyFrom(bytes))
        .build();
    //noinspection ResultOfMethodCallIgnored
    stub.addBinaryData(request);
  }

  public byte[] getBinaryData(@NotNull String eventID, @NotNull String binaryDataName) {
    GetBinaryDataRequest request = GetBinaryDataRequest.newBuilder()
        .setEventId(eventID)
        .setBinaryDataName(binaryDataName)
        .build();
    GetBinaryDataResponse response = stub.getBinaryData(request);
    return response.getBinaryData().toByteArray();
  }

  @NotNull
  public Collection<String> getAllDocumentNames(@NotNull String eventID) {
    GetAllDocumentNamesRequest request = GetAllDocumentNamesRequest
        .newBuilder()
        .setEventId(eventID)
        .build();
    GetAllDocumentNamesResponse response = stub.getAllDocumentNames(request);
    return response.getDocumentNamesList();
  }

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

  @NotNull
  public String getDocumentText(@NotNull String eventID, @NotNull String documentName) {
    GetDocumentTextRequest request = GetDocumentTextRequest.newBuilder()
        .setEventId(eventID)
        .setDocumentName(documentName)
        .build();
    GetDocumentTextResponse response = stub.getDocumentText(request);
    return response.getText();
  }

  public @NotNull List<@NotNull LabelIndexInfo> getLabelIndicesInfos(@NotNull String eventID,
                                                                     @NotNull String documentName) {
    GetLabelIndicesInfoRequest request = GetLabelIndicesInfoRequest.newBuilder()
        .setEventId(eventID)
        .setDocumentName(documentName)
        .build();
    GetLabelIndicesInfoResponse response = stub.getLabelIndicesInfo(request);
    List<LabelIndexInfo> result = new ArrayList<>();
    for (GetLabelIndicesInfoResponse.LabelIndexInfo info : response.getLabelIndexInfosList()) {
      LabelIndexInfo.LabelIndexType type;
      switch (info.getType()) {
        case OTHER:
          type = LabelIndexInfo.LabelIndexType.OTHER;
          break;
        case JSON:
          type = LabelIndexInfo.LabelIndexType.JSON;
          break;
        default:
          type = LabelIndexInfo.LabelIndexType.UNKNOWN;
          break;
      }
      result.add(new LabelIndexInfo(info.getIndexName(), type));
    }
    return result;
  }

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
  public void close() {
    channel.shutdown();
  }
}

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

import com.google.protobuf.ByteString;
import edu.umn.nlpie.mtap.api.v1.EventsGrpc;
import edu.umn.nlpie.mtap.api.v1.EventsOuterClass.*;
import edu.umn.nlpie.mtap.common.Config;
import edu.umn.nlpie.mtap.common.ConfigImpl;
import edu.umn.nlpie.mtap.discovery.Discovery;
import edu.umn.nlpie.mtap.discovery.DiscoveryMechanism;
import edu.umn.nlpie.mtap.exc.EventExistsException;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import io.grpc.Status;
import io.grpc.StatusRuntimeException;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.io.Closeable;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;

import static edu.umn.nlpie.mtap.MTAP.EVENTS_SERVICE_NAME;

/**
 * A client to an events service.
 */
public class EventsClient implements AutoCloseable {

  private final ManagedChannel channel;

  private final EventsGrpc.EventsBlockingStub stub;

  private final String instanceId;

  /**
   * Creates a client.
   *
   * @param channel The GRPC channel to the events service.
   */
  public EventsClient(ManagedChannel channel) {
    this.channel = channel;
    stub = EventsGrpc.newBlockingStub(channel);
    GetEventsInstanceIdResponse response = stub
        .getEventsInstanceId(GetEventsInstanceIdRequest.newBuilder().build());
    instanceId = response.getInstanceId();
  }

  public String getInstanceId() {
    return instanceId;
  }

  /**
   * Opens the event with the ID, if it does not already exist it will be created.
   *
   * @param eventID       The unique event identifier.
   * @param onlyCreateNew Fail if the event already exists.
   * @throws EventExistsException if the event already exists on the events
   *                              service and only create new is set.
   */
  @SuppressWarnings("ResultOfMethodCallIgnored")
  public void openEvent(@NotNull String eventID, boolean onlyCreateNew) {
    OpenEventRequest request = OpenEventRequest.newBuilder()
        .setEventId(eventID)
        .setOnlyCreateNew(onlyCreateNew)
        .build();
    try {
      stub.openEvent(request);
    } catch (StatusRuntimeException e) {
      if (e.getStatus().getCode() == Status.Code.ALREADY_EXISTS) {
        EventExistsException exception = new EventExistsException(
            "An event already exists with the id: " + eventID
        );
        exception.addSuppressed(e);
        throw exception;
      }
      throw e;
    }
  }

  /**
   * Closes the event with the given ID, releasing a permit on the event.
   *
   * @param eventID The event identifier.
   */
  @SuppressWarnings("ResultOfMethodCallIgnored")
  public void closeEvent(@NotNull String eventID) {
    CloseEventRequest request = CloseEventRequest.newBuilder()
        .setEventId(eventID)
        .build();
    stub.closeEvent(request);
  }

  /**
   * Returns a map of all the metadata on the event.
   *
   * @param eventID The unique event identifier.
   * @return A map of all the current metadata on the event.
   */
  public @NotNull Map<String, String> getAllMetadata(@NotNull String eventID) {
    GetAllMetadataRequest request = GetAllMetadataRequest.newBuilder()
        .setEventId(eventID)
        .build();
    GetAllMetadataResponse response = stub.getAllMetadata(request);
    return response.getMetadataMap();
  }

  /**
   * Adds a metadata entry to the event.
   *
   * @param eventID The unique event identifier.
   * @param key     The metadata's key.
   * @param value   The metadata's value.
   */
  @SuppressWarnings("ResultOfMethodCallIgnored")
  public void addMetadata(@NotNull String eventID, @NotNull String key, @NotNull String value) {
    AddMetadataRequest req = AddMetadataRequest.newBuilder()
        .setEventId(eventID)
        .setKey(key)
        .setValue(value)
        .build();
    stub.addMetadata(req);
  }

  /**
   * Get all of the keys that have associated binary data in the event's binaries map.
   *
   * @param eventID The unique event identifier.
   * @return A collection of all of the binary data names.
   */
  public @NotNull Collection<String> getAllBinaryDataNames(@NotNull String eventID) {
    GetAllBinaryDataNamesRequest request = GetAllBinaryDataNamesRequest.newBuilder()
        .setEventId(eventID)
        .build();
    GetAllBinaryDataNamesResponse response = stub.getAllBinaryDataNames(request);
    return response.getBinaryDataNamesList();
  }

  /**
   * Adds binary data to the event.
   *
   * @param eventID        The unique event identifier.
   * @param binaryDataName The key for the binary data.
   * @param bytes          The binary data.
   */
  @SuppressWarnings("ResultOfMethodCallIgnored")
  public void addBinaryData(
      @NotNull String eventID,
      @NotNull String binaryDataName,
      @NotNull byte[] bytes
  ) {
    AddBinaryDataRequest request = AddBinaryDataRequest.newBuilder()
        .setEventId(eventID)
        .setBinaryDataName(binaryDataName)
        .setBinaryData(ByteString.copyFrom(bytes))
        .build();
    stub.addBinaryData(request);
  }

  /**
   * Gets binary data on the event.
   *
   * @param eventID        The unique event identifier.
   * @param binaryDataName The key for the binary data.
   * @return The binary data.
   */
  public byte[] getBinaryData(@NotNull String eventID, @NotNull String binaryDataName) {
    GetBinaryDataRequest request = GetBinaryDataRequest.newBuilder()
        .setEventId(eventID)
        .setBinaryDataName(binaryDataName)
        .build();
    GetBinaryDataResponse response = stub.getBinaryData(request);
    return response.getBinaryData().toByteArray();
  }

  /**
   * Gets all of the names of documents that are stored on an event.
   *
   * @param eventID The unique event identifier.
   * @return A collection of document name strings.
   */
  public @NotNull Collection<String> getAllDocumentNames(@NotNull String eventID) {
    GetAllDocumentNamesRequest request = GetAllDocumentNamesRequest
        .newBuilder()
        .setEventId(eventID)
        .build();
    GetAllDocumentNamesResponse response = stub.getAllDocumentNames(request);
    return response.getDocumentNamesList();
  }

  /**
   * Attaches a document to the event.
   *
   * @param eventID      The unique event identifier.
   * @param documentName An identifier string for the document relative to the event.
   * @param text         The document text.
   */
  @SuppressWarnings("ResultOfMethodCallIgnored")
  public void addDocument(
      @NotNull String eventID,
      @NotNull String documentName,
      @NotNull String text
  ) {
    AddDocumentRequest request = AddDocumentRequest.newBuilder()
        .setEventId(eventID)
        .setDocumentName(documentName)
        .setText(text)
        .build();
    stub.addDocument(request);
  }

  /**
   * Retrieves the text of a document.
   *
   * @param eventID      The unique event identifier.
   * @param documentName The event-unique document identifier.
   * @return A string of the document text.
   */
  public @NotNull String getDocumentText(@NotNull String eventID, @NotNull String documentName) {
    GetDocumentTextRequest request = GetDocumentTextRequest.newBuilder()
        .setEventId(eventID)
        .setDocumentName(documentName)
        .build();
    GetDocumentTextResponse response = stub.getDocumentText(request);
    return response.getText();
  }

  /**
   * Gets information about the label indices on a document and their type.
   *
   * @param eventID      The unique event identifier.
   * @param documentName The event-unique document identifier.
   * @return A list of LabelIndexInfo objects which contain the name and type of the label indices.
   */
  public @NotNull List<@NotNull LabelIndexInfo> getLabelIndicesInfos(
      @NotNull String eventID,
      @NotNull String documentName
  ) {
    GetLabelIndicesInfoRequest request = GetLabelIndicesInfoRequest.newBuilder()
        .setEventId(eventID)
        .setDocumentName(documentName)
        .build();
    GetLabelIndicesInfoResponse response = stub.getLabelIndicesInfo(request);
    List<LabelIndexInfo> result = new ArrayList<>();
    for (GetLabelIndicesInfoResponse.LabelIndexInfo info : response.getLabelIndexInfosList()) {
      LabelIndexInfo.LabelIndexType type;
      switch (info.getType()) {
        case CUSTOM:
          type = LabelIndexInfo.LabelIndexType.CUSTOM;
          break;
        case GENERIC:
          type = LabelIndexInfo.LabelIndexType.GENERIC;
          break;
        default:
          type = LabelIndexInfo.LabelIndexType.UNKNOWN;
          break;
      }
      result.add(new LabelIndexInfo(info.getIndexName(), type));
    }
    return result;
  }

  /**
   * Adds a label index to a document.
   *
   * @param eventID      The unique event identifier.
   * @param documentName The event-unique document identifier.
   * @param indexName    The label index identifier.
   * @param labels       The labels to add.
   * @param adapter      An adapter which transforms the labels into proto messages.
   * @param <L>          The label type.
   */
  @SuppressWarnings("ResultOfMethodCallIgnored")
  public <L extends Label> void addLabels(
      @NotNull String eventID,
      @NotNull String documentName,
      @NotNull String indexName,
      @NotNull List<@NotNull L> labels,
      @NotNull ProtoLabelAdapter<L> adapter
  ) {
    AddLabelsRequest.Builder requestBuilder = AddLabelsRequest.newBuilder()
        .setEventId(eventID)
        .setDocumentName(documentName)
        .setIndexName(indexName)
        .setNoKeyValidation(true);
    adapter.addToMessage(labels, requestBuilder);
    AddLabelsRequest request = requestBuilder.build();
    stub.addLabels(request);
  }

  /**
   * Retrieves a label index from a document.
   *
   * @param document  The document the labels appear on.
   * @param indexName The label index identifier.
   * @param adapter   An adapter which will transform proto messages into labels.
   * @param <L>       The label type.
   * @return A label index containing the specified labels.
   */
  public <L extends Label> @NotNull LabelIndex<L> getLabels(
      @NotNull Document document,
      @NotNull String indexName,
      @NotNull ProtoLabelAdapter<L> adapter
  ) {
    if (document.getEvent() == null) {
      throw new IllegalStateException("Attempting to retrieve labels from document without an event.");
    }
    GetLabelsRequest request = GetLabelsRequest.newBuilder()
        .setEventId(document.getEvent().getEventID())
        .setDocumentName(document.getName())
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

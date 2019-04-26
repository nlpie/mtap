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

import com.google.protobuf.Any;
import edu.umn.nlpnewt.api.v1.EventsGrpc;
import io.grpc.stub.StreamObserver;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import static edu.umn.nlpnewt.api.v1.EventsOuterClass.*;

public class EventsService extends EventsGrpc.EventsImplBase {

  private static class LabelIndex {
    JsonLabels jsonLabels = null;
    Any otherLabels = null;
  }

  private static class Document {
    String text;
    Map<String, LabelIndex> labelIndexMap = new HashMap<>();
  }

  private static class Event {
    Map<String, Document> documents = new HashMap<>();
    Map<String, String> metadata = new HashMap<>();
    int references = 0;
  }

  Map<String, Event> eventMap = new ConcurrentHashMap<>();

  @Override
  public void openEvent(OpenEventRequest request, StreamObserver<OpenEventResponse> responseObserver) {
    String eventId = request.getEventId();
    Event event = eventMap.get(eventId);
    boolean created = false;
    if (event == null) {
      created = true;
      event = new Event();
      eventMap.put(eventId, event);
    }
    event.references++;
    responseObserver.onNext(OpenEventResponse.newBuilder().setCreated(created).build());
    responseObserver.onCompleted();
  }

  @Override
  public void closeEvent(CloseEventRequest request, StreamObserver<CloseEventResponse> responseObserver) {
    String eventId = request.getEventId();
    Event event = eventMap.get(eventId);
    boolean deleted = false;
    if (event != null) {
      event.references--;
      if (event.references == 0) {
        deleted = true;
        eventMap.remove(eventId);
      }
    }
    responseObserver.onNext(CloseEventResponse.newBuilder().setDeleted(deleted).build());
    responseObserver.onCompleted();
  }

  @Override
  public void getAllMetadata(GetAllMetadataRequest request, StreamObserver<GetAllMetadataResponse> responseObserver) {
    String eventId = request.getEventId();
    Event event = eventMap.get(eventId);
    GetAllMetadataResponse response = GetAllMetadataResponse.newBuilder().putAllMetadata(event.metadata).build();
    responseObserver.onNext(response);
    responseObserver.onCompleted();
  }

  @Override
  public void addMetadata(AddMetadataRequest request, StreamObserver<AddMetadataResponse> responseObserver) {
    String eventId = request.getEventId();
    Event event = eventMap.get(eventId);
    event.metadata.put(request.getKey(), request.getValue());
    responseObserver.onNext(AddMetadataResponse.newBuilder().build());
    responseObserver.onCompleted();
  }

  @Override
  public void addDocument(AddDocumentRequest request, StreamObserver<AddDocumentResponse> responseObserver) {
    String eventId = request.getEventId();
    Event event = eventMap.get(eventId);
    Document document = new Document();
    document.text = request.getText();
    event.documents.put(request.getDocumentName(), document);
    responseObserver.onNext(AddDocumentResponse.newBuilder().build());
    responseObserver.onCompleted();
  }

  @Override
  public void getAllDocumentNames(GetAllDocumentNamesRequest request, StreamObserver<GetAllDocumentNamesResponse> responseObserver) {
    String eventId = request.getEventId();
    Event event = eventMap.get(eventId);
    GetAllDocumentNamesResponse response = GetAllDocumentNamesResponse.newBuilder()
        .addAllDocumentNames(event.documents.keySet())
        .build();
    responseObserver.onNext(response);
    responseObserver.onCompleted();
  }

  @Override
  public void getDocumentText(GetDocumentTextRequest request, StreamObserver<GetDocumentTextResponse> responseObserver) {
    String eventId = request.getEventId();
    Event event = eventMap.get(eventId);
    Document document = event.documents.get(request.getDocumentName());
    GetDocumentTextResponse response = GetDocumentTextResponse.newBuilder()
        .setText(document.text)
        .build();
    responseObserver.onNext(response);
    responseObserver.onCompleted();
  }

  @Override
  public void addLabels(AddLabelsRequest request, StreamObserver<AddLabelsResponse> responseObserver) {
    String eventId = request.getEventId();
    Event event = eventMap.get(eventId);
    Document document = event.documents.get(request.getDocumentName());
    if (request.hasJsonLabels()) {
      LabelIndex value = new LabelIndex();
      value.jsonLabels = JsonLabels.newBuilder(request.getJsonLabels()).build();
      document.labelIndexMap.put(request.getIndexName(), value);
    } else if (request.hasOtherLabels()) {
      LabelIndex value = new LabelIndex();
      value.otherLabels = request.getOtherLabels();
      document.labelIndexMap.put(request.getIndexName(), value);
    }
    responseObserver.onNext(AddLabelsResponse.newBuilder().build());
    responseObserver.onCompleted();
  }

  @Override
  public void getLabels(GetLabelsRequest request, StreamObserver<GetLabelsResponse> responseObserver) {
    String eventId = request.getEventId();
    Event event = eventMap.get(eventId);
    Document document = event.documents.get(request.getDocumentName());
    LabelIndex labelIndex = document.labelIndexMap.get(request.getIndexName());
    GetLabelsResponse.Builder builder = GetLabelsResponse.newBuilder();
    if (labelIndex.jsonLabels != null) {
      builder.setJsonLabels(labelIndex.jsonLabels);
    } else if (labelIndex.otherLabels != null) {
      builder.setOtherLabels(labelIndex.otherLabels);
    }
    responseObserver.onNext(builder.build());
    responseObserver.onCompleted();
  }
}

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

package edu.umn.nlpnewt.model;

import com.google.protobuf.ByteString;
import edu.umn.nlpnewt.api.v1.EventsGrpc;
import edu.umn.nlpnewt.api.v1.EventsOuterClass.*;
import edu.umn.nlpnewt.api.v1.EventsOuterClass.GetLabelIndicesInfoResponse.LabelIndexInfo.LabelIndexType;
import edu.umn.nlpnewt.model.*;
import io.grpc.ManagedChannel;
import io.grpc.inprocess.InProcessChannelBuilder;
import io.grpc.inprocess.InProcessServerBuilder;
import io.grpc.stub.StreamObserver;
import io.grpc.testing.GrpcCleanupRule;
import org.jetbrains.annotations.NotNull;
import org.junit.Rule;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.mockito.Mockito;
import org.mockito.stubbing.Answer;

import java.io.IOException;
import java.util.*;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

class EventsClientTest {

  @Rule
  public final GrpcCleanupRule grpcCleanup = new GrpcCleanupRule();

  private EventsGrpc.EventsImplBase eventsService;

  private EventsClient tested;
  private ProtoLabelAdapter adapter;

  @BeforeEach
  void setUp() throws IOException {
    eventsService = mock(EventsGrpc.EventsImplBase.class, Mockito.CALLS_REAL_METHODS);
    String name = InProcessServerBuilder.generateName();
    grpcCleanup.register(InProcessServerBuilder
        .forName(name).directExecutor().addService(eventsService).build().start());

    ManagedChannel channel = grpcCleanup.register(InProcessChannelBuilder.forName(name).directExecutor().build());

    tested = new EventsClient(channel);

    adapter = mock(ProtoLabelAdapter.class);
  }

  @Test
  @SuppressWarnings("unchecked")
  void openEvent() {
    doAnswer((Answer<Void>) invocation -> {
      StreamObserver<OpenEventResponse> observer = invocation.getArgument(1);
      observer.onNext(OpenEventResponse.newBuilder().setCreated(false).build());
      observer.onCompleted();
      return null;
    }).when(eventsService).openEvent(
        any(OpenEventRequest.class),
        any(StreamObserver.class)
    );

    tested.openEvent("1", true);
    ArgumentCaptor<OpenEventRequest> captor = ArgumentCaptor
        .forClass(OpenEventRequest.class);
    verify(eventsService).openEvent(captor.capture(), any());
    OpenEventRequest request = captor.getValue();
    assertEquals("1", request.getEventId());
    assertTrue(request.getOnlyCreateNew());
  }

  @Test
  void closeEvent() {
    doAnswer((Answer<Void>) invocation -> {
      StreamObserver<CloseEventResponse> observer = invocation.getArgument(1);
      observer.onNext(CloseEventResponse.newBuilder().setDeleted(true).build());
      observer.onCompleted();
      return null;
    }).when(eventsService).closeEvent(any(), any());

    tested.closeEvent("1");
    ArgumentCaptor<CloseEventRequest> captor = ArgumentCaptor.forClass(CloseEventRequest.class);
    verify(eventsService).closeEvent(captor.capture(), any());
    CloseEventRequest request = captor.getValue();
    assertEquals("1", request.getEventId());
  }

  @Test
  void getAllMetadata() {
    HashMap<String, String> map = new HashMap<>();
    map.put("foo", "bar");
    doAnswer((Answer<Void>) invocation -> {
      StreamObserver<GetAllMetadataResponse> observer = invocation.getArgument(1);
      observer.onNext(GetAllMetadataResponse.newBuilder().putAllMetadata(map).build());
      observer.onCompleted();
      return null;
    }).when(eventsService).getAllMetadata(
        any(),
        any()
    );

    Map<String, String> metadata = tested.getAllMetadata("1");
    ArgumentCaptor<GetAllMetadataRequest> captor = ArgumentCaptor
        .forClass(GetAllMetadataRequest.class);
    verify(eventsService).getAllMetadata(captor.capture(), any());
    GetAllMetadataRequest request = captor.getValue();
    assertEquals("1", request.getEventId());
    assertTrue(metadata.containsKey("foo"));
    assertEquals("bar", metadata.get("foo"));
  }

  @Test
  void addMetadata() {
    doAnswer((Answer<Void>) invocation -> {
      StreamObserver<AddMetadataResponse> observer = invocation.getArgument(1);
      observer.onNext(AddMetadataResponse.newBuilder().build());
      observer.onCompleted();
      return null;
    }).when(eventsService).addMetadata(any(), any());

    tested.addMetadata("1", "foo", "bar");
    ArgumentCaptor<AddMetadataRequest> captor = ArgumentCaptor.forClass(AddMetadataRequest.class);
    verify(eventsService).addMetadata(captor.capture(), any());
    AddMetadataRequest request = captor.getValue();
    assertEquals("1", request.getEventId());
    assertEquals("foo", request.getKey());
    assertEquals("bar", request.getValue());
  }

  @Test
  void getAllBinaryDataNames() {
    doAnswer((Answer<Void>) invocation -> {
      StreamObserver<GetAllBinaryDataNamesResponse> observer = invocation.getArgument(1);
      observer.onNext(GetAllBinaryDataNamesResponse.newBuilder().addBinaryDataNames("a")
      .addBinaryDataNames("b").build());
      observer.onCompleted();
      return null;
    }).when(eventsService).getAllBinaryDataNames(any(), any());
    Collection<String> response = tested.getAllBinaryDataNames("1");
    ArgumentCaptor<GetAllBinaryDataNamesRequest> captor = ArgumentCaptor.forClass(GetAllBinaryDataNamesRequest.class);
    verify(eventsService).getAllBinaryDataNames(captor.capture(), any());
    GetAllBinaryDataNamesRequest request = captor.getValue();
    assertEquals("1", request.getEventId());
    assertEquals(2, response.size());
    assertTrue(response.contains("a"));
    assertTrue(response.contains("b"));
  }

  @Test
  void addBinaryData() {
    doAnswer((Answer<Void>) invocation -> {
      StreamObserver<AddBinaryDataResponse> observer = invocation.getArgument(1);
      observer.onNext(AddBinaryDataResponse.newBuilder().build());
      observer.onCompleted();
      return null;
    }).when(eventsService).addBinaryData(any(), any());
    tested.addBinaryData("1", "a", new byte[] {(byte) 0xBF, (byte) 0xFF});
    ArgumentCaptor<AddBinaryDataRequest> captor = ArgumentCaptor.forClass(AddBinaryDataRequest.class);
    verify(eventsService).addBinaryData(captor.capture(), any());
    AddBinaryDataRequest request = captor.getValue();
    assertArrayEquals(request.getBinaryData().toByteArray(), new byte[]{(byte) 0xBF, (byte) 0xFF});
  }

  @Test
  void getBinaryData() {
    doAnswer((Answer<Void>) invocation -> {
      StreamObserver<GetBinaryDataResponse> observer = invocation.getArgument(1);
      observer.onNext(GetBinaryDataResponse.newBuilder().setBinaryData(ByteString.copyFrom(
          new byte[] {(byte) 0xBF, (byte) 0xFF}
      )).build());
      observer.onCompleted();
      return null;
    }).when(eventsService).getBinaryData(any(), any());
    byte[] b = tested.getBinaryData("1", "a");
    ArgumentCaptor<GetBinaryDataRequest> captor = ArgumentCaptor.forClass(GetBinaryDataRequest.class);
    verify(eventsService).getBinaryData(captor.capture(), any());
    GetBinaryDataRequest request = captor.getValue();
    assertArrayEquals(new byte[] {(byte) 0xBF, (byte) 0xFF}, b);
    assertEquals("1", request.getEventId());
    assertEquals("a", request.getBinaryDataName());
  }

  @Test
  void getAllDocuments() {
    doAnswer((Answer<Void>) invocation -> {
      StreamObserver<GetAllDocumentNamesResponse> observer = invocation.getArgument(1);
      observer.onNext(GetAllDocumentNamesResponse.newBuilder().addDocumentNames("foo")
          .addDocumentNames("bar").build());
      observer.onCompleted();
      return null;
    }).when(eventsService).getAllDocumentNames(any(), any());

    Collection<String> documents = tested.getAllDocumentNames("1");
    ArgumentCaptor<GetAllDocumentNamesRequest> captor = ArgumentCaptor
        .forClass(GetAllDocumentNamesRequest.class);
    verify(eventsService).getAllDocumentNames(captor.capture(), any());
    GetAllDocumentNamesRequest request = captor.getValue();
    assertEquals("1", request.getEventId());
    assertEquals(2, documents.size());
    assertTrue(documents.contains("foo"));
    assertTrue(documents.contains("bar"));
  }

  @Test
  void addDocument() {
    doAnswer((Answer<Void>) invocation -> {
      StreamObserver<AddDocumentResponse> observer = invocation.getArgument(1);
      observer.onNext(AddDocumentResponse.newBuilder().build());
      observer.onCompleted();
      return null;
    }).when(eventsService).addDocument(any(), any());

    tested.addDocument("1", "plaintext", "Some text");
    ArgumentCaptor<AddDocumentRequest> captor = ArgumentCaptor.forClass(AddDocumentRequest.class);
    verify(eventsService).addDocument(captor.capture(), any());
    AddDocumentRequest request = captor.getValue();
    assertEquals("1", request.getEventId());
    assertEquals("plaintext", request.getDocumentName());
    assertEquals("Some text", request.getText());
  }

  @Test
  void getDocumentText() {
    doAnswer((Answer<Void>) invocation -> {
      StreamObserver<GetDocumentTextResponse> observer = invocation.getArgument(1);
      observer.onNext(GetDocumentTextResponse.newBuilder().setText("Some text.").build());
      observer.onCompleted();
      return null;
    }).when(eventsService).getDocumentText(any(), any());

    String text = tested.getDocumentText("1", "plaintext");
    ArgumentCaptor<GetDocumentTextRequest> captor = ArgumentCaptor
        .forClass(GetDocumentTextRequest.class);
    verify(eventsService).getDocumentText(captor.capture(), any());
    assertEquals("Some text.", text);
    GetDocumentTextRequest request = captor.getValue();
    assertEquals("1", request.getEventId());
    assertEquals("plaintext", request.getDocumentName());
  }

  @Test
  void getLabelIndicesInfo() {
    doAnswer((Answer<Void>) invocation -> {
      StreamObserver<GetLabelIndicesInfoResponse> observer = invocation.getArgument(1);
      GetLabelIndicesInfoResponse.Builder builder = GetLabelIndicesInfoResponse.newBuilder();
      builder.addLabelIndexInfosBuilder().setIndexName("foo").setType(LabelIndexType.JSON).build();
      builder.addLabelIndexInfosBuilder().setIndexName("bar").setType(LabelIndexType.OTHER).build();
      builder.addLabelIndexInfosBuilder().setIndexName("baz").setType(LabelIndexType.UNKNOWN)
          .build();
      observer.onNext(builder.build());
      observer.onCompleted();
      return null;
    }).when(eventsService).getLabelIndicesInfo(any(), any());

    List<@NotNull LabelIndexInfo> infos = tested.getLabelIndicesInfos("1", "plaintext");
    ArgumentCaptor<GetLabelIndicesInfoRequest> captor = ArgumentCaptor
        .forClass(GetLabelIndicesInfoRequest.class);
    verify(eventsService).getLabelIndicesInfo(captor.capture(), any());
    assertEquals(3, infos.size());
    assertEquals(new LabelIndexInfo("foo", LabelIndexInfo.LabelIndexType.JSON), infos.get(0));
    assertEquals(new LabelIndexInfo("bar", LabelIndexInfo.LabelIndexType.OTHER), infos.get(1));
    assertEquals(new LabelIndexInfo("baz", LabelIndexInfo.LabelIndexType.UNKNOWN), infos.get(2));
    GetLabelIndicesInfoRequest req = captor.getValue();
    assertEquals("1", req.getEventId());
    assertEquals("plaintext", req.getDocumentName());
  }

  @Test
  @SuppressWarnings("unchecked")
  void addLabels() {
    doAnswer((Answer<Void>) invocation -> {
      StreamObserver<AddLabelsResponse> observer = invocation.getArgument(1);
      observer.onNext(AddLabelsResponse.getDefaultInstance());
      observer.onCompleted();
      return null;
    }).when(eventsService).addLabels(any(), any());

    tested.addLabels("1", "plaintext", "index",
        Collections.singletonList(GenericLabel.createSpan(1, 5)), adapter);
    ArgumentCaptor<AddLabelsRequest> captor = ArgumentCaptor.forClass(AddLabelsRequest.class);
    verify(eventsService).addLabels(captor.capture(), any());
    verify(adapter).addToMessage(eq(Collections.singletonList(GenericLabel.createSpan(1, 5))), any());
    AddLabelsRequest request = captor.getValue();
    assertEquals("1", request.getEventId());
    assertEquals("plaintext", request.getDocumentName());
    assertEquals("index", request.getIndexName());
  }

  @Test
  @SuppressWarnings("unchecked")
  void getLabelsWithAdapter() {
    doAnswer((Answer<Void>) invocation -> {
      StreamObserver<GetLabelsResponse> observer = invocation.getArgument(1);
      observer.onNext(GetLabelsResponse.newBuilder().build());
      observer.onCompleted();
      return null;
    }).when(eventsService).getLabels(any(), any());
    when(adapter.createIndexFromResponse(any()))
        .thenReturn(new StandardLabelIndex(Collections.singletonList(GenericLabel.createSpan(0, 5))));
    tested.getLabels("1", "plaintext", "index", adapter);
    ArgumentCaptor<GetLabelsRequest> captor = ArgumentCaptor.forClass(GetLabelsRequest.class);
    verify(eventsService).getLabels(captor.capture(), any());
    GetLabelsRequest request = captor.getValue();
    assertEquals("1", request.getEventId());
    assertEquals("plaintext", request.getDocumentName());
    assertEquals("index", request.getIndexName());
    verify(adapter).createIndexFromResponse(any());
  }
}

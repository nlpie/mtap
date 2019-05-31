package edu.umn.nlpnewt.internal.events;

import edu.umn.nlpnewt.LabelIndexInfo;
import edu.umn.nlpnewt.ProtoLabelAdapter;
import edu.umn.nlpnewt.api.v1.EventsGrpc;
import edu.umn.nlpnewt.api.v1.EventsOuterClass.*;
import edu.umn.nlpnewt.api.v1.EventsOuterClass.GetLabelIndicesInfoResponse.LabelIndexInfo.LabelIndexType;
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

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

class EventsClientImplTest {

  @Rule
  public final GrpcCleanupRule grpcCleanup = new GrpcCleanupRule();

  private EventsGrpc.EventsImplBase eventsService;

  private EventsClientImpl tested;
  private ProtoLabelAdapter adapter;

  @BeforeEach
  void setUp() throws IOException {
    eventsService = mock(EventsGrpc.EventsImplBase.class, Mockito.CALLS_REAL_METHODS);
    String name = InProcessServerBuilder.generateName();
    grpcCleanup.register(InProcessServerBuilder
        .forName(name).directExecutor().addService(eventsService).build().start());

    ManagedChannel channel = grpcCleanup.register(InProcessChannelBuilder.forName(name).directExecutor().build());

    tested = new EventsClientImpl(channel);

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
  void getAllDocuments() {
    doAnswer((Answer<Void>) invocation -> {
      StreamObserver<GetAllDocumentNamesResponse> observer = invocation.getArgument(1);
      observer.onNext(GetAllDocumentNamesResponse.newBuilder().addDocumentNames("foo")
          .addDocumentNames("bar").build());
      observer.onCompleted();
      return null;
    }).when(eventsService).getAllDocumentNames(any(), any());

    Collection<String> documents = tested.getAllDocuments("1");
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
        Collections.singletonList(Span.of(1, 5)), adapter);
    ArgumentCaptor<AddLabelsRequest> captor = ArgumentCaptor.forClass(AddLabelsRequest.class);
    verify(eventsService).addLabels(captor.capture(), any());
    verify(adapter).addToMessage(eq(Collections.singletonList(Span.of(1, 5))), any());
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
        .thenReturn(NewtEvents.standardLabelIndex(Collections.singletonList(Span.of(0, 5))));
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

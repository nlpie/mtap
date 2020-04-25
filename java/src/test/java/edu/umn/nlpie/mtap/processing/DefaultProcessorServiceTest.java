package edu.umn.nlpie.mtap.processing;

import com.google.protobuf.Struct;
import com.google.protobuf.Value;
import com.google.protobuf.util.Durations;
import edu.umn.nlpie.mtap.api.v1.Processing;
import edu.umn.nlpie.mtap.api.v1.ProcessorGrpc;
import edu.umn.nlpie.mtap.common.JsonObject;
import edu.umn.nlpie.mtap.common.JsonObjectImpl;
import edu.umn.nlpie.mtap.discovery.DiscoveryMechanism;
import edu.umn.nlpie.mtap.discovery.ServiceInfo;
import io.grpc.ManagedChannel;
import io.grpc.Server;
import io.grpc.StatusRuntimeException;
import io.grpc.inprocess.InProcessChannelBuilder;
import io.grpc.inprocess.InProcessServerBuilder;
import io.grpc.testing.GrpcCleanupRule;
import org.junit.Rule;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import java.io.IOException;
import java.net.UnknownHostException;
import java.time.Duration;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ExecutionException;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class DefaultProcessorServiceTest {
  @Rule
  public final GrpcCleanupRule grpcCleanup = new GrpcCleanupRule();

  @Mock
  ProcessorRunner mockRunner;

  @Mock
  TimingService mockTimingService;

  @Mock
  DiscoveryMechanism mockDiscoveryMechanism;

  @Mock
  HealthService mockHealthService;

  String processorId = "processorId";

  String uniqueServiceId = "uniqueServiceId";

  private String name;

  @BeforeEach
  void setUp() {
    MockitoAnnotations.initMocks(this);
  }

  @Test
  void testLifecycleWithRegistration() throws UnknownHostException {
    DefaultProcessorService sut = createProcessorService(true);

    sut.started(8888);
    ArgumentCaptor<ServiceInfo> captor = ArgumentCaptor.forClass(ServiceInfo.class);
    verify(mockDiscoveryMechanism).register(captor.capture());
    ServiceInfo value = captor.getValue();
    assertEquals("processorId", value.getName());
    assertEquals("uniqueServiceId", value.getIdentifier());

    sut.close();

    ArgumentCaptor<ServiceInfo> deCaptor = ArgumentCaptor.forClass(ServiceInfo.class);
    verify(mockDiscoveryMechanism).deregister(deCaptor.capture());
    ServiceInfo deInfo = deCaptor.getValue();
    assertEquals("uniqueServiceId", deInfo.getIdentifier());
  }

  @Test
  void testProcess() throws IOException, InterruptedException {
    DefaultProcessorService processorService = createProcessorService(false);
    createServer(processorService).start();
    ProcessorGrpc.ProcessorBlockingStub stub = createStub();

    HashMap<String, List<String>> createdIndices = new HashMap<>();
    createdIndices.put("plaintext", Arrays.asList("indexOne", "indexTwo"));
    HashMap<String, Duration> times = new HashMap<>();
    times.put("process_method", Duration.ofNanos(30));
    JsonObjectImpl resultObject = JsonObjectImpl.newBuilder().setProperty("result", true).build();
    ProcessingResult result = new ProcessingResult(createdIndices, times, resultObject);
    when(mockRunner.process(eq("1"), any(JsonObject.class))).thenReturn(result);

    Processing.ProcessResponse response = stub.process(Processing.ProcessRequest.newBuilder()
        .setEventId("1")
        .setParams(Struct.newBuilder().putFields("test", Value.newBuilder().setBoolValue(true).build()).build())
        .build()
    );

    verify(mockTimingService).addTime("process_method", 30);

    ArgumentCaptor<JsonObject> jsonCaptor = ArgumentCaptor.forClass(JsonObjectImpl.class);
    verify(mockRunner).process(eq("1"), jsonCaptor.capture());
    JsonObject params = jsonCaptor.getValue();
    assertTrue(params.getBooleanValue("test"));
    assertEquals(1, response.getTimingInfoCount());
    assertEquals(30, response.getTimingInfoOrThrow("process_method").getNanos());
    List<Processing.CreatedIndex> createdIndicesResponse = response.getCreatedIndicesList();
    assertEquals(2, createdIndicesResponse.size());
    assertTrue(createdIndicesResponse.contains(Processing.CreatedIndex.newBuilder().setDocumentName("plaintext").setIndexName("indexOne").build()));
    assertTrue(createdIndicesResponse.contains(Processing.CreatedIndex.newBuilder().setDocumentName("plaintext").setIndexName("indexTwo").build()));
    assertTrue(response.getResult().getFieldsOrThrow("result").getBoolValue());
  }

  @Test
  void processFailure() throws IOException, InterruptedException {
    DefaultProcessorService processorService = createProcessorService(false);
    createServer(processorService).start();
    ProcessorGrpc.ProcessorBlockingStub stub = createStub();

    when(mockRunner.process(eq("1"), any(JsonObjectImpl.class))).thenThrow(new IllegalStateException("foo"));

    StatusRuntimeException exception = assertThrows(StatusRuntimeException.class,
        () -> stub.process(Processing.ProcessRequest.newBuilder()
            .setEventId("1")
            .setParams(Struct.newBuilder()
                .putFields("test", Value.newBuilder().setBoolValue(true).build()).build())
            .build()
        ));
    assertEquals("INTERNAL: java.lang.IllegalStateException: foo", exception.getMessage());
  }

  @Test
  void getInfo() throws IOException {
    DefaultProcessorService processorService = createProcessorService(false);
    createServer(processorService).start();
    ProcessorGrpc.ProcessorBlockingStub stub = createStub();

    Map<String, Object> metadata = new HashMap<>();
    metadata.put("name", "test-processor");
    metadata.put("description", "desc.");
    metadata.put("entry_point", "foo");
    when(mockRunner.getProcessorMeta()).thenReturn(metadata);

    Processing.GetInfoResponse response = stub.getInfo(
        Processing.GetInfoRequest.newBuilder().setProcessorId("processorId").build()
    );

    JsonObjectImpl jsonObject = JsonObjectImpl.newBuilder().copyStruct(response.getMetadata())
        .build();
    assertEquals("test-processor", jsonObject.getStringValue("name"));
    assertEquals("desc.", jsonObject.getStringValue("description"));
    assertEquals("foo", jsonObject.getStringValue("entry_point"));
  }

  @Test
  void getStats() throws IOException, InterruptedException, ExecutionException {
    DefaultProcessorService processorService = createProcessorService(false);
    createServer(processorService).start();
    ProcessorGrpc.ProcessorBlockingStub stub = createStub();

    HashMap<String, List<String>> createdIndices = new HashMap<>();
    createdIndices.put("plaintext", Arrays.asList("indexOne", "indexTwo"));
    HashMap<String, Duration> times = new HashMap<>();
    times.put("processorId:process_method", Duration.ofNanos(30));
    JsonObjectImpl resultObject = JsonObjectImpl.newBuilder().setProperty("result", true).build();
    ProcessingResult result = new ProcessingResult(createdIndices, times, resultObject);
    when(mockRunner.process(eq("1"), any(JsonObjectImpl.class))).thenReturn(result);

    stub.process(Processing.ProcessRequest.newBuilder()
        .setEventId("1")
        .setParams(Struct.newBuilder().putFields("test", Value.newBuilder().setBoolValue(true).build()).build())
        .build()
    );

    Map<String, Processing.TimerStats> timerStatsMap = new HashMap<>();
    timerStatsMap.put("processorId:process_method", Processing.TimerStats.newBuilder().setMax(Durations.fromNanos(30)).build());
    when(mockTimingService.getTimerStats()).thenReturn(timerStatsMap);

    Processing.GetStatsResponse stats = stub.getStats(Processing.GetStatsRequest.newBuilder()
        .setProcessorId("id").build());

    assertEquals(1, stats.getProcessed());
    assertEquals(0, stats.getFailures());
    assertEquals(30, stats.getTimingStatsOrThrow("processorId:process_method").getMax().getNanos());
  }

  private DefaultProcessorService createProcessorService(boolean register) {
    return new DefaultProcessorService(
        mockRunner,
        mockTimingService,
        mockDiscoveryMechanism,
        mockHealthService,
        processorId,
        uniqueServiceId,
        register
    );
  }

  private Server createServer(DefaultProcessorService processorService) throws IOException {
    name = InProcessServerBuilder.generateName();
    return grpcCleanup.register(InProcessServerBuilder.forName(name).directExecutor().addService(processorService).build());
  }

  private ProcessorGrpc.ProcessorBlockingStub createStub() {
    ManagedChannel channel = grpcCleanup.register(
        InProcessChannelBuilder.forName(name).directExecutor().build()
    );
    return ProcessorGrpc.newBlockingStub(channel);
  }
}
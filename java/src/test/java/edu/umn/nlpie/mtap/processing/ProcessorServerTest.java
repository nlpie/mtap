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

package edu.umn.nlpie.mtap.processing;

import com.google.protobuf.Struct;
import com.google.protobuf.Value;
import com.google.protobuf.util.Durations;
import edu.umn.nlpie.mtap.model.Document;
import edu.umn.nlpie.mtap.api.v1.Processing;
import edu.umn.nlpie.mtap.api.v1.ProcessorGrpc;
import edu.umn.nlpie.mtap.common.JsonObject;
import edu.umn.nlpie.mtap.common.JsonObjectBuilder;
import edu.umn.nlpie.mtap.common.JsonObjectImpl;
import edu.umn.nlpie.mtap.discovery.DiscoveryMechanism;
import edu.umn.nlpie.mtap.discovery.ServiceInfo;
import io.grpc.ManagedChannel;
import io.grpc.Server;
import io.grpc.StatusRuntimeException;
import io.grpc.inprocess.InProcessChannelBuilder;
import io.grpc.inprocess.InProcessServerBuilder;
import io.grpc.testing.GrpcCleanupRule;
import org.jetbrains.annotations.NotNull;
import org.junit.Rule;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

import java.io.IOException;
import java.time.Duration;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.*;

class ProcessorServerTest {
  @Rule
  public final GrpcCleanupRule grpcCleanup = new GrpcCleanupRule();

  private Runner mockRunner;
  private DiscoveryMechanism mockDiscoveryMechanism;

  private ProcessorServer tested;
  private String name;

  @BeforeEach
  void setUp() {
    mockRunner = mock(Runner.class);
    when(mockRunner.getProcessorId()).thenReturn("processorId");
    when(mockRunner.getProcessorMeta()).thenReturn(TestProcessor.class.getAnnotation(Processor.class));
    mockDiscoveryMechanism = mock(DiscoveryMechanism.class);
    name = InProcessServerBuilder.generateName();
    InProcessServerBuilder serverBuilder = InProcessServerBuilder.forName(name).directExecutor();
    tested = new ProcessorServer(
        serverBuilder,
        mockRunner,
        "uniqueServiceId",
        true,
        mockDiscoveryMechanism,
        Executors.newSingleThreadExecutor()
    );
  }

  @Test
  void testLifecycle() throws IOException, InterruptedException {
    tested.start();
    Server server = grpcCleanup.register(tested.getServer());
    assertEquals(-1, tested.getPort());
    tested.shutdown();
    tested.blockUntilShutdown();
    assertTrue(server.isShutdown());
    ArgumentCaptor<ServiceInfo> captor = ArgumentCaptor.forClass(ServiceInfo.class);
    verify(mockDiscoveryMechanism).register(captor.capture());
    ServiceInfo value = captor.getValue();
    assertEquals("processorId", value.getName());
    assertEquals("uniqueServiceId", value.getIdentifier());
    ArgumentCaptor<ServiceInfo> deCaptor = ArgumentCaptor.forClass(ServiceInfo.class);
    verify(mockDiscoveryMechanism).deregister(deCaptor.capture());
    ServiceInfo deInfo = deCaptor.getValue();
    assertEquals("uniqueServiceId", value.getIdentifier());
  }

  @Test
  void testProcess() throws IOException, InterruptedException {
    tested.start();
    grpcCleanup.register(tested.getServer());

    HashMap<String, List<String>> createdIndices = new HashMap<>();
    createdIndices.put("plaintext", Arrays.asList("indexOne", "indexTwo"));
    HashMap<String, Duration> times = new HashMap<>();
    times.put("process_method", Duration.ofNanos(30));
    JsonObjectImpl resultObject = JsonObjectImpl.newBuilder().setProperty("result", true).build();
    ProcessingResult result = new ProcessingResult(createdIndices, times, resultObject);
    when(mockRunner.process(eq("1"), any(JsonObject.class))).thenReturn(result);

    ManagedChannel channel = grpcCleanup.register(InProcessChannelBuilder.forName(name).directExecutor().build());
    ProcessorGrpc.ProcessorBlockingStub stub = ProcessorGrpc.newBlockingStub(
        channel
    );

    Processing.ProcessResponse response = stub.process(Processing.ProcessRequest.newBuilder()
        .setEventId("1")
        .setParams(Struct.newBuilder().putFields("test", Value.newBuilder().setBoolValue(true).build()).build())
        .build()
    );

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
    channel.shutdown();
    channel.awaitTermination(10, TimeUnit.SECONDS);
  }

  @Test
  void processFailure() throws IOException, InterruptedException {
    when(mockRunner.process(eq("1"), any(JsonObjectImpl.class))).thenThrow(new IllegalStateException("foo"));

    tested.start();
    grpcCleanup.register(tested.getServer());

    ManagedChannel channel = grpcCleanup.register(InProcessChannelBuilder.forName(name).directExecutor().build());
    try {

      ProcessorGrpc.ProcessorBlockingStub stub = ProcessorGrpc.newBlockingStub(
          channel
      );
      StatusRuntimeException exception = assertThrows(StatusRuntimeException.class, () -> stub.process(Processing.ProcessRequest.newBuilder()
          .setEventId("1")
          .setParams(Struct.newBuilder().putFields("test", Value.newBuilder().setBoolValue(true).build()).build())
          .build()
      ));
      assertEquals("INTERNAL: java.lang.IllegalStateException: foo", exception.getMessage());
    } finally {
      channel.shutdownNow();
      channel.awaitTermination(10, TimeUnit.SECONDS);
    }
    channel.shutdown();
    channel.awaitTermination(10, TimeUnit.SECONDS);
  }

  @Test
  void getInfo() throws IOException, InterruptedException {
    tested.start();
    grpcCleanup.register(tested.getServer());

    ManagedChannel channel = grpcCleanup.register(
        InProcessChannelBuilder.forName(name).directExecutor().build()
    );
    ProcessorGrpc.ProcessorBlockingStub stub = ProcessorGrpc.newBlockingStub(channel);

    Processing.GetInfoResponse response = stub.getInfo(
        Processing.GetInfoRequest.newBuilder().setProcessorId("processorId").build()
    );
    assertEquals("test-processor", response.getName());
    assertEquals("desc.", response.getDescription());
    assertEquals("foo", response.getEntryPoint());
    assertEquals("java", response.getLanguage());
    assertEquals("a_param", response.getParameters(0).getName());
    assertEquals("param desc.", response.getParameters(0).getDescription());
    assertEquals("bool", response.getParameters(0).getDataType());
    assertTrue(response.getParameters(0).getRequired());
    assertEquals("b_param", response.getParameters(1).getName());
    assertEquals("str", response.getParameters(1).getDataType());
    assertFalse(response.getParameters(1).getRequired());
    assertEquals("input_index", response.getInputs(0).getName());
    assertEquals("desc", response.getInputs(0).getDescription());
    assertEquals("prop_a", response.getInputs(0).getProperties(0).getName());
    assertEquals("prop desc.", response.getInputs(0).getProperties(0).getDescription());
    assertEquals("blah", response.getInputs(0).getProperties(0).getDataType());
    assertTrue(response.getInputs(0).getProperties(0).getNullable());
    assertEquals("prop_b", response.getInputs(0).getProperties(1).getName());
    assertEquals("str", response.getInputs(0).getProperties(1).getDataType());
    assertFalse(response.getInputs(0).getProperties(1).getNullable());


    channel.shutdown();
    channel.awaitTermination(10, TimeUnit.SECONDS);
  }

  @Test
  void getStats() throws IOException, InterruptedException {
    tested.start();
    grpcCleanup.register(tested.getServer());

    HashMap<String, List<String>> createdIndices = new HashMap<>();
    createdIndices.put("plaintext", Arrays.asList("indexOne", "indexTwo"));
    HashMap<String, Duration> times = new HashMap<>();
    times.put("processorId:process_method", Duration.ofNanos(30));
    JsonObjectImpl resultObject = JsonObjectImpl.newBuilder().setProperty("result", true).build();
    ProcessingResult result = new ProcessingResult(createdIndices, times, resultObject);
    when(mockRunner.process(eq("1"), any(JsonObjectImpl.class))).thenReturn(result);

    ManagedChannel channel = grpcCleanup.register(
        InProcessChannelBuilder.forName(name).directExecutor().build()
    );
    ProcessorGrpc.ProcessorBlockingStub stub = ProcessorGrpc.newBlockingStub(channel);

    stub.process(Processing.ProcessRequest.newBuilder()
        .setEventId("1")
        .setParams(Struct.newBuilder().putFields("test", Value.newBuilder().setBoolValue(true).build()).build())
        .build()
    );

    Processing.GetStatsResponse stats = stub.getStats(Processing.GetStatsRequest.newBuilder()
        .setProcessorId("id").build());

    assertEquals(1, stats.getProcessed());
    assertEquals(0, stats.getFailures());
    assertEquals(30, stats.getTimingStatsOrThrow("processorId:process_method").getMax().getNanos());

    channel.shutdown();
    channel.awaitTermination(10, TimeUnit.SECONDS);
  }

  @Test
  void testAddTime() throws ExecutionException, InterruptedException {
    for (Integer i : Arrays.asList(3156, 1289, 3778, 1526, 3882, 4625, 3214, 1426, 2982, 874, 1226,
        2774, 1013, 4719, 3393, 2622, 1010, 1011, 2941, 3775, 3467, 4547,
        4176, 703, 606, 1485, 137, 2640, 2052, 138, 4748, 3350, 4939,
        1838, 3423, 807, 1827, 4502, 2335, 4822, 399, 1742, 248, 2662,
        1935, 931, 595, 2740, 891, 738)) {
      tested.addTime("test", i);
    }
    Map<String, Processing.TimerStats> timerStats = tested.getTimerStats();
    Processing.TimerStats stats = timerStats.get("test");
    assertNotNull(stats);
    assertEquals(1450, Durations.toNanos(stats.getStd()));
    assertEquals(137, Durations.toNanos(stats.getMin()));
    assertEquals(4939, Durations.toNanos(stats.getMax()));
    assertEquals(2333, Durations.toNanos(stats.getMean()));
    assertEquals(116659, Durations.toNanos(stats.getSum()));
  }

  @Processor(
      value = "test-processor",
      description = "desc.",
      entryPoint = "foo",
      parameters = {
          @ParameterDescription(
              name = "a_param",
              description = "param desc.",
              dataType = "bool",
              required = true
          ),
          @ParameterDescription(
              name = "b_param",
              dataType = "str"
          )
      },
      inputs = {
          @LabelIndexDescription(
              name = "input_index",
              description = "desc",
              properties = {
                  @PropertyDescription(name = "prop_a", description = "prop desc.", dataType = "blah", nullable = true),
                  @PropertyDescription(name = "prop_b", dataType = "str")
              }
          )
      },
      outputs = {
          @LabelIndexDescription(
              name = "output_index",
              nameFromParameter = "output_index",
              description = "Occurrences of the specified word."
          )
      }
  )
  private static class TestProcessor extends DocumentProcessor {
    @Override
    protected void process(@NotNull Document document, @NotNull JsonObject params, @NotNull JsonObjectBuilder result) {

    }
  }
}

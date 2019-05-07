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

package edu.umn.nlpnewt.internal.processing;

import com.google.protobuf.Struct;
import com.google.protobuf.Value;
import edu.umn.nlpnewt.JsonObject;
import edu.umn.nlpnewt.JsonObjectImpl;
import edu.umn.nlpnewt.api.v1.Processing;
import edu.umn.nlpnewt.api.v1.ProcessorGrpc;
import edu.umn.nlpnewt.internal.services.ServiceInfo;
import edu.umn.nlpnewt.internal.services.ServiceLifecycle;
import edu.umn.nlpnewt.internal.timing.TimesCollector;
import io.grpc.StatusRuntimeException;
import io.grpc.inprocess.InProcessChannelBuilder;
import io.grpc.inprocess.InProcessServerBuilder;
import io.grpc.testing.GrpcCleanupRule;
import org.junit.Rule;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

import java.io.IOException;
import java.time.Duration;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;

import static edu.umn.nlpnewt.Newt.PROCESSOR_SERVICE_TAG;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

class ProcessorServiceImplTest {
  @Rule
  public final GrpcCleanupRule grpcCleanup = new GrpcCleanupRule();
  private ServiceLifecycle serviceLifecycle;
  private Runner runner;
  private TimesCollector timesCollector;
  private String uniqueServiceId;

  @BeforeEach
  void setUp() {
    serviceLifecycle = mock(ServiceLifecycle.class);
    runner = mock(Runner.class);
    timesCollector = mock(TimesCollector.class);
    uniqueServiceId = "uniqueServiceId";
  }

  public ProcessorService createProcessorService(boolean register) {
    return new ProcessorServiceImpl(serviceLifecycle, runner, timesCollector, uniqueServiceId,
        register);
  }

  @Test
  void testProcess() throws IOException {
    HashMap<String, List<String>> createdIndices = new HashMap<>();
    createdIndices.put("plaintext", Arrays.asList("indexOne", "indexTwo"));
    HashMap<String, Duration> times = new HashMap<>();
    times.put("process_method", Duration.ofNanos(30));
    JsonObjectImpl resultObject = JsonObjectImpl.newBuilder().setProperty("result", true).build();
    ProcessingResult result = new ProcessingResult(createdIndices, times, resultObject);
    when(runner.process(eq("1"), any(JsonObject.class))).thenReturn(result);

    ProcessorService service = createProcessorService(true);

    String name = InProcessServerBuilder.generateName();
    InProcessServerBuilder.forName(name).directExecutor().addService(service).build().start();

    ProcessorGrpc.ProcessorBlockingStub stub = ProcessorGrpc.newBlockingStub(
        grpcCleanup.register(InProcessChannelBuilder.forName(name).directExecutor().build())
    );

    Processing.ProcessResponse response = stub.process(Processing.ProcessRequest.newBuilder()
        .setEventId("1")
        .setParams(Struct.newBuilder().putFields("test", Value.newBuilder().setBoolValue(true).build()).build())
        .build()
    );

    ArgumentCaptor<JsonObject> jsonCaptor = ArgumentCaptor.forClass(JsonObjectImpl.class);
    verify(runner).process(eq("1"), jsonCaptor.capture());
    JsonObject params = jsonCaptor.getValue();
    assertTrue(params.getBooleanValue("test"));
    verify(timesCollector).addTime("process_method", 30);
    assertEquals(1, response.getTimingInfoCount());
    assertEquals(30, response.getTimingInfoOrThrow("process_method").getNanos());
    List<Processing.CreatedIndex> createdIndicesResponse = response.getCreatedIndicesList();
    assertEquals(2, createdIndicesResponse.size());
    assertTrue(createdIndicesResponse.contains(Processing.CreatedIndex.newBuilder().setDocumentName("plaintext").setIndexName("indexOne").build()));
    assertTrue(createdIndicesResponse.contains(Processing.CreatedIndex.newBuilder().setDocumentName("plaintext").setIndexName("indexTwo").build()));
    assertTrue(response.getResult().getFieldsOrThrow("result").getBoolValue());
  }

  @Test
  void processFailure() throws IOException {
    when(runner.process(eq("1"), any(JsonObjectImpl.class))).thenThrow(new IllegalStateException("foo"));

    ProcessorService service = createProcessorService(true);

    String name = InProcessServerBuilder.generateName();
    InProcessServerBuilder.forName(name).directExecutor().addService(service).build().start();

    ProcessorGrpc.ProcessorBlockingStub stub = ProcessorGrpc.newBlockingStub(
        grpcCleanup.register(InProcessChannelBuilder.forName(name).directExecutor().build())
    );

    StatusRuntimeException exception = assertThrows(StatusRuntimeException.class, () -> stub.process(Processing.ProcessRequest.newBuilder()
        .setEventId("1")
        .setParams(Struct.newBuilder().putFields("test", Value.newBuilder().setBoolValue(true).build()).build())
        .build()
    ));
    assertEquals("INTERNAL: java.lang.IllegalStateException: foo", exception.getMessage());
  }

  @Test
  void getInfo() throws IOException {
    ProcessorService service = createProcessorService(true);
    when(runner.getProcessorName()).thenReturn("name");
    when(runner.getProcessorId()).thenReturn("id");

    String name = InProcessServerBuilder.generateName();
    InProcessServerBuilder.forName(name).directExecutor().addService(service).build().start();

    ProcessorGrpc.ProcessorBlockingStub stub = ProcessorGrpc.newBlockingStub(
        grpcCleanup.register(InProcessChannelBuilder.forName(name).directExecutor().build())
    );

    Processing.GetInfoResponse response = stub.getInfo(Processing.GetInfoRequest.newBuilder().setProcessorId("id").build());
    assertEquals("name", response.getName());
  }

  @Test
  void getStats() throws IOException {
    HashMap<String, List<String>> createdIndices = new HashMap<>();
    createdIndices.put("plaintext", Arrays.asList("indexOne", "indexTwo"));
    HashMap<String, Duration> times = new HashMap<>();
    times.put("process_method", Duration.ofNanos(30));
    JsonObjectImpl resultObject = JsonObjectImpl.newBuilder().setProperty("result", true).build();
    ProcessingResult result = new ProcessingResult(createdIndices, times, resultObject);
    when(runner.process(eq("1"), any(JsonObjectImpl.class))).thenReturn(result);

    HashMap<String, Processing.TimerStats> timesMap = new HashMap<>();
    timesMap.put("test:process_method", Processing.TimerStats.newBuilder()
        .setMax(com.google.protobuf.Duration.newBuilder().setNanos(100).build()).build());
    when(timesCollector.getTimerStats()).thenReturn(timesMap);

    ProcessorService service = createProcessorService(true);

    String name = InProcessServerBuilder.generateName();
    InProcessServerBuilder.forName(name).directExecutor().addService(service).build().start();

    ProcessorGrpc.ProcessorBlockingStub stub = ProcessorGrpc.newBlockingStub(
        grpcCleanup.register(InProcessChannelBuilder.forName(name).directExecutor().build())
    );

    stub.process(Processing.ProcessRequest.newBuilder()
        .setEventId("1")
        .setParams(Struct.newBuilder().putFields("test", Value.newBuilder().setBoolValue(true).build()).build())
        .build()
    );

    Processing.GetStatsResponse stats = stub.getStats(Processing.GetStatsRequest.newBuilder()
        .setProcessorId("id").build());

    assertEquals(1, stats.getProcessed());
    assertEquals(0, stats.getFailures());
    assertEquals(100, stats.getTimingStatsOrThrow("test:process_method").getMax().getNanos());
  }

  @Test
  void startedServing() {
    when(runner.getProcessorId()).thenReturn("foo");

    ProcessorService service = createProcessorService(true);

    service.startedServing("localhost", 9090);

    ArgumentCaptor<ServiceInfo> serviceInfoCaptor = ArgumentCaptor.forClass(ServiceInfo.class);
    verify(serviceLifecycle).startedService(serviceInfoCaptor.capture());

    ServiceInfo serviceInfo = serviceInfoCaptor.getValue();
    assertEquals("localhost", serviceInfo.getAddress());
    assertEquals(9090, serviceInfo.getPort());
    assertEquals("uniqueServiceId", serviceInfo.getIdentifier());
    assertEquals("foo", serviceInfo.getName());
    assertEquals(Collections.singletonList(PROCESSOR_SERVICE_TAG), serviceInfo.getTags());
    assertTrue(serviceInfo.isRegister());
  }

  @Test
  void stoppedServing() {
    when(runner.getProcessorId()).thenReturn("foo");

    ProcessorService service = createProcessorService(true);

    service.stoppedServing();

    ArgumentCaptor<ServiceInfo> serviceInfoCaptor = ArgumentCaptor.forClass(ServiceInfo.class);
    verify(serviceLifecycle).stoppedService(serviceInfoCaptor.capture());

    ServiceInfo serviceInfo = serviceInfoCaptor.getValue();
    assertEquals("uniqueServiceId", serviceInfo.getIdentifier());
    assertEquals("foo", serviceInfo.getName());
    assertTrue(serviceInfo.isRegister());

    verify(runner).close();
  }
}

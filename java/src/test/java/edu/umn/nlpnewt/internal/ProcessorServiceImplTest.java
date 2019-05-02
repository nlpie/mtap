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

package edu.umn.nlpnewt.internal;

import com.google.protobuf.Struct;
import com.google.protobuf.Value;
import com.google.rpc.DebugInfo;
import edu.umn.nlpnewt.EventProcessor;
import edu.umn.nlpnewt.JsonObject;
import edu.umn.nlpnewt.NewtEvents;
import edu.umn.nlpnewt.ProcessorContextManager;
import edu.umn.nlpnewt.api.v1.Processing;
import edu.umn.nlpnewt.api.v1.ProcessorGrpc;
import io.grpc.Server;
import io.grpc.StatusRuntimeException;
import io.grpc.inprocess.InProcessChannelBuilder;
import io.grpc.inprocess.InProcessServerBuilder;
import io.grpc.protobuf.ProtoUtils;
import io.grpc.testing.GrpcCleanupRule;
import org.junit.Rule;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

import java.io.IOException;
import java.time.Duration;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;

import static edu.umn.nlpnewt.Newt.PROCESSOR_SERVICE_TAG;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

class ProcessorServiceImplTest {
  @Rule
  public final GrpcCleanupRule grpcCleanup = new GrpcCleanupRule();

  @Test
  void testProcess() throws IOException {
    ProcessorRunner runner = mock(ProcessorRunner.class);
    HashMap<String, List<String>> createdIndices = new HashMap<>();
    createdIndices.put("plaintext", Arrays.asList("indexOne", "indexTwo"));
    HashMap<String, Duration> times = new HashMap<>();
    times.put("process_method", Duration.ofNanos(30));
    JsonObject resultObject = JsonObject.newBuilder().setProperty("result", true).build();
    ProcessingResult result = new ProcessingResult(createdIndices, times, resultObject);
    when(runner.process(eq("1"), any(JsonObject.class))).thenReturn(result);

    RegistrationAndHealthManager rhManager = mock(RegistrationAndHealthManager.class);

    TimesCollector timesCollector = mock(TimesCollector.class);

    ProcessorServiceImpl service = new ProcessorServiceImpl(runner, rhManager, timesCollector);

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

    ArgumentCaptor<JsonObject> jsonCaptor = ArgumentCaptor.forClass(JsonObject.class);
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
    ProcessorRunner runner = mock(ProcessorRunner.class);
    when(runner.process(eq("1"), any(JsonObject.class))).thenThrow(new IllegalStateException("bluh"));

    RegistrationAndHealthManager rhManager = mock(RegistrationAndHealthManager.class);

    TimesCollector timesCollector = mock(TimesCollector.class);

    ProcessorServiceImpl service = new ProcessorServiceImpl(runner, rhManager, timesCollector);

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
    assertEquals("INTERNAL: java.lang.IllegalStateException: bluh", exception.getMessage());
  }

  @Test
  void getInfo() throws IOException {
    ProcessorRunner runner = mock(ProcessorRunner.class);
    when(runner.process(eq("1"), any(JsonObject.class))).thenThrow(new IllegalStateException("bluh"));

    RegistrationAndHealthManager rhManager = mock(RegistrationAndHealthManager.class);

    TimesCollector timesCollector = mock(TimesCollector.class);

    ProcessorServiceImpl service = new ProcessorServiceImpl(runner, rhManager, timesCollector);
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
    ProcessorRunner runner = mock(ProcessorRunner.class);
    HashMap<String, List<String>> createdIndices = new HashMap<>();
    createdIndices.put("plaintext", Arrays.asList("indexOne", "indexTwo"));
    HashMap<String, Duration> times = new HashMap<>();
    times.put("process_method", Duration.ofNanos(30));
    JsonObject resultObject = JsonObject.newBuilder().setProperty("result", true).build();
    ProcessingResult result = new ProcessingResult(createdIndices, times, resultObject);
    when(runner.process(eq("1"), any(JsonObject.class))).thenReturn(result);

    RegistrationAndHealthManager rhManager = mock(RegistrationAndHealthManager.class);

    TimesCollector timesCollector = mock(TimesCollector.class);
    HashMap<String, Processing.TimerStats> timesMap = new HashMap<>();
    timesMap.put("test:process_method", Processing.TimerStats.newBuilder()
        .setMax(com.google.protobuf.Duration.newBuilder().setNanos(100).build()).build());
    when(timesCollector.getTimerStats()).thenReturn(timesMap);

    ProcessorServiceImpl service = new ProcessorServiceImpl(runner, rhManager, timesCollector);

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
    ProcessorRunner runner = mock(ProcessorRunner.class);
    when(runner.getProcessorId()).thenReturn("foo");

    RegistrationAndHealthManager rhManager = mock(RegistrationAndHealthManager.class);

    TimesCollector timesCollector = mock(TimesCollector.class);

    ProcessorServiceImpl service = new ProcessorServiceImpl(runner, rhManager, timesCollector);

    service.startedServing("localhost", 9090);

    verify(rhManager).setHealthAddress("localhost");
    verify(rhManager).setHealthPort(9090);
    verify(rhManager).startedService("foo", PROCESSOR_SERVICE_TAG);
  }

  @Test
  void stoppedServing() {
    ProcessorRunner runner = mock(ProcessorRunner.class);
    when(runner.getProcessorId()).thenReturn("foo");

    RegistrationAndHealthManager rhManager = mock(RegistrationAndHealthManager.class);
    Runnable deregister = mock(Runnable.class);
    when(rhManager.startedService("foo", PROCESSOR_SERVICE_TAG)).thenReturn(deregister);

    TimesCollector timesCollector = mock(TimesCollector.class);

    ProcessorServiceImpl service = new ProcessorServiceImpl(runner, rhManager, timesCollector);

    service.startedServing("localhost", 9090);
    service.stoppedServing();

    verify(runner).close();
    verify(deregister).run();
  }
}

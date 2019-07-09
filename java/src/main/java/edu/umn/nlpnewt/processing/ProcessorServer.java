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

package edu.umn.nlpnewt.processing;

import com.google.protobuf.Struct;
import com.google.protobuf.util.Durations;
import com.google.rpc.DebugInfo;
import edu.umn.nlpnewt.api.v1.Processing;
import edu.umn.nlpnewt.api.v1.Processing.TimerStats;
import edu.umn.nlpnewt.api.v1.ProcessorGrpc;
import edu.umn.nlpnewt.common.JsonObjectImpl;
import edu.umn.nlpnewt.discovery.DiscoveryMechanism;
import edu.umn.nlpnewt.discovery.ServiceInfo;
import io.grpc.Metadata;
import io.grpc.Server;
import io.grpc.ServerBuilder;
import io.grpc.Status;
import io.grpc.health.v1.HealthCheckResponse;
import io.grpc.protobuf.ProtoUtils;
import io.grpc.services.HealthStatusManager;
import io.grpc.stub.StreamObserver;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.net.InetAddress;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Future;
import java.util.stream.Collectors;

import static edu.umn.nlpnewt.Newt.PROCESSOR_SERVICE_TAG;


/**
 * Responsible for running and hosting {@link EventProcessor} and {@link DocumentProcessor} classes.
 */
final class ProcessorServer implements edu.umn.nlpnewt.common.Server {
  private static final Logger logger = LoggerFactory.getLogger(ProcessorServer.class);
  private final Map<String, RunningVariance> timesMap = new HashMap<>();
  private final Runner runner;
  private final String uniqueServiceId;
  private final boolean register;
  private final DiscoveryMechanism discoveryMechanism;
  private final ExecutorService timingExecutor;

  private HealthStatusManager healthStatusManager = null;
  private Server server = null;
  private boolean running = false;

  ProcessorServer(ServerBuilder serverBuilder,
                  Runner runner,
                  String uniqueServiceId,
                  boolean register,
                  DiscoveryMechanism discoveryMechanism,
                  ExecutorService timingExecutor) {
    Servicer servicer = new Servicer();
    healthStatusManager = new HealthStatusManager();
    serverBuilder.addService(healthStatusManager.getHealthService());
    serverBuilder.addService(servicer);
    server = serverBuilder.build();
    this.runner = runner;
    this.uniqueServiceId = uniqueServiceId;
    this.register = register;
    this.discoveryMechanism = discoveryMechanism;
    this.timingExecutor = timingExecutor;
  }

  @Override
  public void start() throws IOException {
    if (running) {
      return;
    }
    running = true;
    server.start();
    int port = server.getPort();
    String processorId = runner.getProcessorId();
    healthStatusManager.setStatus(processorId, HealthCheckResponse.ServingStatus.SERVING);
    if (register) {
      InetAddress localHost = InetAddress.getLocalHost();
      ServiceInfo serviceInfo = new ServiceInfo(
          processorId,
          uniqueServiceId,
          localHost.getHostAddress(),
          port,
          Collections.singletonList(PROCESSOR_SERVICE_TAG)
      );
      discoveryMechanism.register(serviceInfo);
    }
    logger.info("Server started on port " + port);
    Runtime.getRuntime().addShutdownHook(new Thread(() -> {
      System.err.println("Shutting down processor server ");
      shutdown();
    }));
  }

  @Override
  public void shutdown() {
    if (!running) {
      return;
    }
    ServiceInfo serviceInfo = new ServiceInfo(
        runner.getProcessorId(),
        uniqueServiceId,
        null,
        -1,
        Collections.singletonList(PROCESSOR_SERVICE_TAG)
    );
    healthStatusManager.setStatus(serviceInfo.getName(), HealthCheckResponse.ServingStatus.NOT_SERVING);
    healthStatusManager.enterTerminalState();
    if (register) {
      discoveryMechanism.deregister(serviceInfo);
    }
    runner.close();
    server.shutdown();
    healthStatusManager = null;
    running = false;
  }

  @Override
  public void blockUntilShutdown() throws InterruptedException {
    server.awaitTermination();
  }

  @Override
  public int getPort() {
    return server.getPort();
  }

  @Override
  public boolean isRunning() {
    return running;
  }

  public Server getServer() {
    return server;
  }

  void addTime(String key, long nanos) {
    timingExecutor.submit(() -> {
      RunningVariance runningVariance = timesMap.computeIfAbsent(key,
          unused -> new RunningVariance());
      runningVariance.addTime(nanos);
    });
  }

  public Map<String, TimerStats> getTimerStats() throws InterruptedException, ExecutionException {
    Future<Map<String, TimerStats>> future = timingExecutor.submit(
        () -> timesMap.entrySet().stream()
            .map(e -> new AbstractMap.SimpleImmutableEntry<>(
                e.getKey(),
                e.getValue().createStats())
            )
            .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue))
    );
    return future.get();
  }

  private class Servicer extends ProcessorGrpc.ProcessorImplBase {

    private int processed = 0;
    private int failures = 0;

    @Override
    public void process(
        Processing.ProcessRequest request,
        StreamObserver<Processing.ProcessResponse> responseObserver
    ) {
      JsonObjectImpl params = JsonObjectImpl.newBuilder().copyStruct(request.getParams()).build();

      try {
        String eventID = request.getEventId();
        ProcessingResult result = runner.process(eventID, params);

        Processing.ProcessResponse.Builder responseBuilder = Processing.ProcessResponse.newBuilder()
            .setResult(result.getResult().copyToStruct(Struct.newBuilder()));
        for (Map.Entry<String, List<String>> entry : result.getCreatedIndices().entrySet()) {
          for (String indexName : entry.getValue()) {
            responseBuilder.addCreatedIndices(Processing.CreatedIndex.newBuilder()
                .setDocumentName(entry.getKey())
                .setIndexName(indexName)
                .build());
          }
        }
        for (Map.Entry<String, Duration> entry : result.getTimes().entrySet()) {
          long nanos = entry.getValue().toNanos();
          addTime(runner.getProcessorId() + ":" +entry.getKey(), nanos);
          responseBuilder.putTimingInfo(entry.getKey(), Durations.fromNanos(nanos));
        }
        responseObserver.onNext(responseBuilder.build());
        responseObserver.onCompleted();
        processed++;
      } catch (Throwable t) {
        Metadata trailers = new Metadata();
        Metadata.Key<DebugInfo> key = ProtoUtils.keyForProto(DebugInfo.getDefaultInstance());
        DebugInfo.Builder debugInfoBuilder = DebugInfo.newBuilder();
        for (StackTraceElement stackTraceElement : t.getStackTrace()) {
          debugInfoBuilder.addStackEntries(stackTraceElement.toString());
        }
        trailers.put(key, debugInfoBuilder.build());
        responseObserver.onError(Status.INTERNAL.withDescription(t.toString())
            .asRuntimeException(trailers));
        failures++;
      }
    }

    @Override
    public void getInfo(Processing.GetInfoRequest request,
                        StreamObserver<Processing.GetInfoResponse> responseObserver) {
      try {
        responseObserver.onNext(Processing.GetInfoResponse.newBuilder()
            .setName(runner.getProcessorName())
            .setIdentifier(runner.getProcessorId()).build());
        responseObserver.onCompleted();
      } catch (Throwable t) {
        responseObserver.onError(Status.INTERNAL.withDescription(t.toString())
            .withCause(t)
            .asRuntimeException());
      }
    }

    @Override
    public void getStats(Processing.GetStatsRequest request,
                         StreamObserver<Processing.GetStatsResponse> responseObserver) {
      try {
        Processing.GetStatsResponse.Builder builder = Processing.GetStatsResponse.newBuilder()
            .setProcessed(processed)
            .setFailures(failures);
        Map<String, TimerStats> timerStatsMap = getTimerStats();
        builder.putAllTimingStats(timerStatsMap);
        responseObserver.onNext(builder.build());
        responseObserver.onCompleted();
      } catch (Throwable t) {
        responseObserver.onError(Status.INTERNAL.withDescription(t.toString())
            .withCause(t)
            .asRuntimeException());
      }
    }
  }
}

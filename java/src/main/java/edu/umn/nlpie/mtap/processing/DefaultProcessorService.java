package edu.umn.nlpie.mtap.processing;

import com.google.protobuf.Struct;
import com.google.protobuf.util.Durations;
import com.google.rpc.DebugInfo;
import edu.umn.nlpie.mtap.Internal;
import edu.umn.nlpie.mtap.MTAP;
import edu.umn.nlpie.mtap.api.v1.Processing;
import edu.umn.nlpie.mtap.api.v1.ProcessorGrpc;
import edu.umn.nlpie.mtap.common.JsonObjectImpl;
import edu.umn.nlpie.mtap.discovery.DiscoveryMechanism;
import edu.umn.nlpie.mtap.discovery.ServiceInfo;
import edu.umn.nlpie.mtap.exc.FailedToConnectToEventsException;
import io.grpc.Metadata;
import io.grpc.Status;
import io.grpc.protobuf.ProtoUtils;
import io.grpc.stub.StreamObserver;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.net.UnknownHostException;
import java.time.Duration;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ExecutionException;

@Internal
public class DefaultProcessorService extends ProcessorGrpc.ProcessorImplBase implements ProcessorService {
  private static final Logger logger = LoggerFactory.getLogger(DefaultProcessorService.class);

  private final @NotNull ProcessorRunner runner;
  private final @NotNull TimingService timingService;
  private final @Nullable DiscoveryMechanism discoveryMechanism;
  private final @NotNull HealthService healthService;

  private final @NotNull String name;
  private final @NotNull String sid;

  private final @NotNull String host;

  private int processed = 0;
  private int failures = 0;
  private int port;

  public DefaultProcessorService(
      @NotNull ProcessorRunner runner,
      @NotNull TimingService timingService,
      @Nullable DiscoveryMechanism discoveryMechanism,
      @NotNull HealthService healthService,
      @Nullable String name,
      @Nullable String sid,
      @NotNull String host
  ) {
    this.runner = runner;
    this.timingService = timingService;
    this.discoveryMechanism = discoveryMechanism;
    this.healthService = healthService;
    this.name = name != null ? name : runner.getProcessor().getProcessorName();
    this.sid = sid != null ? sid : UUID.randomUUID().toString();
    this.host = host;
  }

  @Override
  public void started(int port) throws UnknownHostException {
    this.port = port;
    healthService.startedServing(name);
    if (discoveryMechanism != null) {
      ServiceInfo serviceInfo = new ServiceInfo(
          name,
          sid,
          host,
          port,
          Collections.singletonList(MTAP.PROCESSOR_SERVICE_TAG)
      );
      discoveryMechanism.register(serviceInfo);
    }
    logger.info("Server for processor_id: {} started on port: {}", name, port);
  }

  @Override
  public void process(
      Processing.ProcessRequest request,
      StreamObserver<Processing.ProcessResponse> responseObserver
  ) {
    JsonObjectImpl params = JsonObjectImpl.newBuilder().copyStruct(request.getParams()).build();

    String eventID = request.getEventId();
    String eventServiceInstanceId = request.getEventServiceInstanceId();
    try {
      ProcessingResult result = runner.process(eventID, eventServiceInstanceId, params);

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
        timingService.addTime(entry.getKey(), nanos);
        responseBuilder.putTimingInfo(entry.getKey(), Durations.fromNanos(nanos));
      }
      responseObserver.onNext(responseBuilder.build());
      responseObserver.onCompleted();
      processed++;
    } catch (FailedToConnectToEventsException e) {
      logger.error("Failed to connect to events service with address: {}", e.getAddress());
      responseObserver.onError(Status.INTERNAL.withCause(e).asRuntimeException());
    } catch (RuntimeException e) {
      logger.error("Exception during processing of event '{}'", eventID, e);
      Metadata trailers = new Metadata();
      Metadata.Key<DebugInfo> key = ProtoUtils.keyForProto(DebugInfo.getDefaultInstance());
      DebugInfo.Builder debugInfoBuilder = DebugInfo.newBuilder();
      for (StackTraceElement stackTraceElement : e.getStackTrace()) {
        debugInfoBuilder.addStackEntries(stackTraceElement.toString());
      }
      trailers.put(key, debugInfoBuilder.build());
      responseObserver.onError(Status.INTERNAL.withDescription(e.toString())
          .asRuntimeException(trailers));
      failures++;
    }
  }

  @Override
  public void getInfo(
      Processing.GetInfoRequest request,
      StreamObserver<Processing.GetInfoResponse> responseObserver
  ) {
    Map<String, Object> processorMeta = runner.getProcessorMeta();
    try {
      JsonObjectImpl.Builder jsonObjectBuilder = JsonObjectImpl.newBuilder();
      jsonObjectBuilder.putAll(processorMeta);
      JsonObjectImpl jsonObject = jsonObjectBuilder.build();

      Processing.GetInfoResponse.Builder builder = Processing.GetInfoResponse.newBuilder();
      jsonObject.copyToStruct(builder.getMetadataBuilder());
      responseObserver.onNext(builder.build());
      responseObserver.onCompleted();
    } catch (RuntimeException e) {
      responseObserver.onError(Status.INTERNAL.withDescription(e.toString())
          .withCause(e)
          .asRuntimeException());
    }
  }

  @Override
  public void getStats(
      Processing.GetStatsRequest request,
      StreamObserver<Processing.GetStatsResponse> responseObserver
  ) {
    try {
      Processing.GetStatsResponse.Builder builder = Processing.GetStatsResponse.newBuilder()
          .setProcessed(processed)
          .setFailures(failures);
      Map<String, Processing.TimerStats> timerStatsMap = timingService.getTimerStats();
      builder.putAllTimingStats(timerStatsMap);
      responseObserver.onNext(builder.build());
      responseObserver.onCompleted();
    } catch (RuntimeException | InterruptedException | ExecutionException e) {
      responseObserver.onError(Status.INTERNAL.withDescription(e.toString())
          .withCause(e)
          .asRuntimeException());
    }
  }

  @Override
  public void close() throws InterruptedException {
    System.out.println("Shutting down processor server with id: \"" + name + "\" on address: \"" + host + ":" + port + "\"");
    ServiceInfo serviceInfo = new ServiceInfo(
        name,
        sid,
        null,
        -1,
        Collections.singletonList(MTAP.PROCESSOR_SERVICE_TAG)
    );
    healthService.stoppedServing(name);
    if (discoveryMechanism != null) {
      discoveryMechanism.deregister(serviceInfo);
    }
    runner.close();
  }
}

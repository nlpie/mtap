package edu.umn.nlpie.mtap.processing;

import com.google.protobuf.Any;
import com.google.protobuf.Struct;
import com.google.protobuf.util.Durations;
import com.google.rpc.Code;
import com.google.rpc.DebugInfo;
import com.google.rpc.ErrorInfo;
import com.google.rpc.LocalizedMessage;
import edu.umn.nlpie.mtap.Internal;
import edu.umn.nlpie.mtap.api.v1.Processing;
import edu.umn.nlpie.mtap.api.v1.ProcessorGrpc;
import edu.umn.nlpie.mtap.common.JsonObjectImpl;
import edu.umn.nlpie.mtap.exc.FailedToConnectToEventsException;
import io.grpc.Status;
import io.grpc.protobuf.StatusProto;
import io.grpc.stub.StreamObserver;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ExecutionException;

@Internal
public class DefaultProcessorService extends ProcessorGrpc.ProcessorImplBase implements ProcessorService {
    private static final Logger logger = LoggerFactory.getLogger(DefaultProcessorService.class);

    private final @NotNull ProcessorRunner runner;
    private final @NotNull TimingService timingService;
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
            @NotNull HealthService healthService,
            @Nullable String name,
            @Nullable String sid,
            @NotNull String host
    ) {
        this.runner = runner;
        this.timingService = timingService;
        this.healthService = healthService;
        this.name = name != null ? name : runner.getProcessor().getProcessorName();
        this.sid = sid != null ? sid : UUID.randomUUID().toString();
        this.host = host;
    }

    @Override
    public void started(int port) {
        this.port = port;
        healthService.startedServing(name);
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
        logger.debug("{} received process request on event: ({}, {})", this.name, eventID, eventServiceInstanceId);
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
            String message = e.getMessage();
            responseObserver.onError(StatusProto.toStatusRuntimeException(buildStatus(e, message)));
        } catch (RuntimeException e) {
            logger.error("Exception during processing of event '{}'", eventID, e);
            String message = "An internal error occurred while attempting to process an Event. " +
                    "This is potentially a bug, contact the developer of the component.";
            responseObserver.onError(StatusProto.toStatusRuntimeException(buildStatus(e, message)));
            failures++;
        }
    }

    @NotNull
    private static com.google.rpc.Status buildStatus(Exception e, String message) {
        DebugInfo.Builder debugInfoBuilder = DebugInfo.newBuilder();
        for (StackTraceElement stackTraceElement : e.getStackTrace()) {
            debugInfoBuilder.addStackEntries(stackTraceElement.toString() + "\n");
        }
        return com.google.rpc.Status.newBuilder()
                .setCode(Code.UNKNOWN.getNumber())
                .setMessage("Internal error during processing.")
                .addDetails(Any.pack(ErrorInfo.newBuilder()
                        .setReason("PROCESSING_FAILURE")
                        .setDomain("mtap.nlpie.umn.edu")
                        .putMetadata("lang", "java")
                        .putMetadata("errorType", e.getClass().getCanonicalName())
                        .putMetadata("errorRepr", e.toString())
                        .build()))
                .addDetails(Any.pack(debugInfoBuilder.build()))
                .addDetails(Any.pack(LocalizedMessage.newBuilder()
                        .setLocale("en-US")
                        .setMessage(message)
                        .build()))
                .build();
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
        System.out.println("Shutting down processor server with name: \"" + name + "\" on address: \"" + host + ":" + port + "\"");
        runner.close();
    }
}

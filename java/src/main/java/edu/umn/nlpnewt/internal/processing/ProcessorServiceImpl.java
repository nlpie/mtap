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
import com.google.protobuf.util.Durations;
import com.google.rpc.DebugInfo;
import edu.umn.nlpnewt.Internal;
import edu.umn.nlpnewt.JsonObjectImpl;
import edu.umn.nlpnewt.api.v1.Processing;
import edu.umn.nlpnewt.api.v1.ProcessorGrpc;
import io.grpc.Metadata;
import io.grpc.Status;
import io.grpc.protobuf.ProtoUtils;
import io.grpc.stub.StreamObserver;

import java.time.Duration;
import java.util.List;
import java.util.Map;

import static edu.umn.nlpnewt.Newt.PROCESSOR_SERVICE_TAG;

@Internal
final class ProcessorServiceImpl extends ProcessorGrpc.ProcessorImplBase implements ProcessorService {
  private final TimesCollector timesCollector;
  private final ProcessorRunner runner;
  private final RegistrationAndHealthManager registrationAndHealthManager;

  private Runnable deregister = null;

  private int processed = 0;
  private int failures = 0;

  ProcessorServiceImpl(
      ProcessorRunner runner,
      RegistrationAndHealthManager registrationAndHealthManager,
      TimesCollector timesCollector
  ) {
    this.runner = runner;
    this.registrationAndHealthManager = registrationAndHealthManager;
    this.timesCollector = timesCollector;
  }

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
        timesCollector.addTime(entry.getKey(), nanos);
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
      builder.putAllTimingStats(timesCollector.getTimerStats());
      responseObserver.onNext(builder.build());
      responseObserver.onCompleted();
    } catch (Throwable t) {
      responseObserver.onError(Status.INTERNAL.withDescription(t.toString())
          .withCause(t)
          .asRuntimeException());
    }
  }

  @Override
  public void startedServing(String address, int port) {
    registrationAndHealthManager.setHealthAddress(address);
    registrationAndHealthManager.setHealthPort(port);
    deregister = registrationAndHealthManager.startedService(runner.getProcessorId(), PROCESSOR_SERVICE_TAG);
  }

  @Override
  public void stoppedServing() {
    if (deregister != null) {
      deregister.run();
    }
    runner.close();
  }
}

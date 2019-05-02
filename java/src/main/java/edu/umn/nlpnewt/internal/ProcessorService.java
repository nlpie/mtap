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

import com.google.protobuf.util.Durations;
import edu.umn.nlpnewt.*;
import edu.umn.nlpnewt.api.v1.Processing;
import edu.umn.nlpnewt.api.v1.ProcessorGrpc;
import io.grpc.Status;
import io.grpc.stub.StreamObserver;

import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.Set;

final class ProcessorService extends ProcessorGrpc.ProcessorImplBase {
  private final TimesCollector timesCollector;
  private final ProcessorRunner runner;

  private int processed = 0;
  private int failures = 0;

  ProcessorService(ProcessorRunner runner) {
    this.runner = runner;
    timesCollector = new TimesCollector();
  }

  @Override
  public void process(
      Processing.ProcessRequest request,
      StreamObserver<Processing.ProcessResponse> responseObserver
  ) {
    JsonObject params = JsonObject.newBuilder().copyStruct(request.getParams()).build();

    try {
      String eventID = request.getEventId();
      ProcessingResult result = runner.process(eventID, params);

      Processing.ProcessResponse.Builder responseBuilder = Processing.ProcessResponse.newBuilder();
      for (Map.Entry<String, List<String>> entry : event.getCreatedIndices().entrySet()) {
        for (String indexName : entry.getValue()) {
          responseBuilder.addCreatedIndices(Processing.CreatedIndex.newBuilder()
              .setDocumentName(entry.getKey())
              .setIndexName(indexName)
              .build());
        }
      }

      AbstractJsonObject resultObject = resultBuilder.build();
      AbstractJsonObject.copyJsonObjectToStruct(resultObject, responseBuilder.getResultBuilder());

      Set<Map.Entry<String, Duration>> entries = runner.getTimes().entrySet();
      for (Map.Entry<String, Duration> entry : entries) {
        long nanos = entry.getValue().toNanos();
        timesCollector.addTime(entry.getKey(), nanos);
        responseBuilder.putTimingInfo(entry.getKey(), Durations.fromNanos(nanos));
      }
      responseObserver.onNext(responseBuilder.build());
      responseObserver.onCompleted();
      processed++;
    } catch (Throwable t) {
      responseObserver.onError(Status.fromThrowable(t).asException());
      failures++;
    }
  }

  @Override
  public void getInfo(Processing.GetInfoRequest request,
                      StreamObserver<Processing.GetInfoResponse> responseObserver) {
    try {
      String name = runner.getProcessor()
          .getClass().getAnnotation(Processor.class).value();
      responseObserver.onNext(Processing.GetInfoResponse.newBuilder().setName(name)
          .setIdentifier(runner.getIdentifier()).build());
      responseObserver.onCompleted();
    } catch (Throwable t) {
      responseObserver.onError(t);
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
      responseObserver.onError(t);
    }
  }
}

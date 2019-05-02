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
import edu.umn.nlpnewt.Timer;
import edu.umn.nlpnewt.*;
import edu.umn.nlpnewt.api.v1.Processing;
import edu.umn.nlpnewt.api.v1.ProcessorGrpc;
import io.grpc.Status;
import io.grpc.stub.StreamObserver;

import java.io.Closeable;
import java.time.Duration;
import java.util.*;

final class ProcessorService extends ProcessorGrpc.ProcessorImplBase {
  private final TimesCollector timesCollector;
  private final ProcessorContextManager processorContext;

  private NewtEvents events = null;
  private AbstractEventProcessor processor = null;

  private int processed = 0;
  private int failures = 0;

  ProcessorService(ProcessorContextManager processorContext) {
    this.processorContext = processorContext;
    timesCollector = new TimesCollector();
  }

  @Override
  public void process(Processing.ProcessRequest request,
                      StreamObserver<Processing.ProcessResponse> responseObserver) {
    Processing.ProcessResponse.Builder responseBuilder = Processing.ProcessResponse.newBuilder();
    try (Closeable ignored = processorContext.enterContext()) {
      processorContext.enterContext();
      String eventID = request.getEventId();
      JsonObject.Builder resultBuilder = JsonObject.newBuilder();
      try (Event event = events.openEvent(eventID)) {
        JsonObject.Builder builder = JsonObject.newBuilder();
        AbstractJsonObject.copyStructToJsonObjectBuilder(request.getParams(), builder);
        JsonObject params = builder.build();
        Timer timer = processorContext.startTimer("process_method");
        processor.process(event, params, resultBuilder);
        timer.stop();
        for (Map.Entry<String, List<String>> entry : event.getCreatedIndices().entrySet()) {
          for (String indexName : entry.getValue()) {
            responseBuilder.addCreatedIndices(Processing.CreatedIndex.newBuilder()
                .setDocumentName(entry.getKey())
                .setIndexName(indexName)
                .build());
          }
        }
      }

      AbstractJsonObject resultObject = resultBuilder.build();
      AbstractJsonObject.copyJsonObjectToStruct(resultObject, responseBuilder.getResultBuilder());

      Set<Map.Entry<String, Duration>> entries = processorContext.getTimes().entrySet();
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
      String name = processor.getClass().getAnnotation(Processor.class).value();
      responseObserver.onNext(Processing.GetInfoResponse.newBuilder().setName(name)
          .setIdentifier(processorContext.getIdentifier()).build());
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

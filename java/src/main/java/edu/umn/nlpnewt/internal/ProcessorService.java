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
import io.grpc.health.v1.HealthCheckResponse;
import io.grpc.services.HealthStatusManager;
import io.grpc.stub.StreamObserver;

import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.Set;

import static edu.umn.nlpnewt.Newt.PROCESSOR_SERVICE_TAG;

class ProcessorService extends ProcessorGrpc.ProcessorImplBase {
  private final Class<? extends AbstractEventProcessor> processorClass;
  private final String eventsTarget;
  private final ProcessorContextManager contextManager;
  private final Config config;
  private final RegistrationManager registrationManager;

  private NewtEvents events = null;

  private AbstractEventProcessor processor;

  private String identifier;

  private Runnable deregister = null;
  private final HealthStatusManager healthStatusManager;

  ProcessorService(
      Config config,
      ProcessorServerOptions options
  ) {
    this.config = config;
    processorClass = options.getProcessorClass();
    eventsTarget = options.getEventsTarget();
    processor = options.getProcessor();
    identifier = options.getIdentifier();
    healthStatusManager = options.getHealthStatusManager();
    contextManager = new ProcessorContextManager(options.getIdentifier(),
        options.getHealthStatusManager());
    if (options.getRegister()) {
      registrationManager = RegistrationManager.create(config);
      registrationManager.setHealthAddress(options.getAddress());
    } else {
      registrationManager = null;
    }
  }

  void start(int port) {
    // instantiate processor if not provided.
    if (processor == null) {
      try {
        try {
          Constructor<? extends AbstractEventProcessor> constructor = processorClass.getConstructor(ProcessorContext.class);
          processor = constructor.newInstance(contextManager.getShim());
        } catch (NoSuchMethodException ignored) {
          // fall back to default constructor
          Constructor<? extends AbstractEventProcessor> constructor = processorClass.getConstructor();
          processor = constructor.newInstance();
        }
      } catch (NoSuchMethodException | IllegalAccessException | InstantiationException | InvocationTargetException e) {
        throw new IllegalStateException("Unable to instantiate processor.", e);
      }
    }

    // set identifier to default if not provided.
    if (identifier == null) {
      identifier = processor.getClass().getAnnotation(Processor.class).value();
    }

    // connect to events service
    if (events == null) {
      events = NewtEventsImpl.create(config, eventsTarget);
    }

    // set health status to serving
    healthStatusManager.setStatus(identifier, HealthCheckResponse.ServingStatus.SERVING);

    // register with registration
    if (registrationManager != null) {
      registrationManager.setHealthPort(port);
      deregister = registrationManager.registerService(identifier, PROCESSOR_SERVICE_TAG);
    }
  }

  void shutdown() {
    if (deregister != null) {
      deregister.run();
    }
    processor.shutdown();
  }

  @Override
  public void process(Processing.ProcessRequest request,
                      StreamObserver<Processing.ProcessResponse> responseObserver) {
    Processing.ProcessResponse.Builder responseBuilder = Processing.ProcessResponse.newBuilder();
    try (ProcessorContextManager.ProcessorThreadContext context = contextManager.enterContext()) {
      contextManager.enterContext();
      String eventID = request.getEventId();

      JsonObject.Builder resultBuilder = JsonObject.newBuilder();
      try (Event event = events.openEvent(eventID)) {
        JsonObject.Builder builder = JsonObject.newBuilder();
        AbstractJsonObject.copyStructToJsonObjectBuilder(request.getParams(), builder);
        JsonObject params = builder.build();
        Timer timer = context.startTimer("process_method");
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

      Set<Map.Entry<String, Duration>> entries = context.getTimes().entrySet();
      for (Map.Entry<String, Duration> entry : entries) {
        responseBuilder.putTimingInfo(entry.getKey(), Durations.fromNanos(entry.getValue().toNanos()));
      }
      responseObserver.onNext(responseBuilder.build());
      responseObserver.onCompleted();
    } catch (Throwable t) {
      responseObserver.onError(Status.fromThrowable(t).asException());
    }
  }

  @Override
  public void getInfo(Processing.GetInfoRequest request,
                      StreamObserver<Processing.GetInfoResponse> responseObserver) {
    try {
      String name = processor.getClass().getAnnotation(Processor.class).value();
      responseObserver.onNext(Processing.GetInfoResponse.newBuilder().setName(name).build());
      responseObserver.onCompleted();
    } catch (Throwable t) {
      responseObserver.onError(t);
    }
  }


}

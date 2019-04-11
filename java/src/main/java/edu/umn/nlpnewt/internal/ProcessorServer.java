/*
 * Copyright 2019 Regents of the University of Minnesota
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
import grpc.health.v1.HealthGrpc;
import io.grpc.Server;
import io.grpc.Status;
import io.grpc.netty.NettyServerBuilder;
import io.grpc.stub.StreamObserver;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.annotation.Nullable;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.net.Inet6Address;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.Set;

import static grpc.health.v1.HealthOuterClass.HealthCheckRequest;
import static grpc.health.v1.HealthOuterClass.HealthCheckResponse;
import static grpc.health.v1.HealthOuterClass.HealthCheckResponse.ServingStatus;
import static grpc.health.v1.HealthOuterClass.HealthCheckResponse.ServingStatus.NOT_SERVING;
import static grpc.health.v1.HealthOuterClass.HealthCheckResponse.ServingStatus.SERVING;

/**
 * A server that hosts {@link AbstractDocumentProcessor} and {@link AbstractEventProcessor}.
 *
 * This class is for internal use, users should either use the command line or
 * {@link Newt#createProcessorServer(ProcessorServerOptions)}.
 */
@Internal
final class ProcessorServer implements edu.umn.nlpnewt.Server {
  private static final Logger logger = LoggerFactory.getLogger(ProcessorServer.class);

  private final Server server;

  private final AbstractEventProcessor processor;

  private final ServiceRegister.RegistrationCalls register;

  private ProcessorServer(Server server,
                          AbstractEventProcessor processor,
                          @Nullable ServiceRegister.RegistrationCalls register) {
    this.server = server;
    this.processor = processor;
    this.register = register;
  }

  public static ProcessorServer create(Config config, ProcessorServerOptions options) {
    AbstractEventProcessor processor = null;
    try {
      Class<? extends AbstractEventProcessor> processorClass = options.getProcessorClass();
      if (processorClass != null) {
        processor = processorClass.getConstructor().newInstance();
      }
    } catch (InstantiationException | InvocationTargetException | NoSuchMethodException | IllegalAccessException e) {
      throw new IllegalStateException("Reflection failure trying to instantiate the processor class.", e);
    }

    if (processor == null) {
      processor = options.getProcessor();
    }

    if (processor == null) {
      throw new IllegalStateException("Processor was not defined.");
    }

    String identifier = options.getIdentifier();
    if (identifier == null) {
      identifier = processor.getClass().getAnnotation(Processor.class).value();
    }

    String eventsTarget = options.getEventsTarget();
    NewtEvents events = NewtInternal.createEvents(config, eventsTarget);
    ProcessorService service = new ProcessorService(processor, events, identifier);
    Server server = NettyServerBuilder.forAddress(new InetSocketAddress(options.getAddress(), options.getPort()))
        .addService(service)
        .addService(new ProcessorHealth(identifier, processor))
        .build();

    ServiceRegister.RegistrationCalls register = null;
    if (options.getRegister()) {
      ServiceRegister serviceRegister = ServiceRegister.getServiceRegister(config);
      register = serviceRegister.registerProcessorService(identifier);
    }

    return new ProcessorServer(server, processor, register);
  }

  @Override
  public void start() throws IOException {
    server.start();
    logger.info("Server started on port " + server.getPort());
    Runtime.getRuntime().addShutdownHook(new Thread(() -> {
      System.err.println("Shutting down processor server ");
      stop();
    }));
    if (register != null) {
      String address = null;
      int port = -1;
      List<? extends SocketAddress> sockets = server.getListenSockets();
      for (SocketAddress socket : sockets) {
        if (socket instanceof InetSocketAddress) {
          InetSocketAddress socketAddress = (InetSocketAddress) socket;
          InetAddress inetAddress = socketAddress.getAddress();
          if (inetAddress instanceof Inet6Address) {
            address = "[" + inetAddress.getHostAddress() + "]";
          } else {
            address = inetAddress.getHostAddress();
          }
          port = socketAddress.getPort();
        }
      }

      if (address == null) {
        throw new IllegalStateException("No address.");
      }

      register.register(address, port, "v1");
    }
  }

  @Override
  public void stop() {
    if (register != null) {
      register.deregister();
    }
    server.shutdown();
    try {
      processor.shutdown();
    } catch (Throwable t) {
      logger.error("Error while shutting down ");
    }
  }

  @Override
  public void blockUntilShutdown() throws InterruptedException {
    server.awaitTermination();
  }

  @Override
  public int getPort() {
    return server.getPort();
  }

  static class ProcessorService extends ProcessorGrpc.ProcessorImplBase {

    private final AbstractEventProcessor processor;

    private final NewtEvents documents;
    private final String identifier;

    ProcessorService(AbstractEventProcessor processor, NewtEvents documents, String identifier) {
      this.processor = processor;
      this.documents = documents;
      this.identifier = identifier;
    }

    @Override
    public void process(Processing.ProcessRequest request,
                        StreamObserver<Processing.ProcessResponse> responseObserver) {
      Processing.ProcessResponse.Builder responseBuilder = Processing.ProcessResponse.newBuilder();
      try (TimingInfoImpl timingInfo = TimingInfoImpl.getTimingInfo()) {
        timingInfo.activate(identifier);
        String eventID = request.getEventId();

        JsonObject.Builder resultBuilder = JsonObject.newBuilder();
        try (Event event = documents.openEvent(eventID)) {
          JsonObject.Builder builder = JsonObject.newBuilder();
          AbstractJsonObject.copyStructToJsonObjectBuilder(request.getParams(), builder);
          JsonObject params = builder.build();
          Timer timer = timingInfo.start("process_method");
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

        Set<Map.Entry<String, Duration>> entries = timingInfo.getTimes().entrySet();
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

  static class ProcessorHealth extends HealthGrpc.HealthImplBase {
    private final String identifier;

    private final AbstractEventProcessor processor;

    ProcessorHealth(String identifier, AbstractEventProcessor processor) {
      this.identifier = identifier;
      this.processor = processor;

    }

    @Override
    public void check(HealthCheckRequest request,
                      StreamObserver<HealthCheckResponse> responseObserver) {
      String service = request.getService();
      try {
        ServingStatus status;
        if ("".equals(service)) {
          status = SERVING;
        } else if (service.equals(identifier)) {
          status = processor.getServingStatus();
        } else {
          status = NOT_SERVING;
        }
        HealthCheckResponse response = HealthCheckResponse.newBuilder().setStatus(status).build();
        responseObserver.onNext(response);
        responseObserver.onCompleted();
      } catch (Throwable t) {
        responseObserver.onError(t);
      }
    }
  }
}

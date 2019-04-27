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

import edu.umn.nlpnewt.*;
import io.grpc.Server;
import io.grpc.health.v1.HealthCheckResponse;
import io.grpc.netty.NettyServerBuilder;
import io.grpc.services.HealthStatusManager;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.net.InetSocketAddress;

/**
 * A server that hosts {@link AbstractDocumentProcessor} and {@link AbstractEventProcessor}.
 * <p>
 * This class is for internal use, users should either use the command line or
 * {@link Newt#createProcessorServer(ProcessorServerOptions)}.
 */
@Internal
final class ProcessorServer implements edu.umn.nlpnewt.Server {
  private static final Logger logger = LoggerFactory.getLogger(ProcessorServer.class);

  private final Server server;
  private final ProcessorService service;

  private ProcessorServer(Server server, ProcessorService service) {
    this.server = server;
    this.service = service;
  }

  public static ProcessorServer create(Config config, ProcessorServerOptions options) {
    ProcessorService service = new ProcessorService(config, options);
    Server server = NettyServerBuilder.forAddress(new InetSocketAddress(options.getAddress(), options.getPort()))
        .addService(service)
        .addService(options.getHealthStatusManager().getHealthService())
        .build();

    return new ProcessorServer(server, service);
  }

  @Override
  public void start() throws IOException {
    server.start();
    service.register();
    logger.info("Server started on port " + server.getPort());
    Runtime.getRuntime().addShutdownHook(new Thread(() -> {
      System.err.println("Shutting down processor server ");
      shutdown();
    }));
  }

  @Override
  public void shutdown() {
    service.shutdown();
    server.shutdown();
  }

  @Override
  public void blockUntilShutdown() throws InterruptedException {
    server.awaitTermination();
  }

  @Override
  public int getPort() {
    return server.getPort();
  }

}

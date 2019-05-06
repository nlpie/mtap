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

import edu.umn.nlpnewt.*;
import io.grpc.Server;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;

/**
 * A server that hosts {@link DocumentProcessorBase} and {@link EventProcessor}.
 * <p>
 * This class is for internal use, users should either use the command line or
 * {@link Newt#createProcessorServer(ProcessorServerOptions)}.
 */
@Internal
final class ProcessorServer implements edu.umn.nlpnewt.Server {
  private static final Logger logger = LoggerFactory.getLogger(ProcessorServer.class);

  private final String address;
  private final Server server;
  private final ProcessorService service;

  private boolean running = false;

  ProcessorServer(
      String address,
      Server server,
      ProcessorService service
  ) {
    this.address = address;
    this.server = server;
    this.service = service;
  }

  @Override
  public void start() throws IOException {
    if (running) {
      return;
    }
    running = true;
    server.start();
    int port = server.getPort();
    service.startedServing(address, port);
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
    running = false;
    service.stoppedServing();
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

  String getAddress() {
    return address;
  }

  Server getServer() {
    return server;
  }

  ProcessorService getService() {
    return service;
  }
}

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

package edu.umn.nlpie.mtap.processing;

import io.grpc.Server;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;


/**
 * Responsible for running and hosting {@link EventProcessor} and {@link DocumentProcessor} classes.
 *
 * @see ProcessorServerOptions
 */
public final class ProcessorServer implements edu.umn.nlpie.mtap.common.Server {
  private static final Logger logger = LoggerFactory.getLogger(ProcessorServer.class);

  private final Server server;
  private final ProcessorService processorService;
  private boolean running = false;

  ProcessorServer(
      ProcessorService processorService,
      Server grpcServer
  ) {
    this.processorService = processorService;
    server = grpcServer;
  }

  @Override
  public void start() throws IOException {
    if (running) {
      return;
    }
    running = true;
    server.start();
    int port = server.getPort();
    processorService.started(port);
    Runtime.getRuntime().addShutdownHook(new Thread(this::shutdown));
  }

  @Override
  public void shutdown() {
    if (!running) {
      return;
    }
    processorService.close();
    server.shutdown();
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
}

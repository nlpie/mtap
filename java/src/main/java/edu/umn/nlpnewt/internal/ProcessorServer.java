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
import io.grpc.netty.NettyServerBuilder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.file.Path;
import java.nio.file.Paths;

/**
 * A server that hosts {@link AbstractDocumentProcessor} and {@link AbstractEventProcessor}.
 * <p>
 * This class is for internal use, users should either use the command line or
 * {@link Newt#createProcessorServer(ProcessorServerOptions)}.
 */
@Internal
final class ProcessorServer implements edu.umn.nlpnewt.Server {
  private static final Logger logger = LoggerFactory.getLogger(ProcessorServer.class);

  private final String address;
  private final Server server;
  private final ProcessorContextManager processorContext;

  ProcessorServer(
      String address,
      Server server,
      ProcessorContextManager processorContext
  ) {
    this.address = address;
    this.server = server;
    this.processorContext = processorContext;
  }

  static ProcessorServer create(Config config, ProcessorServerOptions options) throws IOException {
    Path configFile = options.getConfigFile();
    if (configFile != null) {
      Config updates = Config.loadConfig(configFile);
      config.update(updates);
    }
    RegistrationAndHealthManager rhManager = RegistrationAndHealthManagerImpl.create(
        config,
        options.getRegister()
    );
    ProcessorContextManager context = new ProcessorContextImpl(config, options, rhManager);
    ProcessorService service = new ProcessorService(context);
    String address = options.getAddress();
    InetSocketAddress socketAddress = new InetSocketAddress(address, options.getPort());
    Server server = NettyServerBuilder.forAddress(socketAddress)
        .addService(service)
        .addService(rhManager.getHealthService())
        .build();
    return new ProcessorServer(address, server, context);
  }

  @Override
  public void start() throws IOException {
    server.start();
    int port = server.getPort();
    processorContext.startedServing(address, port);
    logger.info("Server started on port " + port);
    Runtime.getRuntime().addShutdownHook(new Thread(() -> {
      System.err.println("Shutting down processor server ");
      shutdown();
    }));
  }

  @Override
  public void shutdown() {
    processorContext.stoppedServing();
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

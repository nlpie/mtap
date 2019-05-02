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

import edu.umn.nlpnewt.*;
import edu.umn.nlpnewt.api.v1.ProcessorGrpc;
import io.grpc.Server;
import io.grpc.internal.AbstractServerImplBuilder;
import io.grpc.netty.NettyServerBuilder;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.file.Path;

class InternalOptions extends ProcessorServerOptions {
  private RegistrationAndHealthManager registrationAndHealthManager = null;
  private Config config;
  private AbstractServerImplBuilder<?> serverBuilder = null;
  private NewtEvents events = null;
  private ProcessorGrpc.ProcessorImplBase processorService = null;
  private ProcessorContextManager contextManager;

  public InternalOptions(Config config) throws IOException {
    this.config = ConfigImpl.createByCopying(config);
    Path configFile = getConfigFile();
    if (configFile != null) {
      ConfigImpl updates = ConfigImpl.loadConfig(configFile);
      this.config.update(updates);
    }
  }

  public InternalOptions(
      Config config,
      ProcessorServerOptions processorServerOptions
  ) throws IOException {
    super(processorServerOptions);
    this.config = ConfigImpl.createByCopying(config);
    Path configFile = getConfigFile();
    if (configFile != null) {
      ConfigImpl updates = ConfigImpl.loadConfig(configFile);
      this.config.update(updates);
    }
  }

  public AbstractServerImplBuilder<?> getServerBuilder() {
    if (serverBuilder == null) {
      InetSocketAddress socketAddress = new InetSocketAddress(getAddress(), getPort());
      return NettyServerBuilder.forAddress(socketAddress);
    }
    return serverBuilder;
  }

  public void setServerBuilder(AbstractServerImplBuilder<?> serverBuilder) {
    this.serverBuilder = serverBuilder;
  }

  public ProcessorServerOptions withServerBuilder(AbstractServerImplBuilder<?> serverBuilder) {
    setServerBuilder(serverBuilder);
    return this;
  }

  public RegistrationAndHealthManager getRegistrationAndHealthManager() {
    if (registrationAndHealthManager == null) {
      return RegistrationAndHealthManagerImpl.create(
          config,
          getRegister()
      );
    }
    return registrationAndHealthManager;
  }

  public void setRegistrationAndHealthManager(RegistrationAndHealthManager registrationAndHealthManager) {
    this.registrationAndHealthManager = registrationAndHealthManager;
  }

  public Config getConfig() {
    return config;
  }

  public void setConfig(Config config) {
    this.config = config;
  }

  public ProcessorGrpc.ProcessorImplBase getProcessorService() {
    if (processorService == null) {
      processorService = new ProcessorService(getContextManager());
    }
    return processorService;
  }

  public void setProcessorService(ProcessorGrpc.ProcessorImplBase processorService) {
    this.processorService = processorService;
  }

  public void setEvents(NewtEvents events) {
    this.events = events;
  }

  public NewtEvents getEvents() {
    return events;
  }

  public ProcessorContextManager getContextManager() {
    if (contextManager == null) {
      contextManager = new ContextManager(this);
    }
    return contextManager;
  }

  public void setContextManager(ProcessorContextManager contextManager) {
    this.contextManager = contextManager;
  }

  public ProcessorServer createProcessorServer() {
    Server server = getServerBuilder()
        .addService(getProcessorService())
        .addService(getRegistrationAndHealthManager().getHealthService())
        .build();
    return new ProcessorServer(getAddress(), server, getContextManager());
  }

}

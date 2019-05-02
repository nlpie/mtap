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
import io.grpc.Server;
import io.grpc.internal.AbstractServerImplBuilder;
import io.grpc.netty.NettyServerBuilder;
import org.jetbrains.annotations.NotNull;

import java.io.IOException;
import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.net.InetSocketAddress;
import java.nio.file.Path;

/**
 * Performs dependency injection of the different processing components.
 */
class InternalOptions extends ProcessorServerOptions {
  private Config config;
  private RegistrationAndHealthManager registrationAndHealthManager = null;
  private AbstractServerImplBuilder<?> serverBuilder = null;
  private NewtEvents events = null;
  private ProcessorService processorService = null;
  private ProcessorContextManager contextManager = null;
  private ProcessorRunner processorRunner = null;
  private String processorName = null;
  private TimesCollector timesCollector = null;

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

  public ProcessorService getProcessorService() {
    if (processorService == null) {
      processorService = new ProcessorServiceImpl(
          getProcessorRunner(),
          getRegistrationAndHealthManager(),
          getTimesCollector()
      );
    }
    return processorService;
  }

  public void setProcessorService(ProcessorService processorService) {
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
      contextManager = new ProcessorContextManager(getIdentifier(), getEvents(), getRegistrationAndHealthManager());
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
    return new ProcessorServer(getAddress(), server, getProcessorService());
  }

  public String getIdentifier() {
    String identifier = super.getIdentifier();
    if (identifier != null) {
      return identifier;
    }
    identifier = getProcessorName();
    setIdentifier(identifier);
    return identifier;
  }

  @NotNull
  private String getProcessorName() {
    if (processorName != null) {
      return processorName;
    }
    EventProcessor processor = getProcessor();
    Class<? extends EventProcessor> processorClass = null;
    if (processor != null) {
      processorClass = processor.getClass();
    }
    if (processorClass == null) {
      processorClass = getProcessorClass();
    }
    if (processorClass == null) {
      throw new IllegalStateException("Requires either processor or processor class.");
    }
    processorName = processorClass.getAnnotation(Processor.class).value();
    return processorName;
  }

  public ProcessorRunner getProcessorRunner() {
    if (processorRunner == null) {
      EventProcessor processor = getProcessor();
      if (processor == null) {
        try {
          Class<? extends EventProcessor> processorClass = getProcessorClass();
          if (processorClass == null) {
            throw new IllegalStateException("Neither processor nor processorClass was set");
          }
          try {
            Constructor<? extends EventProcessor> constructor = processorClass.getConstructor(ProcessorContext.class);
            processor = constructor.newInstance(getContextManager().getContext());
          } catch (NoSuchMethodException ignored) {
            // fall back to default constructor
            Constructor<? extends EventProcessor> constructor = processorClass.getConstructor();
            processor = constructor.newInstance();
          }
        } catch (NoSuchMethodException | IllegalAccessException | InstantiationException | InvocationTargetException e) {
          throw new IllegalStateException("Unable to instantiate processor.", e);
        }
      }

      processorRunner = new ProcessorRunnerImpl(
          processor,
          getContextManager(),
          getEvents(),
          getProcessorName(),
          getIdentifier()
      );
    }
    return processorRunner;
  }

  public void setProcessorRunner(ProcessorRunner processorRunner) {
    this.processorRunner = processorRunner;
  }

  public void setProcessorName(String processorName) {
    this.processorName = processorName;
  }

  public TimesCollector getTimesCollector() {
    if (timesCollector == null) {
      timesCollector = new TimesCollectorImpl();
    }
    return timesCollector;
  }

  public void setTimesCollector(TimesCollector timesCollector) {
    this.timesCollector = timesCollector;
  }
}

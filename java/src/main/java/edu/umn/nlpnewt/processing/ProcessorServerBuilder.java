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
package edu.umn.nlpnewt.processing;

import edu.umn.nlpnewt.common.Config;
import edu.umn.nlpnewt.common.ConfigImpl;
import edu.umn.nlpnewt.discovery.DiscoveryMechanism;
import edu.umn.nlpnewt.model.EventsClient;
import edu.umn.nlpnewt.model.EventsClientBuilder;
import io.grpc.Server;
import io.grpc.ServerBuilder;
import io.grpc.services.HealthStatusManager;
import org.jetbrains.annotations.NotNull;

import java.util.concurrent.Executors;

/**
 * Builder for processor servers.
 */
public class ProcessorServerBuilder {
  private final EventProcessor processor;
  private final ProcessorServerOptions options;

  private Config config;

  private EventsClient eventsClient;

  private ServiceLifecycle serviceLifecycle = null;

  private DiscoveryMechanism discoveryMechanism = null;

  private TimesCollector timesCollector;

  public ProcessorServerBuilder(@NotNull EventProcessor eventProcessor,
                                @NotNull ProcessorServerOptions options) {
    processor = eventProcessor;
    this.options = options;
  }

  public static @NotNull ProcessorServerBuilder forProcessor(
      @NotNull EventProcessor eventProcessor,
      @NotNull ProcessorServerOptions options
  ) {
    return new ProcessorServerBuilder(eventProcessor, options);
  }

  public Config getConfig() {
    if (config == null) {
      config = ConfigImpl.loadConfigFromLocationOrDefaults(options.getConfigFile());
    }
    return config;
  }

  public void setConfig(@NotNull Config config) {
    this.config = config;
  }

  public @NotNull ProcessorServerBuilder withConfig(@NotNull Config config) {
    setConfig(config);
    return this;
  }

  public @NotNull EventsClient getEventsClient() {
    if (eventsClient == null) {
      eventsClient = EventsClientBuilder.newBuilder()
          .withConfig(getConfig())
          .withAddress(options.getEventsTarget())
          .build();
    }
    return eventsClient;
  }

  public void setEventsClient(@NotNull EventsClient eventsClient) {
    this.eventsClient = eventsClient;
  }

  public @NotNull ProcessorServerBuilder withEventsClient(@NotNull EventsClient eventsClient) {
    setEventsClient(eventsClient);
    return this;
  }

  public DiscoveryMechanism getDiscoveryMechanism() {
    if (discoveryMechanism == null) {

    }
    return discoveryMechanism;
  }

  public void setDiscoveryMechanism(DiscoveryMechanism discoveryMechanism) {
    this.discoveryMechanism = discoveryMechanism;
  }

  public ServiceLifecycle getServiceLifecycle() {
    if (serviceLifecycle != null) {
      serviceLifecycle = new ServiceLifecycleImpl(new HealthStatusManager(), getDiscoveryMechanism());
    }
    return serviceLifecycle;
  }

  public void setServiceLifecycle(ServiceLifecycle serviceLifecycle) {
    this.serviceLifecycle = serviceLifecycle;
  }

  public @NotNull ProcessorServerBuilder withDiscoveryMechanism(
      @NotNull DiscoveryMechanism discoveryMechanism
  ) {
    setDiscoveryMechanism(discoveryMechanism);
    return this;
  }

  public @NotNull TimesCollector getTimesCollector() {
    if (timesCollector == null) {
      timesCollector = new TimesCollectorImpl(Executors.newSingleThreadExecutor());
    }
    return timesCollector;
  }

  public void setTimesCollector(@NotNull TimesCollector timesCollector) {

    this.timesCollector = timesCollector;
  }

  public @NotNull ProcessorServerBuilder withTimesCollector(@NotNull TimesCollector timesCollector) {
    setTimesCollector(timesCollector);
    return this;
  }

  public ProcessorServer build() {
    return build(ServerBuilder.forPort(options.getPort()));
  }

  public ProcessorServer build(ServerBuilder serverBuilder) {
    String processorName = processor.getClass().getAnnotation(Processor.class).value();
    String processorId = options.getIdentifier();
    if (processorId == null) {
      processorId = processorName;
    }
    ContextManager contextManager = new ContextManagerImpl(
        getServiceLifecycle(),
        processorId
    );
    Runner runner = new RunnerImpl(
        processor,
        getEventsClient(),
        contextManager,
        processorName,
        processorId
    );
    ProcessorService service = new ProcessorServiceImpl(
        getServiceLifecycle(),
        runner,
        getTimesCollector(),
        options.getUniqueServiceId(),
        options.getRegister()
    );
    Server server = serverBuilder
        .addService(service)
        .addService(getServiceLifecycle().getHealthService())
        .build();
    return new ProcessorServer(options.getAddress(), server, service);
  }

}

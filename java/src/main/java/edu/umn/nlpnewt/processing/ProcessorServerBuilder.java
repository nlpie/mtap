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
import edu.umn.nlpnewt.discovery.Discovery;
import edu.umn.nlpnewt.discovery.DiscoveryMechanism;
import edu.umn.nlpnewt.model.EventsClient;
import edu.umn.nlpnewt.model.EventsClientBuilder;
import io.grpc.ServerBuilder;
import org.jetbrains.annotations.NotNull;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Builder for processor servers, performs dependency injection of all the various components
 * needed by the processor server.
 */
public class ProcessorServerBuilder {
  private final EventProcessor processor;
  private final ProcessorServerOptions options;

  private Config config = null;
  private EventsClient eventsClient = null;
  private DiscoveryMechanism discoveryMechanism = null;
  private ExecutorService timingExecutor = null;

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
      discoveryMechanism = Discovery.getDiscoveryMechanism(getConfig());
    }
    return discoveryMechanism;
  }

  public void setDiscoveryMechanism(DiscoveryMechanism discoveryMechanism) {
    this.discoveryMechanism = discoveryMechanism;
  }

  public @NotNull ProcessorServerBuilder withDiscoveryMechanism(
      @NotNull DiscoveryMechanism discoveryMechanism
  ) {
    setDiscoveryMechanism(discoveryMechanism);
    return this;
  }

  public ProcessorServerOptions getOptions() {
    return options;
  }

  public ExecutorService getTimingExecutor() {
    if (timingExecutor == null) {
      timingExecutor = Executors.newSingleThreadExecutor();
    }
    return timingExecutor;
  }

  public ProcessorServerBuilder setTimingExecutor(ExecutorService timingExecutor) {
    this.timingExecutor = timingExecutor;
    return this;
  }

  public ProcessorServer build() {
    return build(ServerBuilder.forPort(options.getPort()));
  }

  public ProcessorServer build(ServerBuilder serverBuilder) {
    Runner runner = RunnerImpl.forProcessor(processor)
        .withClient(getEventsClient())
        .withProcessorId(options.getIdentifier())
        .build();
    return new ProcessorServer(serverBuilder,
        runner,
        options.getUniqueServiceId(),
        options.getRegister(),
        getDiscoveryMechanism(),
        getTimingExecutor());
  }

}

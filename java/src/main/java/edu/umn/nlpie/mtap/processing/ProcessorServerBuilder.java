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

import edu.umn.nlpie.mtap.common.ConfigImpl;
import edu.umn.nlpie.mtap.model.EventsClient;
import edu.umn.nlpie.mtap.model.EventsClientBuilder;
import edu.umn.nlpie.mtap.common.Config;
import edu.umn.nlpie.mtap.discovery.Discovery;
import edu.umn.nlpie.mtap.discovery.DiscoveryMechanism;
import io.grpc.Server;
import io.grpc.ServerBuilder;
import io.grpc.services.HealthStatusManager;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

/**
 * @deprecated
 */
public class ProcessorServerBuilder {
  private final EventProcessor processor;
  private final ProcessorServerOptions options;

  private @Nullable Config config = null;
  private @Nullable EventsClient eventsClient = null;
  private @Nullable DiscoveryMechanism discoveryMechanism = null;
  private @Nullable TimingService timingService = null;
  private @Nullable HealthStatusManager healthStatusManager = null;

  public ProcessorServerBuilder(
      @NotNull EventProcessor eventProcessor,
      @NotNull ProcessorServerOptions options
  ) {
    processor = eventProcessor;
    this.options = options;
  }

  public static @NotNull ProcessorServerBuilder forProcessor(
      @NotNull EventProcessor processor,
      @NotNull ProcessorServerOptions options
  ) {
    return new ProcessorServerBuilder(processor, options);
  }

  public @Nullable Config getConfig() {
    return config;
  }

  public void setConfig(@Nullable Config config) {
    this.config = config;
  }

  public @NotNull ProcessorServerBuilder withConfig(@Nullable Config config) {
    this.config = config;
    return this;
  }

  public @Nullable EventsClient getEventsClient() {
    return eventsClient;
  }

  public void setEventsClient(@Nullable EventsClient eventsClient) {
    this.eventsClient = eventsClient;
  }

  public @NotNull ProcessorServerBuilder withEventsClient(@Nullable EventsClient eventsClient) {
    this.eventsClient = eventsClient;
    return this;
  }

  public @Nullable DiscoveryMechanism getDiscoveryMechanism() {
    return discoveryMechanism;
  }

  public void setDiscoveryMechanism(@NotNull DiscoveryMechanism discoveryMechanism) {
    this.discoveryMechanism = discoveryMechanism;
  }

  public @NotNull ProcessorServerBuilder withDiscoveryMechanism(
      @Nullable DiscoveryMechanism discoveryMechanism
  ) {
    this.discoveryMechanism = discoveryMechanism;
    return this;
  }

  public @NotNull ProcessorServerOptions getOptions() {
    return options;
  }

  public TimingService getTimingService() {
    if (timingService == null) {
      timingService = new DefaultTimingService();
    }
    return timingService;
  }

  public void setTimingService(@Nullable TimingService timingService) {
    this.timingService = timingService;
  }

  public @NotNull ProcessorServerBuilder withTimingService(@Nullable TimingService timingService) {
    this.timingService = timingService;
    return this;
  }

  public @Nullable HealthStatusManager getHealthStatusManager() {
    return healthStatusManager;
  }

  public void setHealthStatusManager(@Nullable HealthStatusManager healthStatusManager) {
    this.healthStatusManager = healthStatusManager;
  }

  public @NotNull ProcessorServerBuilder withHealthStatusManager(@Nullable HealthStatusManager healthStatusManager) {
    this.healthStatusManager = healthStatusManager;
    return this;
  }

  public @NotNull ProcessorServer build() {
    return build(null);
  }

  /**
   * Builds a processor server that can be used to host the processor using a grpc server builder.
   * The port specified by {@link ProcessorServerOptions#getPort()} will not be used and instead
   * the one already configured on the {@code serverBuilder} parameter will be used.
   *
   * @param serverBuilder The grpc server builder.
   * @return Processor server object.
   */
  public @NotNull ProcessorServer build(@Nullable ServerBuilder<?> serverBuilder) {
    return options.createServer(processor);
  }
}

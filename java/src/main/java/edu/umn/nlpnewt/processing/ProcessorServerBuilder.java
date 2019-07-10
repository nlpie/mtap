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
  private ExecutorService backgroundExecutor = null;

  public ProcessorServerBuilder(
      @NotNull EventProcessor eventProcessor,
      @NotNull ProcessorServerOptions options
  ) {
    processor = eventProcessor;
    this.options = options;
  }

  /**
   * Creates a new processor server builder.
   *
   * @param processor The event or document processor to host.
   * @param options   The runtime options for the server.
   *
   * @return A new processor server builder.
   */
  public static @NotNull ProcessorServerBuilder forProcessor(
      @NotNull EventProcessor processor,
      @NotNull ProcessorServerOptions options
  ) {
    return new ProcessorServerBuilder(processor, options);
  }

  /**
   * Gets the configuration that will be used for the processor server, loading from the location
   * specified in the options, or the default locations if the configuration has not been
   * previously set.
   *
   * @return A configuration object containing the system configuration.
   */
  public @NotNull Config getConfig() {
    if (config == null) {
      config = ConfigImpl.loadConfigFromLocationOrDefaults(options.getConfigFile());
    }
    return config;
  }

  /**
   * Setter for the configuration.
   *
   * @param config Configuration object.
   */
  public void setConfig(@NotNull Config config) {
    this.config = config;
  }

  /**
   * Fluent interface method for setting the configuration.
   *
   * @param config Configuration object.
   *
   * @return this builder.
   */
  public @NotNull ProcessorServerBuilder withConfig(@NotNull Config config) {
    this.config = config;
    return this;
  }

  /**
   * Returns the event client for interacting with the events service,
   * if it has not been set one will be created.
   *
   * @return Events client object.
   */
  public @NotNull EventsClient getEventsClient() {
    if (eventsClient == null) {
      eventsClient = EventsClientBuilder.newBuilder()
          .withAddress(options.getEventsTarget())
          .withConfig(getConfig())
          .withDiscoveryMechanism(getDiscoveryMechanism())
          .build();
    }
    return eventsClient;
  }

  /**
   * Sets the events client that will be used by the framework to retrieve events and documents for
   * the processor.
   *
   * @param eventsClient The events client.
   */
  public void setEventsClient(@NotNull EventsClient eventsClient) {
    this.eventsClient = eventsClient;
  }

  /**
   * Sets the events client that will be used by the framework to retrieve events and documents for
   * the processor.
   *
   * @param eventsClient The events client.
   *
   * @return this builder.
   */
  public @NotNull ProcessorServerBuilder withEventsClient(@NotNull EventsClient eventsClient) {
    this.eventsClient = eventsClient;
    return this;
  }

  /**
   * Gets the discovery mechanism to be used by the framework if needed to register the processor
   * or discover the events service.
   *
   * @return The discovery mechanism object.
   */
  public @NotNull DiscoveryMechanism getDiscoveryMechanism() {
    if (discoveryMechanism == null) {
      discoveryMechanism = Discovery.getDiscoveryMechanism(getConfig());
    }
    return discoveryMechanism;
  }

  /**
   * Gets the discovery mechanism to be used by the framework if needed to register the processor
   * or discover the events service.
   *
   * @param discoveryMechanism The discovery mechanism object.
   */
  public void setDiscoveryMechanism(@NotNull DiscoveryMechanism discoveryMechanism) {
    this.discoveryMechanism = discoveryMechanism;
  }

  /**
   * Gets the discovery mechanism to be used by the framework if needed to register the processor
   * or discover the events service.
   *
   * @param discoveryMechanism The discovery mechanism object.
   *
   * @return this builder.
   */
  public @NotNull ProcessorServerBuilder withDiscoveryMechanism(
      @NotNull DiscoveryMechanism discoveryMechanism
  ) {
    this.discoveryMechanism = discoveryMechanism;
    return this;
  }

  /**
   * Gets the command-line processor options passed during creation of this builder.
   *
   * @return options object.
   */
  public @NotNull ProcessorServerOptions getOptions() {
    return options;
  }

  /**
   * Gets the executor service that will be used for background tasks like timing. If one has not
   * been created {@link Executors#newSingleThreadExecutor()} will be used.
   *
   * @return An executor service for background tasks.
   */
  public @NotNull ExecutorService getBackgroundExecutor() {
    if (backgroundExecutor == null) {
      backgroundExecutor = Executors.newSingleThreadExecutor();
    }
    return backgroundExecutor;
  }

  /**
   * Sets the executor service that will be used for background tasks like timing.
   *
   * @param executorService An executor service for background tasks.
   */
  public void setBackgroundExecutor(@NotNull ExecutorService executorService) {
    this.backgroundExecutor = executorService;
  }

  /**
   * Sets the executor service that will be used for background tasks like timing.
   *
   * @param executorService An executor service for background tasks.
   *
   * @return this builder.
   */
  public @NotNull ProcessorServerBuilder withBackgroundExecutor(
      @NotNull ExecutorService executorService
  ) {
    this.backgroundExecutor = executorService;
    return this;
  }

  /**
   * Builds a processor server that can be used to host the processor on the port specified by
   * {@link ProcessorServerOptions#getPort()}.
   *
   * @return Processor server object.
   */
  public @NotNull ProcessorServer build() {
    return build(ServerBuilder.forPort(options.getPort()));
  }

  /**
   * Builds a processor server that can be used to host the processor using a grpc server builder.
   * The port specified by {@link ProcessorServerOptions#getPort()} will not be used and instead
   * the one already configured on the {@code serverBuilder} parameter will be used.
   *
   * @param serverBuilder The grpc server builder.
   * @return Processor server object.
   */
  public @NotNull ProcessorServer build(@NotNull ServerBuilder serverBuilder) {
    Runner runner = LocalRunner.forProcessor(processor)
        .withClient(getEventsClient())
        .withProcessorId(options.getIdentifier())
        .build();
    return new ProcessorServer(serverBuilder,
        runner,
        options.getUniqueServiceId(),
        options.getRegister(),
        getDiscoveryMechanism(),
        getBackgroundExecutor());
  }

}

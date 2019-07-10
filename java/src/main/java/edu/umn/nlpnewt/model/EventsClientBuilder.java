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

package edu.umn.nlpnewt.model;

import edu.umn.nlpnewt.common.Config;
import edu.umn.nlpnewt.common.ConfigImpl;
import edu.umn.nlpnewt.discovery.Discovery;
import edu.umn.nlpnewt.discovery.DiscoveryMechanism;
import io.grpc.ManagedChannelBuilder;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.function.Consumer;

import static edu.umn.nlpnewt.Newt.EVENTS_SERVICE_NAME;

/**
 * Builder for an events client which can be used to manipulate
 */
public class EventsClientBuilder {
  private Config config;

  private @Nullable String address;

  private DiscoveryMechanism discoveryMechanism;

  public static @NotNull EventsClientBuilder newBuilder() {
    return new EventsClientBuilder();
  }

  public @NotNull Config getConfig() {
    if (config == null) {
      config = ConfigImpl.loadFromDefaultLocations();
    }
    return config;
  }

  public void setConfig(Config config) {
    this.config = config;
  }

  public @NotNull EventsClientBuilder withConfig(@NotNull Config config) {
    setConfig(config);
    return this;
  }

  public @Nullable String getAddress() {
    return address;
  }

  public void setAddress(@Nullable String address) {
    this.address = address;
  }

  public @NotNull EventsClientBuilder withAddress(@Nullable String address) {
    this.address = address;
    return this;
  }

  /**
   * Gets the discovery mechanism to be used by the framework if needed to discover the events
   * service.
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
   * Gets the discovery mechanism to be used by the framework if needed to discover the events
   * service.
   *
   * @param discoveryMechanism The discovery mechanism object.
   */
  public void setDiscoveryMechanism(@NotNull DiscoveryMechanism discoveryMechanism) {
    this.discoveryMechanism = discoveryMechanism;
  }

  /**
   * Gets the discovery mechanism to be used by the framework if needed to discover the events
   * service.
   *
   * @param discoveryMechanism The discovery mechanism object.
   *
   * @return this builder.
   */
  public @NotNull EventsClientBuilder withDiscoveryMechanism(
      @NotNull DiscoveryMechanism discoveryMechanism
  ) {
    this.discoveryMechanism = discoveryMechanism;
    return this;
  }

  private void setNameResolver(ManagedChannelBuilder builder) {
    builder.nameResolverFactory(getDiscoveryMechanism().getNameResolverFactory());
  }

  /**
   * Creates an events client, allowing control of how the channel is set up.
   *
   * @param configureChannel A consumer which is responsible for configuring the grpc channel.
   *
   * @return Events client object.
   */
  public @NotNull EventsClient build(@NotNull Consumer<ManagedChannelBuilder> configureChannel) {
    String target = this.address;
    if (target == null) {
      target = getDiscoveryMechanism().getServiceTarget(EVENTS_SERVICE_NAME, "v1");
      configureChannel = ((Consumer<ManagedChannelBuilder>) this::setNameResolver)
          .andThen(configureChannel);
    }
    ManagedChannelBuilder<?> channelBuilder = ManagedChannelBuilder.forTarget(target);
    configureChannel.accept(channelBuilder);
    return new EventsClient(channelBuilder.build());
  }

  /**
   * Creates an event client with {@link ManagedChannelBuilder#usePlaintext()} enabled for the
   * grpc channel.
   *
   * @return Events client.
   */
  public @NotNull EventsClient build() {
    return build(ManagedChannelBuilder::usePlaintext);
  }
}

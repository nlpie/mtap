/*
 * Copyright 2021 Regents of the University of Minnesota.
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

import edu.umn.nlpie.mtap.MTAP;
import edu.umn.nlpie.mtap.common.Config;
import edu.umn.nlpie.mtap.discovery.Discovery;
import edu.umn.nlpie.mtap.discovery.DiscoveryMechanism;
import edu.umn.nlpie.mtap.model.ChannelFactory;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;

import java.util.concurrent.TimeUnit;

public class StandardChannelFactory implements ChannelFactory {
  private final Config config;
  private boolean nameResolverAdded = false;
  private Object nameResolverAddedMutex = new Object();

  public StandardChannelFactory(Config config) {
    this.config = config;
  }

  @Override
  public ManagedChannel createChannel(String address) {
    ManagedChannel eventsChannel;
    ManagedChannelBuilder<?> builder;
    if (address == null) {
      DiscoveryMechanism discoveryMechanism = Discovery.getDiscoveryMechanism(config);
      discoveryMechanism.initializeNameResolution();
      String target = discoveryMechanism.getServiceTarget(MTAP.EVENTS_SERVICE_NAME);
      builder = ManagedChannelBuilder.forTarget(target);
    } else {
      builder = ManagedChannelBuilder.forTarget(address);
    }
    Integer maxInboundMessageSize = config.getIntegerValue("grpc.events_options.grpc.max_receive_message_length");
    if (maxInboundMessageSize != null) {
      builder.maxInboundMessageSize(maxInboundMessageSize);
    }
    Integer keepAliveTime = config.getIntegerValue("grpc.events_options.grpc.keepalive_time_ms");
    if (keepAliveTime != null) {
      builder.keepAliveTime(keepAliveTime, TimeUnit.MILLISECONDS);
    }
    Integer keepAliveTimeout = config.getIntegerValue("grpc.events_options.grpc.keepalive_timeout_ms");
    if (keepAliveTimeout != null) {
      builder.keepAliveTimeout(keepAliveTimeout, TimeUnit.MILLISECONDS);
    }
    Boolean permitKeepAliveWithoutCalls = config.getBooleanValue("grpc.events_options.grpc.permit_keepalive_without_calls");
    if (permitKeepAliveWithoutCalls != null) {
      builder.keepAliveWithoutCalls(permitKeepAliveWithoutCalls);
    }
    eventsChannel = builder.usePlaintext().build();
    return eventsChannel;
  }
}

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

public class StandardChannelFactory implements ChannelFactory {
  private final Config config;

  public StandardChannelFactory(Config config) {
    this.config = config;
  }

  @Override
  public ManagedChannel createChannel(String address) {
    ManagedChannel eventsChannel;
    ManagedChannelBuilder<?> channelBuilder;
    if (address == null) {
      DiscoveryMechanism discoveryMechanism = Discovery.getDiscoveryMechanism(config);
      String target = discoveryMechanism.getServiceTarget(MTAP.EVENTS_SERVICE_NAME);
      channelBuilder = ManagedChannelBuilder.forTarget(target)
          .nameResolverFactory(discoveryMechanism.getNameResolverFactory());
    } else {
      channelBuilder = ManagedChannelBuilder.forTarget(address);
    }
    channelBuilder.maxInboundMessageSize(config.getIntegerValue("grpc.java_events_channel_options.maxInboundMessageSize"));
    eventsChannel = channelBuilder.usePlaintext().build();
    return eventsChannel;
  }
}

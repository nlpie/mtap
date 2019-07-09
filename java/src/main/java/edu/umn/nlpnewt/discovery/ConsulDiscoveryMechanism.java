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

package edu.umn.nlpnewt.discovery;

import com.orbitz.consul.AgentClient;
import com.orbitz.consul.Consul;
import com.orbitz.consul.model.agent.ImmutableRegCheck;
import com.orbitz.consul.model.agent.ImmutableRegistration;
import edu.umn.nlpnewt.common.Config;
import edu.umn.nlpnewt.processing.ConsulNameResolver;
import io.grpc.NameResolver;

import java.net.MalformedURLException;
import java.net.URL;
import java.util.List;

public class ConsulDiscoveryMechanism implements DiscoveryMechanism {
  private final String host;
  private final int port;
  private AgentClient agent = null;

  ConsulDiscoveryMechanism(Config config) {
    host = config.getStringValue("consul.host");
    port = config.getIntegerValue("consul.port");
  }

  public AgentClient getAgent() {
    if (agent == null) {
      try {
        this.agent = Consul.builder()
            .withUrl(new URL("http", host, port, ""))
            .build().agentClient();
      } catch (MalformedURLException e) {
        throw new IllegalStateException(e);
      }
    }
    return agent;
  }

  @Override
  public String getServiceTarget(String serviceName, String... tags) {
    StringBuilder sb = new StringBuilder("consul://")
        .append(host)
        .append(":")
        .append(port)
        .append("/")
        .append(serviceName);
    if (tags != null && tags.length > 0) {
      for (String tag : tags) {
        sb.append("/").append(tag);
      }
    }
    return sb.toString();
  }

  @Override
  public void register(ServiceInfo serviceInfo) {
    ImmutableRegCheck grpcCheck = ImmutableRegCheck.builder()
        .interval("10s")
        .grpc(serviceInfo.getAddress() + ":" + serviceInfo.getPort() + "/" + serviceInfo.getName())
        .status("passing")
        .build();
    List<String> tags = serviceInfo.getTags();
    ImmutableRegistration registration = ImmutableRegistration.builder()
        .address("")
        .name(serviceInfo.getName())
        .id(serviceInfo.getIdentifier())
        .port(serviceInfo.getPort())
        .check(grpcCheck)
        .addTags(tags.toArray(new String[0]))
        .build();
    getAgent().register(registration);
  }

  @Override
  public void deregister(ServiceInfo serviceInfo) {
    getAgent().deregister(serviceInfo.getIdentifier());
  }

  @Override
  public NameResolver.Factory getNameResolverFactory() {
    return new ConsulNameResolver.Factory();
  }
}

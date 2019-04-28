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
package edu.umn.nlpnewt.internal;

import com.google.common.net.HostAndPort;
import com.orbitz.consul.AgentClient;
import com.orbitz.consul.Consul;
import com.orbitz.consul.model.agent.ImmutableRegCheck;
import com.orbitz.consul.model.agent.ImmutableRegistration;
import edu.umn.nlpnewt.Config;
import edu.umn.nlpnewt.Internal;
import edu.umn.nlpnewt.Newt;

import java.util.UUID;
import java.util.concurrent.Callable;

/**
 * Internal code to do service registration magic.
 */
@Internal
abstract class RegistrationManager {

  protected String address;
  protected int port;

  static RegistrationManager create(Config config) {
    if ("consul".equals(config.getStringValue("discovery"))) {
      return new ConsulRegistrationManager(config);
    } else {
      throw new IllegalArgumentException("Unrecognized discovery mechanism");
    }
  }

  public void setHealthAddress(String address) {
    this.address = address;
  }

  public void setHealthPort(int port) {
    this.port = port;
  }

  abstract Runnable registerService(String identifier, String... tags);

  static final class ConsulRegistrationManager extends RegistrationManager {

    private final AgentClient agent;

    ConsulRegistrationManager(Config config) {
      String host = config.getStringValue("consul.host");
      int port = config.getIntegerValue("consul.port");
      HostAndPort hostAndPort = HostAndPort.fromHost(host).withDefaultPort(port);
      Consul consul = Consul.builder().withHostAndPort(hostAndPort).build();
      agent = consul.agentClient();
    }

    Runnable registerService(String identifier, String... tags) {
      String uuid = UUID.randomUUID().toString();
      ImmutableRegCheck grpcCheck = ImmutableRegCheck.builder()
          .interval("10s")
          .grpc(address + ":" + port)
          .status("passing")
          .build();
      ImmutableRegistration registration = ImmutableRegistration.builder()
          .address("")
          .id(uuid)
          .name(identifier)
          .port(port)
          .check(grpcCheck)
          .addTags(tags)
          .build();
      agent.register(registration);

      return () -> agent.deregister(uuid);
    }
  }

  static abstract class RegistrationCalls {
    public abstract void register(String identifier);

    public abstract void deregister();
  }
}

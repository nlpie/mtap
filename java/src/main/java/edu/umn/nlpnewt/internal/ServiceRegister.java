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

/**
 * Internal code to do service registration magic.
 */
@Internal
abstract class ServiceRegister {
  static ServiceRegister getServiceRegister(Config config) {
    if ("consul".equals(config.getStringValue("discovery"))) {
      return new ConsulServiceRegister(config);
    } else {
      throw new IllegalArgumentException("Unrecognized discovery mechanism");
    }
  }

  abstract RegistrationCalls registerProcessorService(String identifier);

  static final class ConsulServiceRegister extends ServiceRegister {

    private final AgentClient agent;

    ConsulServiceRegister(Config config) {
      String host = config.getStringValue("consul.host");
      int port = config.getIntegerValue("consul.port");
      HostAndPort hostAndPort = HostAndPort.fromHost(host).withDefaultPort(port);
      Consul consul = Consul.builder().withHostAndPort(hostAndPort).build();
      agent = consul.agentClient();
    }

    @Override
    RegistrationCalls registerProcessorService(String identifier) {

      return new RegistrationCalls() {
        private final UUID uuid = UUID.randomUUID();

        @Override
        public void register(String address, int port, String version) {
          ImmutableRegCheck grpcCheck = ImmutableRegCheck.builder()
              .interval("10s")
              .grpc(address + ":" + port)
              .status("passing")
              .build();
          ImmutableRegistration registration = ImmutableRegistration.builder()
              .address("")
              .id(uuid.toString())
              .name(identifier)
              .port(port)
              .check(grpcCheck)
              .addTags(Newt.PROCESSOR_SERVICE_TAG)
              .build();
          agent.register(registration);
        }

        @Override
        public void deregister() {
          agent.deregister(uuid.toString());
        }
      };
    }
  }

  static abstract class RegistrationCalls {
    public abstract void register(String address, int port, String version);

    public abstract void deregister();
  }
}

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
import io.grpc.BindableService;
import io.grpc.health.v1.HealthCheckResponse;
import io.grpc.services.HealthStatusManager;

import java.util.UUID;

/**
 * Internal code to do service registration magic.
 */
@Internal
abstract class RegistrationAndHealthManagerImpl implements RegistrationAndHealthManager {
  private final HealthStatusManager healthStatusManager = new HealthStatusManager();

  protected String address;
  protected int port;

  static RegistrationAndHealthManager create(Config config, boolean register) {
    if (register) {
      if ("consul".equals(config.getStringValue("discovery"))) {
        return new ConsulRegistration(config);
      } else {
        throw new IllegalArgumentException("Unrecognized discovery mechanism");
      }
    }
    return new NoRegistration();
  }

  @Override
  public void setHealthAddress(String address) {
    this.address = address;
  }

  @Override
  public void setHealthPort(int port) {
    this.port = port;
  }

  @Override
  public Runnable startedService(String processor_id, String... tags) {
    String uuid = UUID.randomUUID().toString();
    healthStatusManager.setStatus(processor_id, HealthCheckResponse.ServingStatus.SERVING);
    registerService(uuid, processor_id, tags);
    return () -> {
      healthStatusManager.setStatus(processor_id, HealthCheckResponse.ServingStatus.NOT_SERVING);
      deregisterService(uuid);
    };
  }

  protected abstract void registerService(String identifier,
                                          String processor_id,
                                          String... tags);

  protected abstract void deregisterService(String identifier);

  @Override
  public BindableService getHealthService() {
    return healthStatusManager.getHealthService();
  }

  @Override
  public void enterTerminalState() {
    healthStatusManager.enterTerminalState();
  }

  @Override
  public void setStatus(String service, HealthCheckResponse.ServingStatus status) {
    healthStatusManager.setStatus(service, status);
  }

  static final class ConsulRegistration extends RegistrationAndHealthManagerImpl {
    private final AgentClient agent;

    ConsulRegistration(Config config) {
      String host = config.getStringValue("consul.host");
      int port = config.getIntegerValue("consul.port");
      HostAndPort hostAndPort = HostAndPort.fromHost(host).withDefaultPort(port);
      Consul consul = Consul.builder().withHostAndPort(hostAndPort).build();
      agent = consul.agentClient();
    }

    @Override
    protected void registerService(String identifier, String processor_id, String... tags) {
      ImmutableRegCheck grpcCheck = ImmutableRegCheck.builder()
          .interval("10s")
          .grpc(address + ":" + port + "/" + processor_id)
          .status("passing")
          .build();
      ImmutableRegistration registration = ImmutableRegistration.builder()
          .address("")
          .id(identifier)
          .name(processor_id)
          .port(port)
          .check(grpcCheck)
          .addTags(tags)
          .build();
      agent.register(registration);
    }

    @Override
    protected void deregisterService(String identifier) {

    }
  }

  static final class NoRegistration extends RegistrationAndHealthManagerImpl {

    @Override
    protected void registerService(String identifier, String processor_id, String... tags) {

    }

    @Override
    protected void deregisterService(String identifier) {

    }
  }
}

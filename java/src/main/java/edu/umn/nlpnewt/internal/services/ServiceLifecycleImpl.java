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
package edu.umn.nlpnewt.internal.services;

import edu.umn.nlpnewt.Internal;
import io.grpc.BindableService;
import io.grpc.health.v1.HealthCheckResponse;
import io.grpc.services.HealthStatusManager;

/**
 * Internal code to do service registration magic.
 */
@Internal
final class ServiceLifecycleImpl implements ServiceLifecycle {
  private final HealthStatusManager healthStatusManager;
  private final DiscoveryMechanism discoveryMechanism;

  public ServiceLifecycleImpl(HealthStatusManager healthStatusManager,
                              DiscoveryMechanism discoveryMechanism) {
    this.healthStatusManager = healthStatusManager;
    this.discoveryMechanism = discoveryMechanism;
  }

  @Override
  public void startedService(ServiceInfo serviceInfo) {
    healthStatusManager.setStatus(serviceInfo.getName(), HealthCheckResponse.ServingStatus.SERVING);
    if (serviceInfo.isRegister()) {
      discoveryMechanism.register(serviceInfo);
    }
  }

  @Override
  public void stoppedService(ServiceInfo serviceInfo) {
    healthStatusManager.setStatus(serviceInfo.getName(), HealthCheckResponse.ServingStatus.NOT_SERVING);
    if (serviceInfo.isRegister()) {
      discoveryMechanism.deregister(serviceInfo);
    }
  }

  @Override
  public BindableService getHealthService() {
    return healthStatusManager.getHealthService();
  }

  @Override
  public void setStatus(String service, HealthCheckResponse.ServingStatus status) {
    healthStatusManager.setStatus(service, status);
  }

  @Override
  public void clearStatus(String service) {
    healthStatusManager.clearStatus(service);
  }

  @Override
  public void enterTerminalState() {
    healthStatusManager.enterTerminalState();
  }
}

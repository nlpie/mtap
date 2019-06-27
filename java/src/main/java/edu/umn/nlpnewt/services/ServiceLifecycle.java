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

package edu.umn.nlpnewt.services;

import edu.umn.nlpnewt.Internal;
import io.grpc.BindableService;
import io.grpc.health.v1.HealthCheckResponse;

@Internal
public interface ServiceLifecycle {
  void startedService(ServiceInfo serviceInfo);

  void stoppedService(ServiceInfo serviceInfo);

  BindableService getHealthService();

  void setStatus(String service, HealthCheckResponse.ServingStatus status);

  void clearStatus(String service);

  void enterTerminalState();
}

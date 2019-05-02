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

package edu.umn.nlpnewt.internal;

import io.grpc.BindableService;
import io.grpc.health.v1.HealthCheckResponse;

public interface RegistrationAndHealthManager {
  void setHealthAddress(String address);

  void setHealthPort(int port);

  Runnable startedService(String processor_id, String... tags);

  BindableService getHealthService();

  void enterTerminalState();

  void setStatus(String identifier, HealthCheckResponse.ServingStatus status);
}

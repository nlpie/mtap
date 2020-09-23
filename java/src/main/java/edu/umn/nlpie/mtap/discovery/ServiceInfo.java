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

package edu.umn.nlpie.mtap.discovery;

import java.util.List;

public class ServiceInfo {
  private final String name;
  private final String identifier;
  private final String host;
  private final int port;
  private final List<String> tags;

  public ServiceInfo(
      String name,
      String identifier,
      String address,
      int port,
      List<String> tags
  ) {
    this.name = name;
    this.identifier = identifier;
    this.host = address;
    this.port = port;
    this.tags = tags;
  }

  public String getName() {
    return name;
  }

  public String getIdentifier() {
    return identifier;
  }

  public String getHost() {
    return host;
  }

  public int getPort() {
    return port;
  }

  public List<String> getTags() {
    return tags;
  }
}

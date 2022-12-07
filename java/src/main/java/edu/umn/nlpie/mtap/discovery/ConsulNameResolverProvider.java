/*
 * Copyright 2022 Regents of the University of Minnesota.
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

import com.google.common.net.HostAndPort;
import com.orbitz.consul.Consul;
import com.orbitz.consul.HealthClient;
import com.orbitz.consul.cache.ServiceHealthCache;
import com.orbitz.consul.cache.ServiceHealthKey;
import com.orbitz.consul.model.health.ServiceHealth;
import com.orbitz.consul.option.ImmutableQueryOptions;
import com.orbitz.consul.option.QueryOptions;
import io.grpc.*;

import java.net.InetSocketAddress;
import java.net.URI;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

final class ConsulNameResolverProvider extends NameResolverProvider {
  private static boolean registered = false;
  private static final Object initializationMutex = new Object();
  private ConsulNameResolverProvider() { }

  public static void register() {
    boolean result = registered;
    if (!result) {
      synchronized (initializationMutex) {
        result = registered;
        if (!result) {
          NameResolverRegistry.getDefaultRegistry().register(new ConsulNameResolverProvider());
          registered = true;
        }
      }
    }
  }

  @Override
  protected boolean isAvailable() {
    return true;
  }

  @Override
  protected int priority() {
    return 5;
  }

  @Override
  public NameResolver newNameResolver(URI targetUri, NameResolver.Args args) {
    String scheme = targetUri.getScheme();
    if (!"consul".equals(scheme)) {
      return null;
    }
    String authority = targetUri.getAuthority();

    String path = targetUri.getPath();
    String[] splits = path.split("/");
    String name = splits[1];
    List<String> tags = Arrays.asList(splits).subList(2, splits.length);
    return new ConsulNameResolver(authority, name, tags);
  }

  @Override
  public String getDefaultScheme() {
    return "consul";
  }

  /**
   * Internal implementation of grpc name-resolution magic using consul.
   */
  private static final class ConsulNameResolver extends NameResolver {

    private final String authority;

    private final ServiceHealthCache health;

    private Listener listener = null;

    private ConsulNameResolver(String authority, String name, List<String> tags) {
      HealthClient healthClient = Consul.builder()
          .withHostAndPort(HostAndPort.fromString(authority))
          .build().healthClient();
      this.authority = authority;
      QueryOptions query = ImmutableQueryOptions.builder().tag(tags).build();
      health = ServiceHealthCache.newCache(healthClient, name, true, 5, query);
      health.addListener(this::update);
    }

    @Override
    public String getServiceAuthority() {
      return authority;
    }

    @Override
    public void start(Listener listener) {
      this.listener = listener;
      health.start();
    }

    @Override
    public void shutdown() {
      health.stop();
      this.listener = null;
    }

    private void update(Map<ServiceHealthKey, ServiceHealth> healths) {
      List<EquivalentAddressGroup> addressGroups = new ArrayList<>();
      for (ServiceHealth health : healths.values()) {
        String address = health.getNode().getAddress();
        int port = health.getService().getPort();
        addressGroups.add(new EquivalentAddressGroup(new InetSocketAddress(address, port)));
      }
      Listener listener = this.listener;
      if (listener != null) {
        listener.onAddresses(addressGroups, Attributes.EMPTY);
      }
    }
  }
}

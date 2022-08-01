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

package edu.umn.nlpie.mtap.model;

import io.grpc.ManagedChannel;

import java.io.Closeable;
import java.io.IOException;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public class EventsClientPool implements AutoCloseable {
  private final List<EventsClient> pool;
  private final Map<String, EventsClient> instanceIdToClientMap;

  private final AtomicInteger ptr = new AtomicInteger(0);

  public EventsClientPool(Collection<EventsClient> clients) {
    pool = new ArrayList<>(clients);
    instanceIdToClientMap = new HashMap<>();
    for (EventsClient client : pool) {
      instanceIdToClientMap.put(client.getInstanceId(), client);
    }
  }

  public static EventsClientPool fromAddresses(String[] addresses, ChannelFactory channelFactory) {
    List<EventsClient> clients = new ArrayList<>(addresses.length);
    for (String address : addresses) {
      clients.add(new EventsClient(channelFactory.createChannel(address), address));
    }
    return new EventsClientPool(clients);
  }

  public EventsClient nextInstance() {
    return pool.get((ptr.getAndIncrement() % pool.size()));
  }

  public EventsClient instanceFor(String instanceId) {
    return instanceIdToClientMap.get(instanceId);
  }

  @Override
  public void close() {
    for (EventsClient eventsClient : pool) {
      eventsClient.close();
    }
  }
}

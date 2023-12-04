package edu.umn.nlpie.mtap.model;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public class EventsClientPool implements AutoCloseable {
  private static final Logger LOGGER = LoggerFactory.getLogger(EventsClientPool.class);

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
    LOGGER.debug("Creating EventsClientPool from addresses: {}", (Object) addresses);
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

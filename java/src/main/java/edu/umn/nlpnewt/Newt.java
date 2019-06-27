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
package edu.umn.nlpnewt;

import edu.umn.nlpnewt.processing.NewtProcessing;
import edu.umn.nlpnewt.services.DiscoveryMechanism;
import edu.umn.nlpnewt.services.NewtServices;
import edu.umn.nlpnewt.timing.NewtTiming;
import io.grpc.ManagedChannelBuilder;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.net.InetSocketAddress;
import java.nio.file.Path;
import java.util.List;

/**
 * The main class and entry points for the NLP-NEWT framework.
 * <p>
 * This object provides methods for interacting with a newt events service and for launching newt
 * processors written in Java.
 */
public final class Newt {
  /**
   * The name used by the events service for discovery.
   */
  public static final String EVENTS_SERVICE_NAME = "nlpnewt-events";

  /**
   * The name used by the processor services for discovery.
   */
  public static final String PROCESSOR_SERVICE_TAG = "v1-nlpnewt-processor";

  /**
   * Creates a standard (capable of handling overlapping labels) label index.
   *
   * @param labels Label objects to use to create the label index.
   * @param <L>    The label type.
   *
   * @return Label Index object.
   */
  public static <L extends Label> @NotNull LabelIndex<L> standardLabelIndex(
      @NotNull List<@NotNull L> labels
  ) {
    return new StandardLabelIndex<>(labels);
  }

  /**
   * Creates a distinct (not capable of handling overlapping labels) label index.
   * <p>
   * The technical definition of distinctness is that all labels should be able to be
   * ordered such that start indices and end indices are strictly increasing.
   *
   * @param labels Label objects to use to create the label index.
   * @param <L>    The label type.
   *
   * @return Label Index object.
   */
  public static <L extends Label> @NotNull LabelIndex<L> distinctLabelIndex(
      @NotNull List<@NotNull L> labels
  ) {
    return new DistinctLabelIndex<L>(labels);
  }

  /**
   * Creates an events client using service discovery to locate the events service.
   *
   * @return Events client object.
   */
  public static @NotNull EventsClient eventsClient() {
    Config config = ConfigImpl.loadFromDefaultLocations();
    return eventsClient(config);
  }

  /**
   * Creates an events client using service discovery to locate the events service.
   *
   * @param config The nlpnewt configuration object.
   *
   * @return Events client object.
   */
  public static @NotNull EventsClient eventsClient(Config config) {
    NewtServices services = new NewtServices(config);
    DiscoveryMechanism discoveryMechanism = services.getDiscoveryMechanism();
    String eventsTarget = discoveryMechanism.getServiceTarget(EVENTS_SERVICE_NAME, "v1");
    return new EventsClient(ManagedChannelBuilder.forTarget(eventsTarget)
        .usePlaintext().nameResolverFactory(discoveryMechanism.getNameResolverFactory()).build());
  }

  /**
   * Creates an object for interacting with a newt events service.
   *
   * <pre>
   *   {@code
   *   try (Events events = newt.events("localhost:9090")) {
   *     // interact with events service.
   *   }
   *   }
   * </pre>
   *
   * @param address The bound address and port of a newt events service. For example:
   *                "localhost:9090" or {@code null} if service discovery should be used.
   *
   * @return {@code EventsClient} object connected to the events service.
   */
  public static @NotNull EventsClient eventsClient(@Nullable String address) {
    if (address == null) {
      return eventsClient();
    }
    return new EventsClient(ManagedChannelBuilder.forTarget(address).usePlaintext().build());
  }

  /**
   * Creates an object for interacting with a newt events service.
   *
   * @param target The bound address and port of a newt events service. For example:
   *               "localhost:9090" or {@code null} if service discovery should be used.
   * @param config The configuration.
   *
   * @return {@code EventsClient} object connected to the events service.
   */
  public static @NotNull EventsClient eventsClient(@Nullable String target, Config config) {
    if (target == null) {
      return eventsClient(config);
    }
    return new EventsClient(ManagedChannelBuilder.forTarget(target).usePlaintext().build());
  }

  /**
   * Creates an object for interacting with a newt events service.
   *
   * <pre>
   *   {@code
   *   try (Events events = newt.events("localhost", 9090)) {
   *     // interact with the events service.
   *   }
   *   }
   * </pre>
   *
   * @param host The host ip or name of a newt events service. Example: "localhost" or "1.1.1.1".
   * @param port The host port of a newt events service. Example: {@code 9999}.
   *
   * @return {@code Events} object connected to the events service.
   */
  public static @NotNull EventsClient eventsClient(@NotNull String host, int port) {
    return eventsClient(host + ":" + port);
  }

  /**
   * Creates a {@code Server} object that can be used to start hosting an
   * {@link EventProcessor} or an {@link DocumentProcessor}.
   * <p>
   * Example:
   * <pre>
   *   {@code
   *   ProcessorServerOptions options = ProcessorServerOptions.emptyOptions()
   *       .withProcessor(new SomeProcessor())
   *       .withPort(9090)
   *       .register();
   *   Server server = newt.createProcessorServer(options);
   *   server.start();
   *   }
   * </pre>
   *
   * @param options The options object.
   *
   * @return {@code Server} object that can be used to start and shutdown serving the processor.
   */
  public static @NotNull Server createProcessorServer(@NotNull ProcessorServerOptions options) {
    Config config = ConfigImpl.loadFromDefaultLocations();
    Path configFile = options.getConfigFile();
    if (configFile != null) {
      config.update(ConfigImpl.loadConfig(configFile));
    }
    EventsClient eventsClient = eventsClient(options.getEventsTarget(), config);
    NewtServices newtServices = new NewtServices(config);
    NewtTiming newtTiming = new NewtTiming();
    NewtProcessing processing = new NewtProcessing(options, eventsClient, newtServices, newtTiming);
    return processing.getProcessorServer();
  }

  /**
   * Creates an object for interacting with a newt events service.
   *
   * <pre>
   *   {@code
   *   InetSocketAddress address = new InetSocketAddress("localhost", 9090);
   *   try (Events events = newt.events(address)) {
   *     // interact with events service.
   *   }
   *   }
   * </pre>
   *
   * @param address An {@code InetSocketAddress} for the bound address and port of a newt events
   *                service.
   *
   * @return {@code Events} object connected to the events service.
   */
  public @NotNull EventsClient eventsClient(@NotNull InetSocketAddress address) {
    return eventsClient(address.getHostString() + ":" + address.getPort());
  }
}

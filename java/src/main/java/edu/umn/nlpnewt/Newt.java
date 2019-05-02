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

import edu.umn.nlpnewt.internal.NewtInternal;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import org.kohsuke.args4j.CmdLineException;
import org.kohsuke.args4j.CmdLineParser;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

import static org.kohsuke.args4j.OptionHandlerFilter.ALL;

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

  private final Config config;

  /**
   * Creates a {@code Newt} object using configuration loaded from the standard locations.
   *
   * @throws IOException If there is an IOException while loading the configuration.
   * @see Config
   */
  public Newt() throws IOException {
    config = Config.loadConfigFromLocationOrDefaults(null);
  }

  /**
   * Creates a {@code Newt} object using a configuration loaded from the {@code configPath}
   * parameter or from the standard locations if {@code configPath} is {@code null}.
   *
   * @param configPath The path to load configuration from or {@code null}.
   *
   * @throws IOException If there is an {@code IOException} while loading the configuration.
   * @see Config
   */
  public Newt(@Nullable Path configPath) throws IOException {
    config = Config.loadConfigFromLocationOrDefaults(configPath);
  }

  /**
   * Creates a {@code Newt} object using configuration loaded from the standard loctaions and
   * updates from the {@code configPath} map.
   *
   * @param configUpdates Map of updates to make to configuration.
   *
   * @throws IOException If there is an {@code IOException} while loading the configuration.
   */
  public Newt(@NotNull Map<@NotNull String, @Nullable Object> configUpdates) throws IOException {
    config = Config.loadConfigFromLocationOrDefaults(null);
    config.update(configUpdates);
  }

  /**
   * Creates a {@code Newt} object using the given configuration.
   *
   * @param config configuration object.
   */
  public Newt(Config config) {
    this.config = config;
  }

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
    return NewtInternal.standardLabelIndex(labels);
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
    return NewtInternal.distinctLabelIndex(labels);
  }

  /**
   * A command-line main method for launching processing servers.
   *
   * @param args The command line arguments for launching the processor server.
   */
  public static void processorServerMain(@NotNull List<@NotNull String> args) {
    ProcessorServerOptions processorServerOptions = new ProcessorServerOptions();

    CmdLineParser parser = new CmdLineParser(processorServerOptions);

    try {
      parser.parseArgument(args);
    } catch (CmdLineException e) {
      System.err.println(e.getMessage());
      System.err.println("java edu.umn.nlpnewt.internal.ProcessorServer [options...] fully.qualified.ProcessorClassName");
      // print the list of available options
      parser.printUsage(System.err);
      System.err.println();

      // print option sample. This is useful some time
      System.err.println("Example: java edu.umn.nlpnewt.internal.ProcessorServer" + parser.printExample(ALL));
      return;
    }

    try {
      Newt newt = new Newt();
      Server server = NewtInternal.createProcessorServer(newt.config, processorServerOptions);
      server.start();
      server.blockUntilShutdown();
    } catch (IOException e) {
      System.err.println("Failed to start server: " + e.getMessage());
    } catch (InterruptedException e) {
      System.err.println("Server interrupted.");
    }
  }

  /**
   * A command-line main method for all of the functionality of the newt Java framework.
   *
   * @param args Array of command line arguments.
   */
  public static void main(@NotNull String[] args) {
    if (args.length > 0) {
      String mode = args[0];
      if (mode.startsWith("-h")) {
        System.out.println("Usage: java -jar Newt.jar MODE");
        System.out.println("Modes: one of {\"processor\", \"-h\", \"--help\"}");
      } else if (mode.startsWith("pr")) {
        processorServerMain(Arrays.asList(args).subList(1, args.length));
      }
      return;
    }

    System.err.println(
        "Incorrect or missing mode argument. Must be one of {\"processor\", \"-h\", \"--help\"}"
    );
  }

  /**
   * Creates an object for interacting with a newt events service.
   *
   * <pre>
   *   {@code
   *   try (NewtEvents events = newt.events("localhost:9090")) {
   *     // interact with events service.
   *   }
   *   }
   * </pre>
   *
   * @param address The bound address and port of a newt events service. For example:
   *                "localhost:9090" or {@code null} if service discovery should be used.
   *
   * @return {@code NewtEvents} object connected to the events service.
   */
  public @NotNull NewtEvents events(@Nullable String address) {
    return NewtInternal.createEvents(config, address);
  }

  /**
   * Creates an object for interacting with a newt events service.
   *
   * <pre>
   *   {@code
   *   try (NewtEvents events = newt.events("localhost", 9090)) {
   *     // interact with the events service.
   *   }
   *   }
   * </pre>
   *
   * @param host The host ip or name of a newt events service. Example: "localhost" or "1.1.1.1".
   * @param port The host port of a newt events service. Example: {@code 9999}.
   *
   * @return {@code NewtEvents} object connected to the events service.
   */
  public @NotNull NewtEvents events(@NotNull String host, int port) {
    return NewtInternal.createEvents(config, host + ":" + port);
  }

  /**
   * Creates an object for interacting with a newt events service.
   *
   * <pre>
   *   {@code
   *   InetSocketAddress address = new InetSocketAddress("localhost", 9090);
   *   try (NewtEvents events = newt.events(address)) {
   *     // interact with events service.
   *   }
   *   }
   * </pre>
   *
   * @param address An {@code InetSocketAddress} for the bound address and port of a newt events
   *                service.
   *
   * @return {@code NewtEvents} object connected to the events service.
   */
  public @NotNull NewtEvents events(@NotNull InetSocketAddress address) {
    return NewtInternal.createEvents(config,
        address.getHostString() + ":" + address.getPort());
  }


  /**
   * Creates a {@code Server} object that can be used to start hosting an
   * {@link AbstractEventProcessor} or an {@link AbstractDocumentProcessor}.
   * <p>
   * Example:
   * <pre>
   *   {@code
   *   ProcessorServerOptions options = ProcessorServerOptions.emptyOptions()
   *       .emptyOptions()
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
  public @NotNull Server createProcessorServer(@NotNull ProcessorServerOptions options) throws IOException {
    return NewtInternal.createProcessorServer(config, options);
  }
}

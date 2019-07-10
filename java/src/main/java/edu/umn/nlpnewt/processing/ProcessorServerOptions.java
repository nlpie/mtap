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

package edu.umn.nlpnewt.processing;

import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import org.kohsuke.args4j.CmdLineException;
import org.kohsuke.args4j.CmdLineParser;
import org.kohsuke.args4j.Option;
import org.kohsuke.args4j.spi.PathOptionHandler;

import java.io.OutputStream;
import java.io.PrintWriter;
import java.nio.file.Path;
import java.util.UUID;

import static org.kohsuke.args4j.OptionHandlerFilter.ALL;

/**
 * Args4j command-line supported options bean for processor servers.
 */
public class ProcessorServerOptions {
  @Option(name = "-p", aliases = {"--port"}, metaVar = "PORT",
      usage = "Port to host the processor service on or 0 if it should bind to a random " +
          "available port.")
  private int port = 0;

  @Option(name = "-r", aliases = {"--register"},
      usage = "Whether to register with service discovery.")
  private boolean register = false;

  @Nullable
  @Option(name = "-e", aliases = {"--events", "--events-address"}, metaVar = "EVENTS_TARGET",
      usage = "Events service GRPC target.")
  private String eventsTarget = null;

  @Nullable
  @Option(name = "-c", aliases = {"--config"}, handler = PathOptionHandler.class,
      metaVar = "CONFIG_PATH", usage = "A path to a config file to load.")
  private Path configFile = null;

  @Nullable
  @Option(name = "-i", aliases = {"--identifier"}, metaVar = "PROCESSOR_ID",
      usage = "The identifier to register the processor under. If not specified will default " +
          "to the @Processor annotation name.")
  private String identifier = null;

  @Nullable
  @Option(name = "-u", aliases = {"--unique-service-id"}, metaVar = "UNIQUE_SERVICE_ID",
      usage = "A unique per-instance server id that will be used to register and deregister the processor")
  private String uniqueServiceId = null;

  /**
   * Default constructor.
   */
  public ProcessorServerOptions() {
  }

  /**
   * Creates a new options bean using the default options.
   *
   * @return Options object containing all of the default options.
   */
  public static @NotNull ProcessorServerOptions defaultOptions() {
    return new ProcessorServerOptions();
  }

  /**
   * Prints a help message.
   *
   * @param parser    The CmdLineParser that was used to parse.
   * @param mainClass The main class this was invoked from.
   * @param e         Optional: the exception thrown by the parser.
   * @param output    Optional: An output stream to write the help message to, by default will use
   *                  {@code System.err}.
   */
  public static void printHelp(@NotNull CmdLineParser parser,
                               @NotNull Class<?> mainClass,
                               @Nullable CmdLineException e,
                               @Nullable OutputStream output) {
    if (output == null) {
      output = System.err;
    }
    PrintWriter writer = new PrintWriter(output);
    if (e != null) {
      writer.println(e.getMessage());
    }
    writer.println("java " + mainClass.getCanonicalName() + " [options...]");
    writer.flush();
    parser.printUsage(output);
    writer.println();

    writer.println("Example: " + mainClass.getCanonicalName() + parser.printExample(ALL));
    writer.flush();
  }

  /**
   * The port to listen on.
   *
   * @return The port number.
   */
  public int getPort() {
    return port;
  }

  /**
   * Sets the port to listen on.
   *
   * @param port The port number.
   */
  public void setPort(int port) {
    this.port = port;
  }

  /**
   * Get accessor for whether the processor should be registered with service discovery.
   *
   * @return {@code true} if the processor should be registered, false if not.
   */
  public boolean getRegister() {
    return register;
  }

  /**
   * Set accessor for whether the processor should be registered with service discovery.
   *
   * @param register {@code true} if the processor should be registered, false if not.
   */
  public void setRegister(boolean register) {
    this.register = register;
  }

  /**
   * An optional target/address for a events service.
   *
   * @return A gRPC target string or {@code null} if service discovery should be used.
   */
  public @Nullable String getEventsTarget() {
    return eventsTarget;
  }

  /**
   * Set a target/address for a events service.
   *
   * @param eventsTarget A gRPC target string or {@code null} if service discovery should be used.
   */
  public void setEventsTarget(@Nullable String eventsTarget) {
    this.eventsTarget = eventsTarget;
  }

  /**
   * An optional configuration file to load.
   *
   * @return Path to configuration file
   */
  public @Nullable Path getConfigFile() {
    return configFile;
  }

  /**
   * Sets an optional configuration file to load.
   *
   * @param configFile Path to configuration file.
   */
  public void setConfigFile(@Nullable Path configFile) {
    this.configFile = configFile;
  }

  /**
   * An optional identifier to replace the processor's default identifier for service registration
   * and discovery.
   *
   * @return A dns-complaint (only alphanumeric characters and dashes -) string
   */
  public @Nullable String getIdentifier() {
    return identifier;
  }

  /**
   * Sets the optional identifier to replace the processor's default identifier for service
   * registration and discovery.
   *
   * @param identifier A dns-complaint (only alphanumeric characters and dashes -) string.
   */
  public void setIdentifier(@Nullable String identifier) {
    this.identifier = identifier;
  }

  /**
   * Gets a unique, per-instance service identifier used to register and deregister the processor
   * with service discovery. Note: This identifier is not used to discover the service like
   * {@link #getIdentifier()}, only to enable de-registration of this specific service instance.
   *
   * @return String identifier or a random UUID if not set.
   */
  public @NotNull String getUniqueServiceId() {
    if (uniqueServiceId == null) {
      uniqueServiceId = UUID.randomUUID().toString();
    }
    return uniqueServiceId;
  }

  /**
   * Sets a unique, per-instance service identifier used to register and deregister the processor
   * with service discovery. Note: This identifier is not used to discover the service like
   * {@link #getIdentifier()}, only to enable de-registration of this specific service instance.
   *
   * @param uniqueServiceId A string identifier unique to this service instance.
   */
  public void setUniqueServiceId(@NotNull String uniqueServiceId) {
    this.uniqueServiceId = uniqueServiceId;
  }
}

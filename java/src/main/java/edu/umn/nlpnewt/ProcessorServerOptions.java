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

import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import org.kohsuke.args4j.*;
import org.kohsuke.args4j.spi.OneArgumentOptionHandler;
import org.kohsuke.args4j.spi.PathOptionHandler;
import org.kohsuke.args4j.spi.Setter;

import java.nio.file.Path;
import java.util.UUID;

/**
 * Options bean used to start a processor server.
 * <p>
 * Which processor to launch is specified via either processor or processorClass.
 */
public class ProcessorServerOptions {

  @Nullable
  @Argument(required = true, metaVar = "PROCESSOR_CLASS", handler = ProcessorOptionHandler.class,
      usage = "Processor full class name")
  private Class<? extends EventProcessor> processorClass = null;

  @Nullable
  private EventProcessor processor = null;

  @NotNull
  @Option(name = "-a", aliases = {"--address"}, metaVar = "ADDRESS",
      usage = "The address to bind the processor service to. Defaults to 127.0.0.1")
  private String address = "127.0.0.1";

  @Option(name = "-p", aliases = {"--port"}, metaVar = "PORT",
      usage = "Port to host the processor service on or 0 if it should bind to a random " +
          "available address.")
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
   * Creates an empty processor server options.
   */
  public ProcessorServerOptions() {
  }

  /**
   * Copy constructor.
   *
   * @param options Options to copy from.
   */
  public ProcessorServerOptions(ProcessorServerOptions options) {
    processorClass = options.getProcessorClass();
    processor = options.getProcessor();
    address = options.getAddress();
    port = options.getPort();
    register = options.getRegister();
    eventsTarget = options.getEventsTarget();
    configFile = options.getConfigFile();
    identifier = options.getIdentifier();
  }

  /**
   * Creates an empty processor server options.
   *
   * @return Processor server options object.
   */
  public static @NotNull ProcessorServerOptions emptyOptions() {
    return new ProcessorServerOptions();
  }

  /**
   * A processor class to instantiate and host. Exclusive with {@link #getProcessor()}.
   *
   * @return processorClass or {@code null} if not set.
   */
  public @Nullable Class<? extends EventProcessor> getProcessorClass() {
    return processorClass;
  }

  /**
   * Sets the processor class to instantiate and host.
   *
   * @param processorClass processorClass or {@code null} if it should be unset.
   */
  public void setProcessorClass(
      @Nullable Class<? extends EventProcessor> processorClass
  ) {
    if (processor != null && processorClass != null) {
      throw new IllegalStateException("Processor already set to processor instance.");
    }
    this.processorClass = processorClass;
  }

  /**
   * Builder method that sets the processor class to instantiate and host.
   *
   * @param processorClass processorClass or {@code null} if it should be unset.
   *
   * @return This options object.
   */
  public ProcessorServerOptions withProcessorClass(
      @Nullable Class<? extends EventProcessor> processorClass
  ) {
    setProcessorClass(processorClass);
    return this;
  }

  /**
   * A processor to instantiate and host. Exclusive with {@link #getProcessorClass()}.
   *
   * @return processor or {@code null} if it is unset.
   */
  public @Nullable EventProcessor getProcessor() {
    return processor;
  }

  /**
   * Set a processor to instantiate and host.
   *
   * @param processor processor or {@code null} if it should be unset.
   */
  public void setProcessor(@Nullable EventProcessor processor) {
    if (processorClass != null && processor != null) {
      throw new IllegalStateException("Processor already defined by class.");
    }
    this.processor = processor;
  }

  /**
   * Builder method that sets a processor to instantiate and host.
   *
   * @param processor processor or {@code null} if it should be unset.
   *
   * @return This options object.
   */
  public ProcessorServerOptions withProcessor(@Nullable EventProcessor processor) {
    setProcessor(processor);
    return this;
  }

  /**
   * The address to bind the server to.
   *
   * @return Either an IP or host name.
   */
  @NotNull
  public String getAddress() {
    return address;
  }

  /**
   * Sets the address to bind the server to.
   *
   * @param address Either an IP or host name.
   */
  public void setAddress(@NotNull String address) {
    this.address = address;
  }

  /**
   * Builder method for the address to bind the server to.
   *
   * @param address Either an IP or host name.
   *
   * @return This options object.
   */
  public ProcessorServerOptions withAddress(@NotNull String address) {
    setAddress(address);
    return this;
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
   * Builder method that sets the port to listen on.
   *
   * @param port The port to listen on.
   *
   * @return This options objects.
   */
  public ProcessorServerOptions withPort(int port) {
    this.port = port;
    return this;
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
   * Sets it so the processor should be registered with service discovery.
   *
   * @return This options object.
   */
  public @NotNull ProcessorServerOptions register() {
    this.register = true;
    return this;
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
   * Builder method for a target to a events service.
   *
   * @param eventsTarget A gRPC target string or {@code null} if service discovery should be used.
   *
   * @return This options object.
   */
  public ProcessorServerOptions withEventsTarget(@Nullable String eventsTarget) {
    this.eventsTarget = eventsTarget;
    return this;
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

  public ProcessorServerOptions withConfigFile(@Nullable Path configFile) {
    setConfigFile(configFile);
    return this;
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
   * Builder method for to set the optional identifier that replaces the processor's default
   * identifier for service registration and discovery.
   *
   * @param identifier A dns-complaint (only alphanumeric characters and dashes -) string.
   *
   * @return This Options object.
   */
  public ProcessorServerOptions withIdentifier(String identifier) {
    setIdentifier(identifier);
    return this;
  }

  /**
   * Gets a unique, per-instance service identifier used to register and deregister the processor
   * with service discovery. Note: This identifier is not used to discover the service like
   * {@link #getIdentifier()}, only to enable de-registration of this specific service instance.
   *
   * @return String identifier or a random UUID if not set.
   */
  public String getUniqueServiceId() {
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
  public void setUniqueServiceId(String uniqueServiceId) {
    this.uniqueServiceId = uniqueServiceId;
  }

  public ProcessorServerOptions withUniqueServiceId(String uniqueServiceId) {
    setUniqueServiceId(uniqueServiceId);
    return this;
  }

  /**
   * An args4j option handler that will parse a fully qualified class name into a
   * {@link EventProcessor} class.
   */
  public static class ProcessorOptionHandler
      extends OneArgumentOptionHandler<Class<? extends EventProcessor>> {

    public ProcessorOptionHandler(
        CmdLineParser parser,
        OptionDef option,
        Setter<? super Class<? extends EventProcessor>> setter
    ) {
      super(parser, option, setter);
    }

    @Override
    protected Class<? extends EventProcessor> parse(
        String argument
    ) throws NumberFormatException, CmdLineException {
      try {
        return getClass().getClassLoader().loadClass(argument).asSubclass(EventProcessor.class);
      } catch (ClassNotFoundException e) {
        e.printStackTrace(System.err);
        throw new CmdLineException(owner, "Invalid processor class name", e);
      }
    }
  }
}

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

package edu.umn.nlpie.mtap.processing;

import edu.umn.nlpie.mtap.common.Config;
import edu.umn.nlpie.mtap.common.ConfigImpl;
import edu.umn.nlpie.mtap.discovery.Discovery;
import edu.umn.nlpie.mtap.discovery.DiscoveryMechanism;
import edu.umn.nlpie.mtap.model.ChannelFactory;
import edu.umn.nlpie.mtap.model.EventsClientPool;
import edu.umn.nlpie.mtap.utilities.Helpers;
import io.grpc.Server;
import io.grpc.netty.shaded.io.grpc.netty.NettyServerBuilder;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import org.kohsuke.args4j.CmdLineException;
import org.kohsuke.args4j.CmdLineParser;
import org.kohsuke.args4j.Option;
import org.kohsuke.args4j.spi.PathOptionHandler;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.*;
import java.net.InetSocketAddress;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

import static org.kohsuke.args4j.OptionHandlerFilter.ALL;


/**
 * Responsible for running and hosting {@link EventProcessor} and {@link DocumentProcessor} classes.
 *
 * @see Builder
 */
public final class ProcessorServer implements edu.umn.nlpie.mtap.common.Server {
  private static final Logger logger = LoggerFactory.getLogger(ProcessorServer.class);

  private final Server grpcServer;
  private final ProcessorService processorService;
  private final String host;

  private final String sid;
  private final boolean writeAddress;
  private boolean running = false;
  private Path addressFile = null;

  ProcessorServer(
      ProcessorService processorService,
      Server grpcServer,
      String host,
      String sid,
      boolean writeAddress
  ) {
    this.processorService = processorService;
    this.host = host;
    this.grpcServer = grpcServer;
    this.sid = sid;
    this.writeAddress = writeAddress;
  }

  @Override
  public void start() throws IOException {
    if (running) {
      return;
    }
    running = true;
    grpcServer.start();
    int port = grpcServer.getPort();

    if (writeAddress) {
      Path homeDir = Helpers.getHomeDirectory();
      addressFile = homeDir.resolve("addresses").resolve(sid + ".address");
      try (BufferedWriter writer = Files.newBufferedWriter(addressFile, StandardOpenOption.CREATE_NEW)) {
        writer.write("" + host + ":" + port);
      }
    }

    processorService.started(port);
    Runtime.getRuntime().addShutdownHook(new Thread(this::shutdown));
  }

  @Override
  public void shutdown() {
    if (!running) {
      return;
    }
    try {
      processorService.close();
    } catch (Exception e) {
      // Print to system
      System.err.println("Exception closing processor service.");
      e.printStackTrace(System.err);
    }
    grpcServer.shutdownNow();
    running = false;
    if (addressFile != null) {
      try {
        Files.delete(addressFile);
      } catch (Exception e) {
        System.err.println("Failed to delete address file");
        e.printStackTrace(System.err);
      }
    }
  }

  @Override
  public void blockUntilShutdown() throws InterruptedException {
    grpcServer.awaitTermination();
  }

  @Override
  public int getPort() {
    return grpcServer.getPort();
  }

  @Override
  public boolean isRunning() {
    return running;
  }

  public Server getGrpcServer() {
    return grpcServer;
  }

  /**
   * Args4j command-line supported options bean for processor servers.
   */
  public static class Builder {
    @Option(name = "--host", metaVar = "HOST",
        usage = "Host i.e. IP address or hostname to bind to.")
    private String host = "127.0.0.1";

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
    @Option(name = "--mtap-config", handler = PathOptionHandler.class, metaVar = "CONFIG_PATH",
        usage = "A path to a config file to load.")
    private Path configFile = null;

    @Nullable
    @Option(name = "-n", aliases = {"--name"}, metaVar = "PROCESSOR_NAME",
        usage = "The identifier to register the processor under. If not specified will default " +
            "to the @Processor annotation name.")
    private String name = null;

    @Nullable
    @Option(name = "--sid", metaVar = "SERVICE_INSTANCE_ID",
        usage = "A unique per-instance server id that will be used to register and deregister the processor")
    private String sid = null;

    @Option(name = "-w", aliases = {"--workers"}, metaVar = "N_WORKERS",
        usage = "The number of threads for GRPC workers.")
    private int workers = 10;

    @Option(name = "--write-address", usage = "Writes the address to the mtap addresses directory.")
    private boolean writeAddress = false;

    @Option(name = "--log-level", metaVar = "LOG_LEVEL", usage = "The log level to use.")
    private String logLevel;

    private ChannelFactory channelFactory;

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
     * @return The host that the server will bind to.
     */
    public @NotNull String getHost() {
      return host;
    }

    /**
     * @param host The host that the server will bind to.
     */
    public void setHost(@NotNull String host) {
      this.host = host;
    }

    public @NotNull Builder host(@NotNull String host) {
      this.host = host;
      return this;
    }

    /**
     * @return The bind port for the server
     */
    public int getPort() {
      return port;
    }

    /**
     * @param port The bind port for the server.
     */
    public void setPort(int port) {
      this.port = port;
    }

    /**
     * @param port The bind port for the server
     * @return this builder.
     */
    public @NotNull Builder port(int port) {
      this.port = port;
      return this;
    }

    /**
     * @return Whether the server should register with service discovery.
     */
    public boolean getRegister() {
      return register;
    }

    /**
     * @param register Whether the server should register with service discovery.
     */
    public void setRegister(boolean register) {
      this.register = register;
    }

    /**
     * @param register Whether the server should register with service discovery.
     * @return this builder.
     */
    public @NotNull Builder register(boolean register) {
      this.register = register;
      return this;
    }

    /**
     * @return A grpc target for the events service.
     */
    public @Nullable String getEventsTarget() {
      return eventsTarget;
    }

    /**
     * @param eventsTarget A grpc target for the events service.
     */
    public void setEventsTarget(@Nullable String eventsTarget) {
      this.eventsTarget = eventsTarget;
    }

    /**
     * @param eventsTarget A grpc target for the events service.
     * @return this builder
     */
    public @NotNull Builder eventsTarget(@Nullable String eventsTarget) {
      this.eventsTarget = eventsTarget;
      return this;
    }

    /**
     * @return Override for the location of the configuration file.
     */
    public @Nullable Path getConfigFile() {
      return configFile;
    }

    /**
     * @param configFile Override for the location of the configuration file.
     */
    public void setConfigFile(@Nullable Path configFile) {
      this.configFile = configFile;
    }

    /**
     * @param configFile Override for the location of the configuration file.
     * @return this builder
     */
    public @NotNull Builder configFile(Path configFile) {
      this.configFile = configFile;
      return this;
    }

    /**
     * An optional name to replace the processor's default name for service registration
     * and discovery.
     *
     * @return A dns-complaint (only alphanumeric characters and dashes -) string
     */
    public @Nullable String getName() {
      return name;
    }

    /**
     * Sets the optional name to replace the processor's default service name for service
     * registration and discovery.
     *
     * @param name A dns-complaint (only alphanumeric characters and dashes -) string.
     */
    public void setName(@Nullable String name) {
      this.name = name;
    }

    /**
     * Sets the optional name to replace the processor's default service name for service
     * registration and discovery.
     *
     * @param name A dns-complaint (only alphanumeric characters and dashes -) string.
     * @return this builder.
     */
    public @NotNull Builder name(@Nullable String name) {
      this.name = name;
      return this;
    }

    /**
     * Gets a unique, per-instance service identifier used to register and deregister the processor
     * with service discovery. Note: This identifier is not used to discover the service like
     * {@link #getName()}, only to enable de-registration of this specific service instance.
     *
     * @return String identifier or a random UUID if not set.
     */
    public @Nullable String getSid() {
      return sid;
    }

    /**
     * Sets a unique, per-instance service identifier used to register and deregister the processor
     * with service discovery. Note: This identifier is not used to discover the service like
     * {@link #getName()}, only to enable de-registration of this specific service instance.
     *
     * @param sid A string identifier unique to this service instance.
     */
    public void setSid(@NotNull String sid) {
      this.sid = sid;
    }

    /**
     * Sets a unique, per-instance service identifier used to register and deregister the processor
     * with service discovery. Note: This identifier is not used to discover the service like
     * {@link #getName()}, only to enable de-registration of this specific service instance.
     *
     * @param uniqueServiceId A string identifier unique to this service instance.
     * @return this builder
     */
    public @NotNull Builder uniqueServiceId(@NotNull String uniqueServiceId) {
      this.sid = uniqueServiceId;
      return this;
    }

    public @NotNull String getLogLevel() {
      return logLevel;
    }

    public void setLogLevel(@Nullable String logLevel) {
      this.logLevel = logLevel;
    }

    public @NotNull Builder logLevel(@Nullable String logLevel) {
      this.logLevel = logLevel;
      return this;
    }

    /**
     * Creates a processor server using the options specified in this object.
     *
     * @param processor The processor to host.
     * @return Object which can be used to control a server's lifecycle.
     */
    public ProcessorServer build(EventProcessor processor) {
      Config config = ConfigImpl.loadConfigFromLocationOrDefaults(configFile);
      String[] addresses;
      if (eventsTarget != null) {
        addresses = eventsTarget.split(",");
      } else {
        addresses = new String[]{null};
      }
      ChannelFactory channelFactory = this.channelFactory;
      if (channelFactory == null) {
        channelFactory = new StandardChannelFactory(config);
      }

      EventsClientPool clientPool = EventsClientPool.fromAddresses(addresses, channelFactory);
      ProcessorRunner runner = new LocalProcessorRunner(clientPool, processor);
      DiscoveryMechanism discoveryMechanism = null;
      if (register) {
        discoveryMechanism = Discovery.getDiscoveryMechanism(config);
      }
      HealthService healthService = new HSMHealthService();
      ProcessorService processorService = new DefaultProcessorService(
          runner,
          new DefaultTimingService(),
          discoveryMechanism,
          healthService,
          name,
          sid,
          host
      );
      NettyServerBuilder builder = NettyServerBuilder.forAddress(new InetSocketAddress(host, port));
      Integer maxInboundMessageSize = config.getIntegerValue("grpc.processor_options.grpc.max_receive_message_length");
      if (maxInboundMessageSize != null) {
        builder.maxInboundMessageSize(maxInboundMessageSize);
      }
      Integer keepAliveTime = config.getIntegerValue("grpc.processor_options.grpc.keepalive_time_ms");
      if (keepAliveTime != null) {
        builder.keepAliveTime(keepAliveTime, TimeUnit.MILLISECONDS);
      }
      Integer keepAliveTimeout = config.getIntegerValue("grpc.processor_options.grpc.keepalive_timeout_ms");
      if (keepAliveTimeout != null) {
        builder.keepAliveTimeout(keepAliveTimeout, TimeUnit.MILLISECONDS);
      }
      Boolean permitKeepAliveWithoutCalls = config.getBooleanValue("grpc.processor_options.grpc.permit_keepalive_without_calls");
      if (permitKeepAliveWithoutCalls != null) {
        builder.permitKeepAliveWithoutCalls(permitKeepAliveWithoutCalls);
      }
      Integer permitKeepAliveTime = config.getIntegerValue("grpc.processor_options.grpc.http2.min_ping_interval_without_data_ms");
      if (permitKeepAliveTime != null) {
        builder.permitKeepAliveTime(permitKeepAliveTime, TimeUnit.MILLISECONDS);
      }
      Server grpcServer = builder
          .executor(Executors.newFixedThreadPool(workers))
          .addService(healthService.getService())
          .addService(processorService).build();
      return new ProcessorServer(processorService, grpcServer, host, sid, writeAddress);
    }

    /**
     * Alias for {@link #build}
     *
     * @param processor The processor to host.
     * @return A server object that can be used to control the lifecycle of the server.
     */
    public ProcessorServer createServer(EventProcessor processor) {
      return build(processor);
    }
  }
}

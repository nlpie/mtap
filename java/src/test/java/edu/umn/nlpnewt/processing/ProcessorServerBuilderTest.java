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

import edu.umn.nlpnewt.common.Config;
import edu.umn.nlpnewt.common.ConfigImpl;
import edu.umn.nlpnewt.discovery.DiscoveryMechanism;
import edu.umn.nlpnewt.model.EventsClient;
import io.grpc.Server;
import io.grpc.ServerBuilder;
import io.grpc.inprocess.InProcessServerBuilder;
import io.grpc.testing.GrpcCleanupRule;
import org.junit.Rule;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.util.concurrent.ExecutorService;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.mock;

class ProcessorServerBuilderTest {
  @Rule
  public final GrpcCleanupRule grpcCleanup = new GrpcCleanupRule();

  private ProcessorServerOptions options;
  private EventProcessor mockProcessor;

  private ProcessorServerBuilder builder;

  @BeforeEach
  void setUp() {
    options = ProcessorServerOptions.defaultOptions();
    mockProcessor = mock(EventProcessor.class);
    builder = ProcessorServerBuilder.forProcessor(mockProcessor, options);
  }

  @Test
  void getConfigNotNull() {
    assertNotNull(builder.getConfig());
  }

  @Test
  void setConfig() {
    Config config = ConfigImpl.defaultConfig();
    builder.setConfig(config);
    assertSame(config, builder.getConfig());
  }

  @Test
  void withConfig() {
    Config config = ConfigImpl.defaultConfig();
    builder.withConfig(config);
    assertSame(config, builder.getConfig());
  }

  @Test
  void getEventsClientNotNull() {
    assertNotNull(builder.getEventsClient());
  }

  @Test
  void setEventsClient() {
    EventsClient client = mock(EventsClient.class);
    builder.setEventsClient(client);
    assertSame(client, builder.getEventsClient());
  }

  @Test
  void withEventsClient() {
    EventsClient mockClient = mock(EventsClient.class);
    builder.withEventsClient(mockClient);
    assertSame(mockClient, builder.getEventsClient());
  }

  @Test
  void getDiscoveryMechanismNotNull() {
    assertNotNull(builder.getDiscoveryMechanism());
  }

  @Test
  void setDiscoveryMechanism() {
    DiscoveryMechanism mockMechanism = mock(DiscoveryMechanism.class);
    builder.setDiscoveryMechanism(mockMechanism);
    assertSame(mockMechanism, builder.getDiscoveryMechanism());
  }

  @Test
  void withDiscoveryMechanism() {
    DiscoveryMechanism mockMechanism = mock(DiscoveryMechanism.class);
    builder.withDiscoveryMechanism(mockMechanism);
    assertSame(mockMechanism, builder.getDiscoveryMechanism());
  }

  @Test
  void getOptions() {
    assertSame(options, builder.getOptions());
  }

  @Test
  void getBackgroundExecutorNotNull() {
    assertNotNull(builder.getBackgroundExecutor());
  }

  @Test
  void setBackgroundExecutor() {
    ExecutorService mockExecutorService = mock(ExecutorService.class);
    builder.setBackgroundExecutor(mockExecutorService);
    assertSame(builder.getBackgroundExecutor(), mockExecutorService);
  }

  @Test
  void withBackgroundExecutor() {
    ExecutorService mockExecutorService = mock(ExecutorService.class);
    builder.withBackgroundExecutor(mockExecutorService);
    assertSame(builder.getBackgroundExecutor(), mockExecutorService);
  }

  @Test
  void build() {
    assertNotNull(builder.build());
  }

  @Test
  void buildWithServerBuilder() throws IOException {
    String name = InProcessServerBuilder.generateName();
    ServerBuilder serverBuilder = InProcessServerBuilder.forName(name).directExecutor();
    ProcessorServer server = builder.build(serverBuilder);
    server.start();
    Server grpcServer = grpcCleanup.register(server.getServer());
    assertNotNull(grpcServer);
    server.shutdown();
  }
}
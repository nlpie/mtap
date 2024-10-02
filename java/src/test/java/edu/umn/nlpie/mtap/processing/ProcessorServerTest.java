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

import io.grpc.Server;
import io.grpc.inprocess.InProcessServerBuilder;
import io.grpc.testing.GrpcCleanupRule;
import org.junit.Rule;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import java.io.IOException;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.verify;

class ProcessorServerTest {
  @Rule
  public final GrpcCleanupRule grpcCleanup = new GrpcCleanupRule();

  @Mock
  private ProcessorService mockProcessorService;

  private AutoCloseable mocks;

  @BeforeEach
  void setUp() {
    mocks = MockitoAnnotations.openMocks(this);
  }

  @AfterEach
  void tearDown() {
    try {
      mocks.close();
    } catch (Exception e) {
      throw new RuntimeException(e);
    }
  }

  @Test
  void testLifecycle() throws IOException, InterruptedException {
    Server server = createServer();
    ProcessorServer tested = createProcessorServer(server);
    tested.start();
    verify(mockProcessorService).started(-1);
    assertEquals(-1, tested.getPort());
    tested.shutdown();
    tested.blockUntilShutdown();
    verify(mockProcessorService).close();
    assertTrue(server.isShutdown());
  }

  private Server createServer() {
    String name = InProcessServerBuilder.generateName();
    Server server = InProcessServerBuilder.forName(name).directExecutor().build();
    grpcCleanup.register(server);
    return server;
  }

  private ProcessorServer createProcessorServer(Server server) {
    return new ProcessorServer(mockProcessorService, server, false);
  }
}

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

package edu.umn.nlpnewt.processing;

import io.grpc.Server;
import io.grpc.inprocess.InProcessServerBuilder;
import io.grpc.testing.GrpcCleanupRule;
import org.junit.Rule;
import org.junit.jupiter.api.Test;

import java.io.IOException;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;

class ProcessorServerTest {
  @Rule
  public final GrpcCleanupRule grpcCleanup = new GrpcCleanupRule();

  @Test
  void start() throws IOException {
    ProcessorService service = mock(ProcessorService.class);
    String name = InProcessServerBuilder.generateName();
    Server server = InProcessServerBuilder.forName(name).directExecutor().build();

    ProcessorServer processorServer = new ProcessorServer("localhost", server,
        service);
    processorServer.start();
    verify(service).startedServing("localhost", -1);
  }

  @Test
  void getPort() throws IOException {
    ProcessorService service = mock(ProcessorService.class);
    String name = InProcessServerBuilder.generateName();
    Server server = InProcessServerBuilder.forName(name).directExecutor().build();

    ProcessorServer processorServer = new ProcessorServer("localhost", server,
        service);
    processorServer.start();
    assertEquals(-1, processorServer.getPort());
  }

  @Test
  void shutdown() throws IOException, InterruptedException {
    ProcessorService service = mock(ProcessorService.class);
    String name = InProcessServerBuilder.generateName();
    Server server = InProcessServerBuilder.forName(name).directExecutor().build();

    ProcessorServer processorServer = new ProcessorServer("localhost", server,
        service);
    processorServer.start();
    processorServer.shutdown();
    processorServer.blockUntilShutdown();
    verify(service).stoppedServing();
  }
}

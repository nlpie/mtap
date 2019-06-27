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

import edu.umn.nlpnewt.*;
import edu.umn.nlpnewt.api.v1.ProcessorGrpc;
import edu.umn.nlpnewt.services.DiscoveryMechanism;
import edu.umn.nlpnewt.services.NewtServices;
import edu.umn.nlpnewt.services.ServiceLifecycle;
import edu.umn.nlpnewt.timing.NewtTiming;
import io.grpc.inprocess.InProcessServerBuilder;
import io.grpc.netty.NettyServerBuilder;
import org.jetbrains.annotations.NotNull;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class NewtProcessingTest {

  private Config config;
  private EventProcessor processor;
  private ProcessorServerOptions options;
  private NewtServices newtServices;
  private NewtTiming newtTiming;
  private NewtProcessing newtProcessing;
  private ServiceLifecycle serviceLifecycle;
  private DiscoveryMechanism discoveryMechanism;
  private ContextManager contextManager;
  private ProcessorContext processorContext;
  private EventsClient eventsClient;
  private Runner runner;
  private ProcessorService service;

  @BeforeEach
  void setUp() {
    config = mock(Config.class);
    processor = mock(EventProcessor.class);
    options = new ProcessorServerOptions(new TestProcessor());
    newtServices = new NewtServices(config);
    discoveryMechanism = mock(DiscoveryMechanism.class);
    newtServices.setDiscoveryMechanism(discoveryMechanism);
    serviceLifecycle = mock(ServiceLifecycle.class);
    newtServices.setServiceLifecycle(serviceLifecycle);
    eventsClient = mock(EventsClient.class);
    newtTiming = new NewtTiming();

    contextManager = mock(ContextManager.class);
    processorContext = mock(ProcessorContext.class);
    when(contextManager.getContext()).thenReturn(processorContext);

    runner = mock(Runner.class);

    service = mock(ProcessorService.class);

    newtProcessing = new NewtProcessing(options, eventsClient, newtServices, newtTiming);
  }

  @Test
  void setProcessorName() {
    newtProcessing.setProcessorName("test-processor");
    assertEquals("test-processor", newtProcessing.getProcessorName());
  }

  @Test
  void getProcessorId() {
    options.setIdentifier("processorId");
    String processorId = newtProcessing.getProcessorId();
    assertEquals("processorId", processorId);
  }

  @Test
  void getProcessorIdFromName() {
    newtProcessing.setProcessorName("processorId");
    String processorId = newtProcessing.getProcessorId();
    assertEquals("processorId", processorId);
  }

  @Test
  void setProcessorId() {
    newtProcessing.setProcessorId("processorID");
    String processorId = newtProcessing.getProcessorId();
    assertEquals("processorID", processorId);
  }

  @Test
  void getContextManager() {
    newtProcessing.setProcessorId("processorId");
    ContextManager contextManager = newtProcessing.getContextManager();
    assertTrue(contextManager instanceof ContextManagerImpl);
    ContextManagerImpl impl = (ContextManagerImpl) contextManager;
    assertEquals(serviceLifecycle, impl.getServiceLifecycle());
    assertEquals("processorId", newtProcessing.getProcessorId());
  }

  @Test
  void setContextManager() {
    newtProcessing.setContextManager(contextManager);
    ContextManager contextManager = newtProcessing.getContextManager();
    assertEquals(this.contextManager, contextManager);
  }

  @Test
  void setProcessor() {
    newtProcessing.setProcessor(processor);
    EventProcessor processor = newtProcessing.getProcessor();
    assertEquals(this.processor, processor);
  }

  @Test
  void testDefaultServerBuilder() {
    assertTrue(newtProcessing.getServerImplBuilder() instanceof NettyServerBuilder);
  }

  @Test
  void getRunner() {
    newtProcessing.setProcessor(processor);
    newtProcessing.setContextManager(contextManager);
    newtProcessing.setProcessorName("processorName");
    newtProcessing.setProcessorId("processorId");

    Runner runner = newtProcessing.getRunner();
    assertTrue(runner instanceof RunnerImpl);
    RunnerImpl impl = (RunnerImpl) runner;
    assertEquals(processor, impl.getProcessor());
    assertEquals(contextManager, impl.getContextManager());
    assertEquals("processorName", impl.getProcessorName());
    assertEquals("processorId", impl.getProcessorId());
  }

  @Test
  void setRunner() {
    newtProcessing.setRunner(runner);
    Runner runner = newtProcessing.getRunner();
    assertEquals(this.runner, runner);
  }

  @Test
  void getService() {
    newtProcessing.setRunner(runner);
    options.setUniqueServiceId("uniqueServiceId");
    options.setRegister(true);

    ProcessorService service = newtProcessing.getService();
    assertTrue(service instanceof ProcessorServiceImpl);
    ProcessorServiceImpl impl = (ProcessorServiceImpl) service;
    assertEquals(runner, impl.getRunner());
    assertEquals("uniqueServiceId", impl.getUniqueServiceId());
    assertTrue(impl.isRegister());
    assertEquals(serviceLifecycle, impl.getServiceLifecycle());
    assertNotNull(impl.getTimesCollector());
  }

  @Test
  void setService() {
    newtProcessing.setService(service);
    ProcessorService service = newtProcessing.getService();
    assertEquals(this.service, service);
  }

  @Test
  void testProvidedServerBuilder() {
    String name = InProcessServerBuilder.generateName();
    InProcessServerBuilder builder = InProcessServerBuilder.forName(name);
    newtProcessing.setServerImplBuilder(builder);
    assertTrue(newtProcessing.getServerImplBuilder() instanceof InProcessServerBuilder);
  }

  @Test
  void getProcessorServer() {
    String name = InProcessServerBuilder.generateName();
    InProcessServerBuilder builder = InProcessServerBuilder.forName(name);
    Service service = new Service();
    newtProcessing.setServerImplBuilder(builder).setService(service);
    ProcessorServer processorServer = newtProcessing.getProcessorServer();
    assertEquals(service, processorServer.getService());
  }

  @Processor("newt-test-processor")
  public static class TestProcessor extends EventProcessor {

    @Override
    public void process(@NotNull Event event, @NotNull JsonObject params, @NotNull JsonObjectBuilder result) {

    }
  }

  static class Service extends ProcessorGrpc.ProcessorImplBase implements ProcessorService {

    @Override
    public void startedServing(String address, int port) {

    }

    @Override
    public void stoppedServing() {

    }
  }
}

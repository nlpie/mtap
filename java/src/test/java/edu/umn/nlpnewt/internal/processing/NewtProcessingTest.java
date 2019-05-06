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

package edu.umn.nlpnewt.internal.processing;

import edu.umn.nlpnewt.*;
import edu.umn.nlpnewt.api.v1.ProcessorGrpc;
import edu.umn.nlpnewt.internal.events.NewtEvents;
import edu.umn.nlpnewt.internal.services.DiscoveryMechanism;
import edu.umn.nlpnewt.internal.services.NewtServices;
import edu.umn.nlpnewt.internal.services.ServiceLifecycle;
import edu.umn.nlpnewt.internal.timing.NewtTiming;
import io.grpc.ServerServiceDefinition;
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
  private NewtEvents newtEvents;
  private NewtTiming newtTiming;
  private NewtProcessing newtProcessing;
  private ServiceLifecycle serviceLifecycle;
  private DiscoveryMechanism discoveryMechanism;
  private ContextManager contextManager;
  private ProcessorContext processorContext;
  private Events events;
  private Runner runner;
  private ProcessorService service;

  @BeforeEach
  void setUp() {
    config = mock(Config.class);
    processor = mock(EventProcessor.class);
    options = ProcessorServerOptions.emptyOptions();
    newtServices = new NewtServices(config);
    discoveryMechanism = mock(DiscoveryMechanism.class);
    newtServices.setDiscoveryMechanism(discoveryMechanism);
    serviceLifecycle = mock(ServiceLifecycle.class);
    newtServices.setServiceLifecycle(serviceLifecycle);
    newtEvents = new NewtEvents(newtServices);
    events = mock(Events.class);
    newtEvents.setEvents(events);
    newtTiming = new NewtTiming();

    contextManager = mock(ContextManager.class);
    processorContext = mock(ProcessorContext.class);
    when(contextManager.getContext()).thenReturn(processorContext);

    runner = mock(Runner.class);

    service = mock(ProcessorService.class);

    newtProcessing = new NewtProcessing(options, newtServices, newtEvents, newtTiming);
  }

  @Test
  void getProcessorClassProcessor() {
    options.setProcessor(processor);
    Class<? extends EventProcessor> processorClass = newtProcessing.getProcessorClass();

    assertEquals(processor.getClass(), processorClass);
  }

  @Test
  void getProcessorClass() {
    options.setProcessorClass(processor.getClass());

    Class<? extends EventProcessor> processorClass = newtProcessing.getProcessorClass();

    assertEquals(processor.getClass(), processorClass);
  }

  @Test
  void getProcessorClassMissing() {
    assertThrows(IllegalArgumentException.class, () -> {
      newtProcessing.getProcessorClass();
    });
  }

  @Test
  void getProcessorName() {
    newtProcessing.setProcessorClass(TestProcessor.class);
    String processorName = newtProcessing.getProcessorName();
    assertEquals("newt-test-processor", processorName);
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
  void setProcessorClass() {
    newtProcessing.setProcessorClass(processor.getClass());
    assertEquals(processor.getClass(), newtProcessing.getProcessorClass());
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
  void getProcessor() {
    options.setProcessor(processor);
    EventProcessor processor = newtProcessing.getProcessor();
    assertEquals(this.processor, processor);
  }

  @Test
  void getProcessorFromClass() {
    options.setProcessorClass(TestProcessor.class);
    EventProcessor processor = newtProcessing.getProcessor();
    assertTrue(processor instanceof TestProcessor);
  }

  @Test
  void getProcessorFromClassWithInit() {
    options.setProcessorClass(TestProcessorWithInit.class);
    EventProcessor processor = newtProcessing.getProcessor();
    assertTrue(processor instanceof TestProcessor);
  }

  @Test
  void getProcessorFromClassWithContext() {
    options.setProcessorClass(TestProcessorWithContext.class);
    newtProcessing.setContextManager(contextManager);
    EventProcessor processor = newtProcessing.getProcessor();
    assertTrue(processor instanceof TestProcessorWithContext);
    TestProcessorWithContext impl = (TestProcessorWithContext) processor;
    assertEquals(processorContext, impl.context);
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
  void getEvents() {
    Events events = newtProcessing.getEvents();
    assertEquals(this.events, events);
  }

  @Test
  void setEvents() {
    Events newEvents = mock(Events.class);
    newtProcessing.setEvents(newEvents);
    assertEquals(newEvents, newtProcessing.getEvents());
  }

  @Test
  void getRunner() {
    newtProcessing.setProcessor(processor);
    newtProcessing.setEvents(events);
    newtProcessing.setContextManager(contextManager);
    newtProcessing.setProcessorName("processorName");
    newtProcessing.setProcessorId("processorId");

    Runner runner = newtProcessing.getRunner();
    assertTrue(runner instanceof RunnerImpl);
    RunnerImpl impl = (RunnerImpl) runner;
    assertEquals(processor, impl.getProcessor());
    assertEquals(events, impl.getEvents());
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
  static class TestProcessor implements EventProcessor {

    @Override
    public void process(@NotNull Event event, @NotNull JsonObject params, @NotNull JsonObjectBuilder result) {

    }
  }

  @Processor("newt-test-processor")
  static class TestProcessorWithInit extends TestProcessor {
    TestProcessorWithInit() {

    }
  }

  @Processor("newt-test-processor-with-context")
  static class TestProcessorWithContext extends TestProcessor {
    final ProcessorContext context;

    public TestProcessorWithContext(ProcessorContext context) {
      this.context = context;
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

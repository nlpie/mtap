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
import org.jetbrains.annotations.NotNull;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

import java.time.Duration;
import java.util.Collections;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.same;
import static org.mockito.Mockito.*;

class ProcessorRunnerImplTest {

  private EventProcessor processor;
  private ProcessorContextManager contextManager;
  private NewtEvents events;
  private JsonObjectBuilder jsonObjectBuilder;
  private ProcessorRunnerImpl runner;
  private ProcessingResultFactory factory;

  @BeforeEach
  void setUp() {
    processor = mock(EventProcessor.class);
    contextManager = mock(ProcessorContextManager.class);
    events = mock(NewtEvents.class);
    jsonObjectBuilder = mock(JsonObjectBuilder.class);
    factory = mock(ProcessingResultFactory.class);

    runner = new ProcessorRunnerImpl(
        processor,
        contextManager,
        events,
        "name",
        "id",
        () -> jsonObjectBuilder,
        factory
    );
  }

  @Test
  void process() {
    ProcessorContext context = mock(ProcessorContext.class);
    JsonObject params = mock(JsonObject.class);
    Timer timer = mock(Timer.class);
    Event event = mock(Event.class);
    JsonObject result = mock(JsonObject.class);
    ProcessingResult processingResult = mock(ProcessingResult.class);

    when(contextManager.enterContext()).thenReturn(context);
    Map<String, Duration> times = Collections.emptyMap();
    when(context.getTimes()).thenReturn(times);
    when(context.startTimer("process_method")).thenReturn(timer);
    when(events.openEvent("1")).thenReturn(event);
    Map<@NotNull String, @NotNull List<@NotNull String>> indices = Collections.emptyMap();
    when(event.getCreatedIndices()).thenReturn(indices);
    when(jsonObjectBuilder.build()).thenReturn(result);
    when(factory.create(anyMap(), anyMap(), any(JsonObject.class))).thenReturn(processingResult);


    runner.process("1", params);

    verify(contextManager).enterContext();
    verify(events).openEvent("1");
    verify(context).startTimer("process_method");
    verify(processor).process(event, params, jsonObjectBuilder);
    verify(timer).stop();
    verify(context).close();
    ArgumentCaptor<Map> createdIndicesCaptor = ArgumentCaptor.forClass(Map.class);
    ArgumentCaptor<Map> timesCaptor = ArgumentCaptor.forClass(Map.class);
    ArgumentCaptor<JsonObject> resultCaptor = ArgumentCaptor.forClass(JsonObject.class);
    verify(factory).create(createdIndicesCaptor.capture(), timesCaptor.capture(), resultCaptor.capture());
    assertEquals(indices, createdIndicesCaptor.getValue());
    assertEquals(times, timesCaptor.getValue());
    assertEquals(result, resultCaptor.getValue());
  }

  @Test
  void getProcessorName() {
    assertEquals("name", runner.getProcessorName());
  }

  @Test
  void getProcessorId() {
    assertEquals("id", runner.getProcessorId());
  }

  @Test
  void close() {
    runner.close();

    verify(processor).shutdown();
  }
}

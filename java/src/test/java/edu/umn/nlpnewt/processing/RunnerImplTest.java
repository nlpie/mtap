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
import org.jetbrains.annotations.NotNull;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.stubbing.Answer;

import java.time.Duration;
import java.util.Collections;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.*;

class RunnerImplTest {

  private EventProcessor processor;
  private EventsClient events;
  private ContextManager contextManager;
  private RunnerImpl runner;

  @BeforeEach
  void setUp() {
    processor = mock(EventProcessor.class);
    events = mock(EventsClient.class);
    contextManager = mock(ContextManager.class);
    runner = new RunnerImpl(
        processor,
        events,
        contextManager,
        "processorName",
        "processorId"
    );
  }

  @Test
  void process() {
    ProcessorContext context = mock(ProcessorContext.class);
    when(contextManager.enterContext()).thenReturn(context);

    Map<String, Duration> times = Collections.emptyMap();
    when(context.getTimes()).thenReturn(times);

    Timer timer = mock(Timer.class);
    when(context.startTimer("process_method")).thenReturn(timer);

    JsonObject params = mock(JsonObject.class);
    doAnswer((Answer<Void>) invocation -> {
      JsonObjectBuilder builder = invocation.getArgument(2);
      builder.setProperty("foo", "bar");
      return null;
    }).when(processor).process(any(Event.class), same(params), any(JsonObjectBuilder.class));

    ProcessingResult processingResult = runner.process("1", params);

    verify(events).openEvent("1", false);
    verify(contextManager).enterContext();
    verify(context).startTimer("process_method");
    verify(processor).process(any(Event.class), same(params), any(JsonObjectBuilder.class));
    verify(timer).stop();
    verify(context).close();

    assertEquals(times, processingResult.getTimes());
    assertEquals("bar", processingResult.getResult().getStringValue("foo"));
  }

  @Test
  void getProcessorName() {
    assertEquals("processorName", runner.getProcessorName());
  }

  @Test
  void getProcessorId() {
    assertEquals("processorId", runner.getProcessorId());
  }

  @Test
  void close() {
    runner.close();

    verify(processor).shutdown();
  }
}

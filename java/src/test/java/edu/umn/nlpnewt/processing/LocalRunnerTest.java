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

import edu.umn.nlpnewt.common.JsonObject;
import edu.umn.nlpnewt.common.JsonObjectBuilder;
import edu.umn.nlpnewt.common.JsonObjectImpl;
import edu.umn.nlpnewt.model.Event;
import edu.umn.nlpnewt.model.EventsClient;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.stubbing.Answer;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.*;

class LocalRunnerTest {

  private EventProcessor processor;
  private EventsClient events;
  private LocalRunner runner;

  @BeforeEach
  void setUp() {
    processor = mock(EventProcessor.class);
    events = mock(EventsClient.class);
    runner = new LocalRunner(
        events,
        processor,
        "processorName",
        "processorId"
    );
  }

  @Test
  void process() {
    JsonObject params = JsonObjectImpl.newBuilder().build();
    doAnswer((Answer<Void>) invocation -> {
      JsonObjectBuilder builder = invocation.getArgument(2);
      builder.setProperty("foo", "bar");
      return null;
    }).when(processor).process(any(Event.class), same(params), any(JsonObjectBuilder.class));

    ProcessingResult processingResult = runner.process("1", params);

    verify(processor).setContext(any(ProcessorContext.class));
    verify(events).openEvent("1", false);
    verify(processor).process(any(Event.class), same(params), any(JsonObjectBuilder.class));

    assertTrue(processingResult.getTimes().get("processorId:process_method").toNanos() > 0);
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

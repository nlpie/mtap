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

import edu.umn.nlpie.mtap.model.Event;
import edu.umn.nlpie.mtap.model.EventsClient;
import edu.umn.nlpie.mtap.common.JsonObject;
import edu.umn.nlpie.mtap.common.JsonObjectBuilder;
import edu.umn.nlpie.mtap.common.JsonObjectImpl;
import edu.umn.nlpie.mtap.model.EventsClientPool;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.stubbing.Answer;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.*;

class LocalProcessorRunnerTest {

  private EventProcessor processor;
  private EventsClientPool pool;
  private EventsClient events;
  private LocalProcessorRunner runner;

  @BeforeEach
  void setUp() {
    processor = mock(EventProcessor.class);
    pool = mock(EventsClientPool.class);
    events = mock(EventsClient.class);
    runner = new LocalProcessorRunner(
        pool,
        processor
    );
  }

  @SuppressWarnings("rawtypes")
  @Test
  void process() {
    JsonObject params = JsonObjectImpl.newBuilder().build();
    doAnswer((Answer<Void>) invocation -> {
      JsonObjectBuilder builder = invocation.getArgument(2);
      builder.setProperty("foo", "bar");
      return null;
    }).when(processor).process(any(Event.class), same(params), any(JsonObjectBuilder.class));
    doReturn(events).when(pool).instanceFor("1");

    ProcessingResult processingResult = runner.process("1", "1", params);

    verify(events).openEvent("1", false);
    verify(processor).process(any(Event.class), same(params), any(JsonObjectBuilder.class));

    assertTrue(processingResult.getTimes().get("process_method").toNanos() > 0);
    assertEquals("bar", processingResult.getResult().getStringValue("foo"));
  }

  @Test
  void close() throws InterruptedException {
    runner.close();

    verify(processor).shutdown();
  }
}

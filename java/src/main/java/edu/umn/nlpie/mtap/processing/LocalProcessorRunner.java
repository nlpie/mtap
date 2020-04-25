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

import edu.umn.nlpie.mtap.Internal;
import edu.umn.nlpie.mtap.model.Event;
import edu.umn.nlpie.mtap.model.EventsClient;
import edu.umn.nlpie.mtap.common.JsonObject;
import edu.umn.nlpie.mtap.common.JsonObjectBuilder;
import edu.umn.nlpie.mtap.common.JsonObjectImpl;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.Map;

@Internal
class LocalProcessorRunner implements ProcessorRunner {
  private final EventsClient client;
  private final EventProcessor processor;
  private final Map<String, Object> processorMeta;

  LocalProcessorRunner(
      EventsClient client,
      EventProcessor processor
  ) {
    this.client = client;
    this.processor = processor;

    processorMeta = processor.getProcessorMetadata();
  }

  @Override
  public ProcessingResult process(String eventID, JsonObject params) {
    try (ProcessorContext context = ProcessorBase.enterContext()) {
      try (Event event = Event.newBuilder().withEventID(eventID).withEventsClient(client).build()) {
        JsonObjectBuilder resultBuilder = JsonObjectImpl.newBuilder();
        Stopwatch stopwatch = ProcessorBase.startedStopwatch("process_method");
        processor.process(event, params, resultBuilder);
        stopwatch.stop();
        return new ProcessingResult(
            event.getCreatedIndices(),
            context.getTimes(),
            resultBuilder.build()
        );
      }
    }
  }

  @Override
  public Map<String, Object> getProcessorMeta() {
    return processorMeta;
  }

  @Override
  public void close() {
    processor.shutdown();
  }
}

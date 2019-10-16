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
class LocalRunner implements Runner {
  private final EventsClient client;
  private final EventProcessor processor;
  private final String processorName;
  private final String processorId;
  private final Map<String, Object> processorMeta;

  LocalRunner(EventsClient client,
              EventProcessor processor,
              String processorName,
              String processorId) {
    this.client = client;
    this.processor = processor;
    this.processorName = processorName;
    this.processorId = processorId;

    processorMeta = processor.getProcessorMetadata();
  }

  public static @NotNull Builder forProcessor(@NotNull EventProcessor processor) {
    return new Builder(processor);
  }

  @Override
  public ProcessingResult process(String eventID, JsonObject params) {
    try (ProcessorContext context = ProcessorBase.enterContext(processorId)) {
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

  EventProcessor getProcessor() {
    return processor;
  }

  @Override
  public String getProcessorName() {
    return processorName;
  }

  @Override
  public String getProcessorId() {
    return processorId;
  }

  @Override
  public Map<String, Object> getProcessorMeta() {
    return processorMeta;
  }



  @Override
  public void close() {
    processor.shutdown();
  }

  public static class Builder {
    private final EventProcessor processor;
    private EventsClient client;
    private String processorName;
    private String processorId;

    public Builder(EventProcessor processor) {
      this.processor = processor;
    }

    public @NotNull Builder withClient(EventsClient client) {
      this.client = client;
      return this;
    }

    public @NotNull Builder withProcessorName(@Nullable String processorName) {
      this.processorName = processorName;
      return this;
    }

    public @NotNull Builder withProcessorId(String processorId) {
      this.processorId = processorId;
      return this;
    }

    public Runner build() {
      String processorName = this.processorName;
      if (processorName == null) {
        processorName = processor.getProcessorName();
      }
      String processorId = this.processorId;
      if (processorId == null) {
        processorId = processorName;
      }
      return new LocalRunner(
          client,
          processor,
          processorName,
          processorId
      );
    }
  }
}

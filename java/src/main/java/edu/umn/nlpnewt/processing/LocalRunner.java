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

import edu.umn.nlpnewt.Internal;
import edu.umn.nlpnewt.common.JsonObject;
import edu.umn.nlpnewt.common.JsonObjectBuilder;
import edu.umn.nlpnewt.common.JsonObjectImpl;
import edu.umn.nlpnewt.model.Event;
import edu.umn.nlpnewt.model.EventsClient;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.time.Duration;
import java.util.Map;

@Internal
class LocalRunner implements Runner {
  private final EventsClient client;
  private final EventProcessor processor;
  private final String processorName;
  private final String processorId;

  LocalRunner(EventsClient client,
              EventProcessor processor,
              String processorName,
              String processorId) {
    this.client = client;
    this.processor = processor;
    this.processorName = processorName;
    this.processorId = processorId;
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
  public Processor getProcessorMeta() {
    return processor.getClass().getAnnotation(Processor.class);
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

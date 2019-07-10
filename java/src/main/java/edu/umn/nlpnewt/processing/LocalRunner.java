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

import com.google.common.base.Stopwatch;
import edu.umn.nlpnewt.Internal;
import edu.umn.nlpnewt.common.JsonObject;
import edu.umn.nlpnewt.common.JsonObjectBuilder;
import edu.umn.nlpnewt.common.JsonObjectImpl;
import edu.umn.nlpnewt.model.Event;
import edu.umn.nlpnewt.model.EventsClient;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

@Internal
class LocalRunner implements Runner {
  private final ProcessorContext context = new Context();
  private final ThreadLocal<ProcessorLocal> threadLocal = new ThreadLocal<>();
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
    processor.setContext(context);
    this.processorName = processorName;
    this.processorId = processorId;
  }

  public static @NotNull Builder forProcessor(@NotNull EventProcessor processor) {
    return new Builder(processor);
  }

  @Override
  public ProcessingResult process(String eventID, JsonObject params) {
    try (ProcessorLocal ignored = new ProcessorLocal()) {
      try (Event event = Event.newBuilder().withEventID(eventID).withEventsClient(client).build()) {
        JsonObjectBuilder resultBuilder = JsonObjectImpl.newBuilder();
        Timer timer = context.startTimer("process_method");
        processor.process(event, params, resultBuilder);
        timer.stop();
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

  private class Context implements ProcessorContext {
    @Override
    public @NotNull Timer startTimer(String key) {
      ProcessorLocal local = threadLocal.get();
      Stopwatch stopwatch = Stopwatch.createStarted();

      return new Timer() {
        @Override
        public void stop() {
          if (!local.active) {
            throw new IllegalStateException("Processor context has been exited prior to stop.");
          }
          local.times.put(processorId + ":" + key, stopwatch.elapsed());
        }

        @Override
        public void close() {
          stop();
        }
      };
    }

    @Override
    public Map<String, Duration> getTimes() {
      return threadLocal.get().times;
    }
  }

  private class ProcessorLocal implements AutoCloseable {
    private final Map<String, Duration> times = new HashMap<>();

    private boolean active = true;

    public ProcessorLocal() {
      threadLocal.set(this);
    }

    @Override
    public void close() {
      active = false;
      threadLocal.remove();
    }
  }
}

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

package edu.umn.nlpnewt.internal;

import com.google.common.base.Stopwatch;
import edu.umn.nlpnewt.*;
import io.grpc.health.v1.HealthCheckResponse;
import org.jetbrains.annotations.NotNull;

import java.io.Closeable;
import java.io.IOException;
import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

import static edu.umn.nlpnewt.Newt.PROCESSOR_SERVICE_TAG;

class ProcessorRunnerImpl implements ProcessorRunner {
  private final ThreadLocal<ProcessorThreadContext> threadContext = new ThreadLocal<>();
  private final InternalOptions internalOptions;
  private final EventProcessor processor;
  private final String identifier;
  private Runnable deregister = null;

  ProcessorRunnerImpl(InternalOptions internalOptions, EventProcessor processor, String identifier) {
    this.internalOptions = internalOptions;
    this.processor = processor;
    this.identifier = identifier;
  }

  @Override
  public @NotNull ProcessorThreadContext enterContext() {
    ProcessorThreadContext processorThreadContext = new ProcessorThreadContext();
    threadContext.set(processorThreadContext);
    return processorThreadContext;
  }

  @NotNull
  private ProcessorThreadContext getCurrent() {
    ProcessorThreadContext local = threadContext.get();
    if (local == null) {
      throw new IllegalStateException("Attempting to use processor context outside of a " +
          "managed process call.");
    }
    return local;
  }

  @Override
  public void startedServing(String address, int port) {
    RegistrationAndHealthManager registrationAndHealthManager = internalOptions.getRegistrationAndHealthManager();
    registrationAndHealthManager.setHealthAddress(address);
    registrationAndHealthManager.setHealthPort(port);
    deregister = registrationAndHealthManager.startedService(identifier, PROCESSOR_SERVICE_TAG);
  }

  @Override
  public void stoppedServing() {
    if (deregister != null) {
      deregister.run();
    }
    processor.shutdown();
  }

  @Override
  public ProcessingResult process(String eventID, JsonObject params) throws IOException {
    JsonObject.Builder resultBuilder = JsonObject.newBuilder();
    try (ProcessorThreadContext context = enterContext()) {
      try (Event event = internalOptions.getEvents().openEvent(eventID)) {
        Timer timer = context.startTimer("process_method");
        processor.process(event, params, resultBuilder);
        timer.stop();
        return new ProcessingResult(event.getCreatedIndices(), context.getTimes(),
            resultBuilder.build());
      }
    }
  }

  public class Context implements ProcessorContext {
    @Override
    public void updateServingStatus(HealthCheckResponse.ServingStatus status) {
      internalOptions.getRegistrationAndHealthManager().setStatus(identifier, status);
    }

    @Override
    public @NotNull Timer startTimer(String key) {
      return getCurrent().startTimer(key);
    }

    @Override
    public Map<String, Duration> getTimes() {
      return getCurrent().getTimes();
    }

    @Override
    public String getIdentifier() {
      return identifier;
    }

    @Override
    public NewtEvents getEvents() {
      return internalOptions.getEvents();
    }
  }

  public class ProcessorThreadContext implements Closeable {
    private final Map<String, Duration> times = new HashMap<>();

    private boolean active = true;

    @NotNull Timer startTimer(String key) {
      Stopwatch stopwatch = Stopwatch.createStarted();

      return new Timer() {
        @Override
        public void stop() {
          if (!active) {
            throw new IllegalStateException("Processor context has been exited prior to stop.");
          }
          times.put(identifier + ":" + key, stopwatch.elapsed());
        }

        @Override
        public void close() {
          stop();
        }
      };
    }

    Map<String, Duration> getTimes() {
      return times;
    }

    @Override
    public void close() {
      active = false;
      threadContext.remove();
    }
  }
}

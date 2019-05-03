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

package edu.umn.nlpnewt;

import com.google.common.base.Stopwatch;
import edu.umn.nlpnewt.internal.processing.RegistrationAndHealthManager;
import io.grpc.health.v1.HealthCheckResponse;
import org.jetbrains.annotations.NotNull;

import java.io.Closeable;
import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

public class ProcessorContextManager {
  private final Context context = new Context();

  private final ThreadLocal<ProcessorThreadContext> threadContext = new ThreadLocal<>();

  private final String identifier;
  private final NewtEvents newtEvents;
  private final RegistrationAndHealthManager registrationAndHealthManager;


  public ProcessorContextManager(
      String identifier,
      NewtEvents newtEvents,
      RegistrationAndHealthManager registrationAndHealthManager
  ) {
    this.identifier = identifier;
    this.newtEvents = newtEvents;
    this.registrationAndHealthManager = registrationAndHealthManager;
  }

  public ProcessorContext enterContext() {
    ProcessorThreadContext processorThreadContext = new ProcessorThreadContext();
    threadContext.set(processorThreadContext);
    return processorThreadContext;
  }

  private ProcessorContext getCurrent() {
    ProcessorThreadContext local = threadContext.get();
    if (local == null) {
      throw new IllegalStateException("Attempting to use processor context outside of a " +
          "managed process call.");
    }
    return local;
  }

  public ProcessorContext getContext() {
    return context;
  }

  public class Context implements ProcessorContext {
    @Override
    public void updateServingStatus(HealthCheckResponse.ServingStatus status) {
      registrationAndHealthManager.setStatus(identifier, status);
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
      return newtEvents;
    }

    @Override
    public void close() { }
  }

  public class ProcessorThreadContext extends Context implements Closeable {
    private final Map<String, Duration> times = new HashMap<>();

    private boolean active = true;

    @Override
    public @NotNull Timer startTimer(String key) {
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

    @Override
    public Map<String, Duration> getTimes() {
      return times;
    }

    @Override
    public void close() {
      active = false;
      threadContext.remove();
    }
  }
}


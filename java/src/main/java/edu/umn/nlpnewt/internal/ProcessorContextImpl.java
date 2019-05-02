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
import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

import static edu.umn.nlpnewt.Newt.PROCESSOR_SERVICE_TAG;

class ProcessorContextImpl implements ProcessorContextManager {
  private final ThreadLocal<ProcessorThreadContext> threadContext = new ThreadLocal<>();
  private final Config config;
  private final ProcessorServerOptions options;
  private final RegistrationAndHealthManager registrationAndHealthManager;

  private String identifier = null;
  private NewtEvents events = null;
  private AbstractEventProcessor processor = null;
  private Runnable deregister;

  ProcessorContextImpl(
      Config config,
      ProcessorServerOptions options,
      RegistrationAndHealthManager registrationAndHealthManager
  ) {
    this.config = config;
    this.options = options;
    this.registrationAndHealthManager = registrationAndHealthManager;
  }

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
    if (events == null) {
      events = NewtEventsImpl.create(config, options.getEventsTarget());
    }
    return events;
  }

  @Override
  public @NotNull Closeable enterContext() {
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
  public AbstractEventProcessor getProcessor() {
    if (processor != null) {
      return processor;
    }
    processor = options.getProcessor();
    if (processor == null) {
      try {
        Class<? extends AbstractEventProcessor> processorClass = options.getProcessorClass();
        if (processorClass == null) {
          throw new IllegalStateException("Neither processor nor processorClass was set");
        }
        try {
          Constructor<? extends AbstractEventProcessor> constructor = processorClass.getConstructor(ProcessorContext.class);
          processor = constructor.newInstance(this);
        } catch (NoSuchMethodException ignored) {
          // fall back to default constructor
          Constructor<? extends AbstractEventProcessor> constructor = processorClass.getConstructor();
          processor = constructor.newInstance();
        }
      } catch (NoSuchMethodException | IllegalAccessException | InstantiationException | InvocationTargetException e) {
        throw new IllegalStateException("Unable to instantiate processor.", e);
      }
    }
    if (identifier == null) {
      identifier = processor.getClass().getAnnotation(Processor.class).value();
    }
    return processor;
  }

  @Override
  public void startedServing(String address, int port) {
    registrationAndHealthManager.setHealthAddress(address);
    registrationAndHealthManager.setHealthPort(port);
    deregister = registrationAndHealthManager.startedService(identifier, PROCESSOR_SERVICE_TAG);
  }

  @Override
  public void stoppedServing() {
    if (deregister != null) {
      deregister.run();
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
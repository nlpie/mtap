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
import edu.umn.nlpnewt.ProcessorContext;
import edu.umn.nlpnewt.ProcessorServerOptions;
import edu.umn.nlpnewt.Timer;
import io.grpc.health.v1.HealthCheckResponse;
import io.grpc.services.HealthStatusManager;
import org.jetbrains.annotations.NotNull;

import java.io.Closeable;
import java.io.IOException;
import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

class ProcessorContextManager {
  private final ThreadLocal<ProcessorThreadContext> threadContext = new ThreadLocal<>();
  private final String identifier;

  private final HealthStatusManager healthStatusManager;

  private final ProcessorContext shim = new ProcessorContext() {
    @Override
    public void updateServingStatus(HealthCheckResponse.ServingStatus status) {
      healthStatusManager.setStatus(identifier, status);
    }

    @Override
    public @NotNull Timer startTimer(String key) {
      return getCurrent().startTimer(key);
    }

    @Override
    public Map<String, Duration> getTimes() {
      return getCurrent().getTimes();
    }
  };

  ProcessorContextManager(String identifier, HealthStatusManager healthStatusManager) {
    this.identifier = identifier;
    this.healthStatusManager = healthStatusManager;
  }

  @NotNull ProcessorThreadContext enterContext() {
    ProcessorThreadContext processorThreadContext = new ProcessorThreadContext();
    threadContext.set(processorThreadContext);
    return processorThreadContext;
  }

  @NotNull ProcessorThreadContext getCurrent() {
    ProcessorThreadContext local = threadContext.get();
    if (local == null) {
      throw new IllegalStateException("Attempting to use processor context outside of a " +
          "managed process call.");
    }
    return local;
  }

  @NotNull ProcessorContext getShim() {
    return shim;
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

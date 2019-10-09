/*
 * Copyright 2019 Regents of the University of Minnesota
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
import edu.umn.nlpnewt.model.Event;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.time.Duration;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

/**
 * Contains functionality related to the handling of processor contexts.
 */
public abstract class ProcessorBase {
  private static final ThreadLocal<ProcessorContextImpl> contextLocal = new ThreadLocal<>();

  @Internal
  public static @NotNull ProcessorContext enterContext(@NotNull String identifier) {
    ProcessorContextImpl existing = contextLocal.get();
    if (existing != null) {
      identifier = existing + "." + identifier;
    }
    ProcessorContextImpl context = new ProcessorContextImpl(existing, identifier);
    contextLocal.set(context);
    return context;
  }

  @Internal
  public static @Nullable ProcessorContext getCurrentContext() {
    return contextLocal.get();
  }

  /**
   * Starts a stopwatch keyed by {@code key} that will attach its duration to the output of the
   * processor.
   * <p>
   * Must be called inside a
   * {@link EventProcessor#process(Event, JsonObject, JsonObjectBuilder)} or
   * {@link EventProcessor#process(Event, JsonObject, JsonObjectBuilder)} method.
   *
   * @param key The key to store the time under.
   * @return A timer object that will automatically store the time elapsed in the processing
   * context.
   */
  public static @NotNull Stopwatch startedStopwatch(String key) {
    Stopwatch stopwatch = new Stopwatch(getCurrentContext(), key);
    stopwatch.start();
    return stopwatch;
  }

  /**
   * Creates a stopwatch keyed by {@code key} that will attach its duration to the output of the
   * processor.
   *
   * @param key The key to store the time under.
   * @return A timer object that will automatically store the time elapsed in the processing
   * context.
   */
  public static @NotNull Stopwatch unstartedStopwatch(String key) {
    return new Stopwatch(getCurrentContext(), key);
  }

  private static class ProcessorContextImpl implements ProcessorContext {
    private final Map<String, Duration> times = new HashMap<>();
    private final ProcessorContextImpl parent;
    private final String identifier;
    private boolean active = true;

    ProcessorContextImpl(@Nullable ProcessorContextImpl parent, @NotNull String identifier) {
      this.parent = parent;
      this.identifier = Objects.requireNonNull(identifier);
    }

    @Override
    public void putTime(@NotNull String key, @NotNull Duration duration) {
      if (!active) {
        throw new IllegalStateException("Attempted to add time to an inactive processor context.");
      }
      times.put(identifier + ":" + key, duration);
    }

    @Override
    public @NotNull Map<String, Duration> getTimes() {
      return new HashMap<>(times);
    }

    @Override
    public void close() {
      active = false;
      contextLocal.set(parent);
    }
  }
}

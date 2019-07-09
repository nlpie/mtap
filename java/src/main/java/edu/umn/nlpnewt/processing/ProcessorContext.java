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

import edu.umn.nlpnewt.common.JsonObject;
import edu.umn.nlpnewt.common.JsonObjectBuilder;
import edu.umn.nlpnewt.model.Event;
import io.grpc.health.v1.HealthCheckResponse;
import org.jetbrains.annotations.NotNull;

import java.time.Duration;
import java.util.Map;

/**
 * Interface for a processing context which gets passed to processors upon construction.
 *
 * The framework will automatically enter a thread context before the
 * {@link EventProcessor#process(Event, JsonObject, JsonObjectBuilder)} or
 * {@link EventProcessor#process(Event, JsonObject, JsonObjectBuilder)} methods are
 * called, and automatically exit after.
 */
public interface ProcessorContext {
  /**
   * Starts a timer keyed by {@code key}.
   * <p>
   * Must be called inside a
   * {@link EventProcessor#process(Event, JsonObject, JsonObjectBuilder)} or
   * {@link EventProcessor#process(Event, JsonObject, JsonObjectBuilder)} method.
   *
   * @param key The key to store the time under.
   *
   * @return A timer object that will automatically store the time elapsed in the processing
   * context.
   */
  @NotNull Timer startTimer(String key);

  /**
   * Returns all of the times that have completed timing in the current thread context.
   * <p>
   * Must be called inside a
   * {@link EventProcessor#process(Event, JsonObject, JsonObjectBuilder)} or
   * {@link EventProcessor#process(Event, JsonObject, JsonObjectBuilder)} method.
   *
   * @return Map of times.
   */
  Map<String, Duration> getTimes();
}

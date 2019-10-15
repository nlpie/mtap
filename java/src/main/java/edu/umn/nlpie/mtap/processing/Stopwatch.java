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

import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.time.Duration;

/**
 * A stopwatch that can be used to time some piece of work in a processing context and
 * automatically add the time to the processing response.
 * <p>
 * It is closeable so that the timer can be used via the try-with-resources block:
 * <pre>
 *   {@code
 *   try (Timer timer = start("process_step_1")) {
 *     // do process step one.
 *   }
 *   }
 * </pre>
 */
public class Stopwatch implements AutoCloseable {
  private final com.google.common.base.Stopwatch stopwatch = com.google.common.base.Stopwatch.createUnstarted();
  private final @Nullable ProcessorContext context;
  private final String key;

  public Stopwatch(@Nullable ProcessorContext context, String key) {
    this.context = context;
    this.key = key;
  }

  /**
   * Starts the timer.
   */
  public void start() {
    stopwatch.start();
  }

  /**
   * Stops/pauses the timer.
   */
  public void stop() {
    stopwatch.stop();
    if (context != null) {
      context.putTime(key, stopwatch.elapsed());
    }
  }

  /**
   * Returns the total elapsed duration.
   *
   * @return The total duration across all start/stop calls.
   */
  public @NotNull Duration elapsed() {
    return stopwatch.elapsed();
  }

  /**
   * Stops the timer, recording the time elapsed.
   */
  @Override
  public void close() {
    if (stopwatch.isRunning()) {
      stopwatch.stop();
    }
    if (context != null) {
      context.putTime(key, stopwatch.elapsed());
    }
  }
}

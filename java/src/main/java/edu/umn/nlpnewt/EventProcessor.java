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
package edu.umn.nlpnewt;

import org.jetbrains.annotations.NotNull;

/**
 * A processor of events.
 */
public interface EventProcessor {
  /**
   * Performs processing of an event.
   *
   * @param event  event object to process.
   * @param params processing parameters.
   * @param result result map
   */
  void process(
      @NotNull Event event,
      @NotNull JsonObject params,
      @NotNull JsonObject.Builder result
  );

  /**
   * Called when the processor service is going to shutdown serving so the processor can free
   * any resources associated with the processor.
   */
  @SuppressWarnings("EmptyMethod")
  default void shutdown() { }
}

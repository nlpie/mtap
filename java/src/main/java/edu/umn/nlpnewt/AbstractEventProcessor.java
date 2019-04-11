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

import grpc.health.v1.HealthOuterClass.HealthCheckResponse.ServingStatus;
import org.jetbrains.annotations.NotNull;

/**
 * Abstract base class for a processor of {@link Event} objects.
 * <p>
 * Example:
 * <pre>
 *     &#64;Processor('example-processor')
 *     public class ExampleProcessor extends AbstractEventProcessor {
 *       &#64;Override
 *       public void process(Event event, JsonObject params, JsonObject.Builder result) {
 *         // do processing on event
 *       }
 *     }
 * </pre>
 * <p>
 * The no-argument default constructor is required for instantiation via reflection. At runtime,
 * the {@link AbstractEventProcessor#process(Event, JsonObject, JsonObject.Builder)} method
 * may be called simultaneously from multiple threads, so the implementing class is responsible for
 * ensuring thread-safety.
 */
public abstract class AbstractEventProcessor {
  public ServingStatus getServingStatus() {
    return ServingStatus.SERVING;
  }

  /**
   * Method where the subclass implementation does its processing on the event.
   *
   * @param event  event object to process.
   * @param params processing parameters.
   * @param result result map
   */
  public abstract void process(
      @NotNull Event event,
      @NotNull JsonObject params,
      @NotNull JsonObject.Builder result
  );

  /**
   * Called when the processor service is going to stop serving so the processor can free
   * any resources associated with the processor.
   *
   * @throws Exception any exception that the subclass processor throws while shutting down.
   */
  public void shutdown() throws Exception {
    // this method left purposefully empty
  }
}

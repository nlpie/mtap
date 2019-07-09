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

import edu.umn.nlpnewt.model.Event;
import edu.umn.nlpnewt.common.JsonObject;
import edu.umn.nlpnewt.common.JsonObjectBuilder;
import org.jetbrains.annotations.NotNull;

/**
 * Abstract base class for a processor of {@link Event} objects.
 * <p>
 * Example:
 * <pre>
 *     &#64;Processor('example-processor')
 *     public class ExampleProcessor extends EventProcessor {
 *       &#64;Override
 *       public void process(Event event, JsonObject params, JsonObject.Builder result) {
 *         // do processing on event
 *       }
 *     }
 * </pre>
 * <p>
 * The no-argument default constructor is required for instantiation via reflection. At runtime,
 * the {@link EventProcessor#process(Event, JsonObject, JsonObjectBuilder)} method
 * may be called simultaneously from multiple threads, so the implementing class is responsible for
 * ensuring thread-safety.
 */
public abstract class EventProcessor {
  private ProcessorContext context = null;

  /**
   * Used by NLP-NEWT to set the processor context.
   *
   * @param context the processor context.
   */
  public void setContext(@NotNull ProcessorContext context) {
    this.context = context;
  }

  /**
   * The current processor context. Will always be non-null once the processor is running.
   *
   * @return A context object that can be used by the processor.
   */
  protected @NotNull ProcessorContext getContext() {
    return context;
  }

  /**
   * Performs processing of an event.
   * @param event  event object to process.
   * @param params processing parameters.
   * @param result result map
   */
  public abstract void process(
      @NotNull Event event,
      @NotNull JsonObject params,
      @NotNull JsonObjectBuilder result
  );

  /**
   * The processor name as specified by the {@link Processor} annotation.
   *
   * @return A string identifier for the processor.
   */
  public String getProcessorName() {
    return getClass().getAnnotation(Processor.class).value();
  }

  /**
   * Called when the processor service is going to shutdown serving so the processor can free
   * any resources associated with the processor.
   */
  @SuppressWarnings("EmptyMethod")
  public void shutdown() { }
}

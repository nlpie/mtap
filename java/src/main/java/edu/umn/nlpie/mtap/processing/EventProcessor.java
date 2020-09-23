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

import edu.umn.nlpie.mtap.common.JsonObject;
import edu.umn.nlpie.mtap.common.JsonObjectBuilder;
import edu.umn.nlpie.mtap.model.Event;
import edu.umn.nlpie.mtap.model.ProtoLabelAdapter;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.*;

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
public abstract class EventProcessor extends ProcessorBase {
  private final @NotNull Map<@NotNull String, @NotNull ProtoLabelAdapter<?>> defaultAdapters = new HashMap<>();

  /**
   * Returns a map of this processor's metadata as specified in the {@link Processor} annotation.
   *
   * @return A map of the processor's metadata.
   */
  public @NotNull Map<@NotNull String, @Nullable Object> getProcessorMetadata() {
    return metadataMap(getClass());
  }

  /**
   * Adds a default adapter for a specified label index name.
   *
   * @param indexName The index name.
   * @param adapter   The adapter.
   */
  protected void addDefaultAdapter(@NotNull String indexName,
                                   @NotNull ProtoLabelAdapter<?> adapter) {
    defaultAdapters.put(indexName, adapter);
  }

  /**
   * Adds a map of default adapters.
   *
   * @param adapterMap A mapping from index names to label adapters.
   */
  protected void addAllDefaultAdapters(@NotNull Map<@NotNull String,
      @NotNull ProtoLabelAdapter<?>> adapterMap) {
    this.defaultAdapters.putAll(adapterMap);
  }

  /**
   * An unmodifiable view of the default label adapters.
   *
   * @return default adapters map.
   */
  public @NotNull Map<@NotNull String, @NotNull ProtoLabelAdapter<?>> getDefaultAdapters() {
    return Collections.unmodifiableMap(defaultAdapters);
  }

  /**
   * Performs processing of an event.
   *
   * @param event  event object to process.
   * @param params processing parameters.
   * @param result result map
   */
  public abstract void process(
      @NotNull Event event,
      @NotNull JsonObject params,
      @NotNull JsonObjectBuilder<?, ?> result
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

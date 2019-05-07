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
 * Abstract base class for a processor of {@link Document} objects.
 * <p>
 * Example:
 * <pre>
 *     &#64;Processor('example-processor')
 *     public class ExampleProcessor extends DocumentProcessorBase {
 *       &#64;Override
 *       protected void process(Document document, JsonObject params, JsonObject.Builder result) {
 *         // do processing on document
 *       }
 *     }
 * </pre>
 * <p>
 * The no-argument default constructor is required for instantiation via reflection. At runtime,
 * the {@link DocumentProcessorBase#process(Document, JsonObject, JsonObjectBuilder)} method
 * may be called simultaneously from multiple threads, so the implementing class is responsible for
 * ensuring thread-safety.
 */
public abstract class DocumentProcessorBase implements EventProcessor {
  @Override
  public final void process(@NotNull Event event,
                            @NotNull JsonObject params,
                            @NotNull JsonObjectBuilder result) {
    String document_name = params.getStringValue("document_name");

    Document document = event.get(document_name);
    process(document, params, result);
  }

  /**
   * Method implemented by subclasses to process documents.
   *  @param document document to process.
   * @param params   processing parameters.
   * @param result   results object.
   */
  protected abstract void process(
      @NotNull Document document,
      @NotNull JsonObject params,
      @NotNull JsonObjectBuilder result
  );
}

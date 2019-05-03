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

package edu.umn.nlpnewt;

/**
 * Abstract base class for a processor of {@link Event} objects.
 * <p>
 * Example:
 * <pre>
 *     &#64;Processor('example-processor')
 *     public class ExampleProcessor extends EventProcessorBase {
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
public abstract class EventProcessorBase implements EventProcessor {

}

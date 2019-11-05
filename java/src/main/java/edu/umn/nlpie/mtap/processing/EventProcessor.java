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
  public static @NotNull Map<String, Object> metadataMap(Class<?> processorClass) {
    Processor processor = processorClass.getAnnotation(Processor.class);
    Map<String, Object> map = new LinkedHashMap<>();
    map.put("name", processor.value());
    if (!"".equals(processor.description())) {
      map.put("description", processor.description());
    }
    String humanName = processor.humanName();
    if ("".equals(humanName)) {
      humanName = processorClass.getSimpleName();
    }
    map.put("human_name", humanName);

    if (processor.inputs().length > 0) {
      List<Map<String, Object>> inputs = new ArrayList<>();
      for (LabelIndexDescription input : processor.inputs()) {
        inputs.add(descToMap(input));
      }
      map.put("inputs", inputs);
    }

    if (processor.outputs().length > 0) {
      List<Map<String, Object>> outputs = new ArrayList<>();
      for (LabelIndexDescription output : processor.outputs()) {
        outputs.add(descToMap(output));
      }
      map.put("outputs", outputs);
    }

    if (processor.parameters().length > 0) {
      List<Map<String, Object>> parameters = new ArrayList<>();
      for (ParameterDescription parameter : processor.parameters()) {
        Map<String, Object> paramMap = new LinkedHashMap<>();
        paramMap.put("name", parameter.name());
        if (!"".equals(parameter.description())) {
          paramMap.put("description", parameter.description());
        }
        paramMap.put("data_type", parameter.dataType());
        paramMap.put("required", parameter.required());
        parameters.add(paramMap);
      }
      map.put("parameters", parameters);
    }

    for (KeyValue keyValue : processor.additionalMetadata()) {
      map.put(keyValue.key(), keyValue.value());
    }

    if (!map.containsKey("implementation_lang")) {
      map.put("implementation_lang", "Java");
    }

    if (!map.containsKey("entry_point")) {
      map.put("entry_point", processorClass.getCanonicalName());
    }

    return map;
  }

  private static @NotNull Map<String, Object> descToMap(LabelIndexDescription input) {
    Map<String, Object> map = new LinkedHashMap<>();
    map.put("name", input.name());
    String reference = input.reference();
    if (!"".equals(reference)) {
      map.put("reference", reference);
    }
    String nameFromParameter = input.nameFromParameter();
    if (!"".equals(nameFromParameter)) {
      map.put("name_from_parameter", nameFromParameter);
    }
    if (!"".equals(input.description())) {
      map.put("description", input.description());
    }
    if (input.properties().length > 0) {
      List<Map<String, Object>> properties = new ArrayList<>();
      for (PropertyDescription property : input.properties()) {
        Map<String, Object> propertyMap = new LinkedHashMap<>();
        propertyMap.put("name", property.name());
        if (!"".equals(property.description())) {
          propertyMap.put("description", property.description());
        }
        if (!"".equals(property.dataType())) {
          propertyMap.put("data_type", property.dataType());
        }
        propertyMap.put("nullable", property.nullable());
        properties.add(propertyMap);
      }
      map.put("properties", properties);
    }
    return map;
  }

  /**
   * Returns a map of this processor's metadata as specified in the {@link Processor} annotation.
   *
   * @return A map of the processor's metadata.
   */
  public @NotNull Map<@NotNull String, @Nullable Object> getProcessorMetadata() {
    return metadataMap(getClass());
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

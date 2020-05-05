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

import edu.umn.nlpie.mtap.Internal;
import edu.umn.nlpie.mtap.model.Event;
import edu.umn.nlpie.mtap.common.JsonObject;
import edu.umn.nlpie.mtap.common.JsonObjectBuilder;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.time.Duration;
import java.util.*;

/**
 * Contains functionality related to the handling of processor contexts.
 */
public abstract class ProcessorBase {
  private static final ThreadLocal<ProcessorContextImpl> contextLocal = new ThreadLocal<>();

  @Internal
  public static @NotNull ProcessorContext enterContext() {
    ProcessorContextImpl existing = contextLocal.get();
    ProcessorContextImpl context = new ProcessorContextImpl(existing);
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

  private static class ProcessorContextImpl implements ProcessorContext {
    private final Map<String, Duration> times = new HashMap<>();
    private final ProcessorContextImpl parent;
    private boolean active = true;

    ProcessorContextImpl(@Nullable ProcessorContextImpl parent) {
      this.parent = parent;
    }

    @Override
    public void putTime(@NotNull String key, @NotNull Duration duration) {
      if (!active) {
        throw new IllegalStateException("Attempted to add time to an inactive processor context.");
      }
      times.compute(key, (unused, value) -> {
        if (value != null) {
          value = value.plus(duration);
        } else {
          value = duration;
        }
        return value;
      });
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

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

package edu.umn.nlpie.mtap.utilities;

import edu.umn.nlpie.mtap.processing.LabelIndexDescription;
import edu.umn.nlpie.mtap.processing.ParameterDescription;
import edu.umn.nlpie.mtap.processing.Processor;
import edu.umn.nlpie.mtap.processing.PropertyDescription;
import org.jetbrains.annotations.NotNull;
import org.kohsuke.args4j.Argument;
import org.kohsuke.args4j.CmdLineException;
import org.kohsuke.args4j.CmdLineParser;
import org.yaml.snakeyaml.Yaml;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.kohsuke.args4j.OptionHandlerFilter.ALL;

/**
 * Utilities for printing processor metadata.
 */
public class PrintProcessorMetadata {
  @Argument(
      usage = "The output yaml file.",
      metaVar = "OUTPUT_FILE",
      required = true
  )
  private Path outputPath = Paths.get("processors.yaml");

  @Argument(
      usage = "The fully-qualified processor class names to print metadata for.",
      metaVar = "PROCESSOR_CLASS",
      required = true,
      multiValued = true,
      index = 1
  )
  private String[] classNames;

  public static Map<String, Object> toMap(Class<?> processorClass) {
    Processor processor = processorClass.getAnnotation(Processor.class);
    Map<String, Object> map = new HashMap<>();
    map.put("name", processor.value());
    map.put("description", processor.description());
    String entryPoint = processor.entryPoint();
    if ("".equals(entryPoint)) {
      entryPoint = processorClass.getCanonicalName();
    }
    map.put("entry_point", entryPoint);
    map.put("language", processor.language());

    List<Map<String, Object>> inputs = new ArrayList<>();
    for (LabelIndexDescription input : processor.inputs()) {
      inputs.add(descToMap(input));
    }
    map.put("inputs", inputs);

    List<Map<String, Object>> outputs = new ArrayList<>();
    for (LabelIndexDescription output : processor.outputs()) {
      outputs.add(descToMap(output));
    }
    map.put("outputs", outputs);

    List<Map<String, Object>> parameters = new ArrayList<>();
    for (ParameterDescription parameter : processor.parameters()) {
      Map<String, Object> paramMap = new HashMap<>();
      paramMap.put("name", parameter.name());
      paramMap.put("description", parameter.description());
      paramMap.put("data_type", parameter.dataType());
      paramMap.put("required", parameter.required());
      parameters.add(paramMap);
    }
    map.put("parameters", parameters);

    return map;
  }

  public static void dump(Path filePath, Class... processorClasses) throws IOException {
    List<Map<String, Object>> lists = new ArrayList<>();
    for (Class processorClass : processorClasses) {
      lists.add(toMap(processorClass));
    }
    Yaml yaml = new Yaml();
    try (
        BufferedWriter writer = Files.newBufferedWriter(
            filePath,
            StandardOpenOption.TRUNCATE_EXISTING, StandardOpenOption.CREATE
        )
    ) {
      yaml.dump(lists, writer);
    }
  }

  public void dumpAll() throws ClassNotFoundException, IOException {
    Class[] classes = new Class[classNames.length];
    for (int i = 0; i < classNames.length; i++) {
      Class<?> aClass = Thread.currentThread().getContextClassLoader().loadClass(classNames[i]);
      classes[i] = aClass;
    }
    dump(outputPath, classes);
  }

  @NotNull
  static Map<String, Object> descToMap(LabelIndexDescription input) {
    Map<String, Object> map = new HashMap<>();
    map.put("name", input.name());
    map.put("name_from_parameter", input.nameFromParameter());
    map.put("description", input.description());
    List<Map<String, Object>> properties = new ArrayList<>();
    for (PropertyDescription property : input.properties()) {
      Map<String, Object> propertyMap = new HashMap<>();
      propertyMap.put("name", property.name());
      propertyMap.put("description", property.description());
      propertyMap.put("data_type", property.dataType());
      propertyMap.put("nullable", property.nullable());
      properties.add(propertyMap);
    }
    map.put("properties", properties);
    return map;
  }

  public static void main(String[] args) {
    PrintProcessorMetadata print = new PrintProcessorMetadata();
    CmdLineParser parser = new CmdLineParser(print);
    try {
      parser.parseArgument(args);
      print.dumpAll();
    } catch (CmdLineException e) {
      String canonicalName = PrintProcessorMetadata.class.getCanonicalName();
      System.err.println("java " + canonicalName + " [options...]");
      parser.printUsage(System.err);
      System.err.println("Example: " + canonicalName + parser.printExample(ALL));
    } catch (IOException | ClassNotFoundException e) {
      e.printStackTrace();
    }
  }
}

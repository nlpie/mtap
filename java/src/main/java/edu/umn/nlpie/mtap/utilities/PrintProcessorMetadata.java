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

import edu.umn.nlpie.mtap.processing.*;
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
import java.util.*;

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

  public static void dump(Path filePath, Class<?>... processorClasses) throws IOException {
    List<Map<String, Object>> lists = new ArrayList<>();
    for (Class<?> processorClass : processorClasses) {
      lists.add(ProcessorBase.metadataMap(processorClass));
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
    Class<?>[] classes = new Class[classNames.length];
    for (int i = 0; i < classNames.length; i++) {
      Class<?> aClass = Thread.currentThread().getContextClassLoader().loadClass(classNames[i]);
      classes[i] = aClass;
    }
    dump(outputPath, classes);
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

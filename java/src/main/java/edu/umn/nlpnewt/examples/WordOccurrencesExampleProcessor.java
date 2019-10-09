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

package edu.umn.nlpnewt.examples;

import edu.umn.nlpnewt.common.JsonObject;
import edu.umn.nlpnewt.common.JsonObjectBuilder;
import edu.umn.nlpnewt.common.Server;
import edu.umn.nlpnewt.model.Document;
import edu.umn.nlpnewt.model.GenericLabel;
import edu.umn.nlpnewt.model.Labeler;
import edu.umn.nlpnewt.processing.*;
import org.jetbrains.annotations.NotNull;
import org.kohsuke.args4j.CmdLineException;
import org.kohsuke.args4j.CmdLineParser;
import org.kohsuke.args4j.Option;

import java.io.IOException;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * An example document processor.
 */
@Processor(
    value = "nlpnewt-example-processor-java",
    description = "Labels occurrences of a word.",
    parameters = {
        @ParameterDescription(
            name = "do_work",
            description = "Whether the processor should do anything.",
            dataType = "bool",
            required = true
        ),
        @ParameterDescription(
            name = "output_index",
            description = "The output index name.",
            dataType = "str"
        )
    },
    outputs = {
        @LabelIndexDescription(
            name = "nlpnewt.examples.word_occurrences",
            nameFromParameter = "output_index",
            description = "Occurrences of the specified word."
        )
    }
)
public class WordOccurrencesExampleProcessor extends DocumentProcessor {

  private final Pattern pattern = Pattern.compile("\\w+");

  private final String word;

  public WordOccurrencesExampleProcessor(String word) {
    this.word = word;
  }

  public static void main(String[] args) {
    Options options = new Options();
    CmdLineParser parser = new CmdLineParser(options);
    try {
      parser.parseArgument(args);
      WordOccurrencesExampleProcessor processor = new WordOccurrencesExampleProcessor(options.word);
      Server server = ProcessorServerBuilder.forProcessor(processor, options).build();
      server.start();
      server.blockUntilShutdown();
    } catch (IOException e) {
      System.err.println("Failed to start server: " + e.getMessage());
    } catch (InterruptedException e) {
      System.err.println("Server interrupted.");
    } catch (CmdLineException e) {
      ProcessorServerOptions.printHelp(parser, WordOccurrencesExampleProcessor.class, e, null);
    }
  }

  @Override
  protected void process(@NotNull Document document,
                         @NotNull JsonObject params,
                         @NotNull JsonObjectBuilder result) {
    // Example of using process level parameters to do conditional processing
    Boolean doWork = params.getBooleanValue("do_work");
    if (doWork == null || !doWork) {
      return;
    }

    String indexName = params.getStringValue("output_index");
    if (indexName == null) {
      indexName = "nlpnewt.examples.word_occurrences";
    }

    // Example of using a timer to do timing of operations
    Stopwatch stopwatch = startedStopwatch("fetch_time");
    String text = document.getText();
    stopwatch.stop();

    // Using a labeler to add labels to the document.
    try (Labeler<GenericLabel> labeler = document.getLabeler(indexName, true)) {
      Matcher matcher = pattern.matcher(text);
      while (matcher.find()) {
        if (word.equals(matcher.group().toLowerCase())) {
          labeler.add(GenericLabel.withSpan(matcher.start(), matcher.end()));
        }
      }
    }

    // Example of returning process level results.
    result.setProperty("answer", 42);
  }

  public static class Options extends ProcessorServerOptions {
    @Option(name = "--word",
        aliases = {
            "--word"
        },
        metaVar = "WORD",
        usage = "The word to label occurrences.")
    String word = "the";
  }
}

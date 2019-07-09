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

import static org.kohsuke.args4j.OptionHandlerFilter.ALL;

/**
 * An example document processor.
 */
@Processor("nlpnewt-example-processor-java")
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
      // if there's a problem in the command line,
      // you'll get this exception. this will report
      // an error message.
      System.err.println(e.getMessage());
      System.err.println("java edu.umn.nlpnewt.examples.WordOccurrencesExampleProcessor [options...]");
      // print the list of available options
      parser.printUsage(System.err);
      System.err.println();

      // print option sample. This is useful some time
      System.err.println("  Example: java edu.umn.nlpnewt.examples.WordOccurrencesExampleProcessor " + parser.printExample(ALL));
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

    // Example of using a timer to do timing of operations
    Timer timer = getContext().startTimer("fetch_time");
    String text = document.getText();
    timer.stop();

    // Using a labeler to add labels to the document.
    try (Labeler<GenericLabel> thesLabeler = document.getLabeler("nlpnewt.examples.thes", true)) {
      Matcher matcher = pattern.matcher(text);
      while (matcher.find()) {
        if (word.equals(matcher.group().toLowerCase())) {
          thesLabeler.add(GenericLabel.newBuilder(matcher.start(), matcher.end()).build());
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
    public String word = "the";
  }
}

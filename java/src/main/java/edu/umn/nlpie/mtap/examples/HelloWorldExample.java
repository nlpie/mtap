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

package edu.umn.nlpie.mtap.examples;

import edu.umn.nlpie.mtap.common.JsonObject;
import edu.umn.nlpie.mtap.common.JsonObjectBuilder;
import edu.umn.nlpie.mtap.common.Server;
import edu.umn.nlpie.mtap.model.Document;
import edu.umn.nlpie.mtap.model.GenericLabel;
import edu.umn.nlpie.mtap.model.Labeler;
import edu.umn.nlpie.mtap.processing.DocumentProcessor;
import edu.umn.nlpie.mtap.processing.Processor;
import edu.umn.nlpie.mtap.processing.ProcessorServer;
import org.kohsuke.args4j.CmdLineException;
import org.kohsuke.args4j.CmdLineParser;

import java.io.IOException;

@Processor("hello")
public class HelloWorldExample extends DocumentProcessor {
  @Override
  protected void process(Document document, JsonObject params, JsonObjectBuilder result) {
    try (Labeler<GenericLabel> labeler = document.getLabeler("hello")) {
      String text = document.getText();
      labeler.add(
          GenericLabel.withSpan(0, text.length()).setProperty("response", "Hello " + text + "!")
      );
    }
  }

  public static void main(String[] args) {
    ProcessorServer.Builder options = new ProcessorServer.Builder();
    CmdLineParser parser = new CmdLineParser(options);
    try {
      parser.parseArgument(args);
      Server server = options.build(new HelloWorldExample());
      server.start();
      server.blockUntilShutdown();
    } catch (IOException e) {
      System.err.println("Failed to start server: " + e.getMessage());
    } catch (InterruptedException e) {
      System.err.println("Server interrupted.");
    } catch (CmdLineException e) {
      ProcessorServer.Builder.printHelp(parser, HelloWorldExample.class, e, null);
    }
  }
}

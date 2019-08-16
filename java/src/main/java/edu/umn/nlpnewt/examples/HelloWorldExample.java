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

package edu.umn.nlpnewt.examples;

import edu.umn.nlpnewt.Newt;
import edu.umn.nlpnewt.common.JsonObject;
import edu.umn.nlpnewt.common.JsonObjectBuilder;
import edu.umn.nlpnewt.common.Server;
import edu.umn.nlpnewt.model.Document;
import edu.umn.nlpnewt.model.GenericLabel;
import edu.umn.nlpnewt.model.Labeler;
import edu.umn.nlpnewt.processing.DocumentProcessor;
import edu.umn.nlpnewt.processing.Processor;
import edu.umn.nlpnewt.processing.ProcessorServerBuilder;
import edu.umn.nlpnewt.processing.ProcessorServerOptions;
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
          GenericLabel.newBuilder(0, text.length())
              .setProperty("response", "Hello" + text + "!")
              .build()
      );
    }
  }

  public static void main(String[] args) {
    ProcessorServerOptions options = new ProcessorServerOptions();
    CmdLineParser parser = new CmdLineParser(options);
    try {
      parser.parseArgument(args);
      Server server = ProcessorServerBuilder.forProcessor(new HelloWorldExample(), options).build();
      server.start();
      server.blockUntilShutdown();
    } catch (IOException e) {
      System.err.println("Failed to start server: " + e.getMessage());
    } catch (InterruptedException e) {
      System.err.println("Server interrupted.");
    } catch (CmdLineException e) {
      ProcessorServerOptions.printHelp(parser, HelloWorldExample.class, e, null);
    }
  }
}

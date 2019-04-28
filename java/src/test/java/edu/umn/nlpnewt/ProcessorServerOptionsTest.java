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
import org.junit.jupiter.api.Test;
import org.kohsuke.args4j.CmdLineException;
import org.kohsuke.args4j.CmdLineParser;

import static org.junit.jupiter.api.Assertions.*;

class ProcessorServerOptionsTest {

  @Processor("test-processor")
  public static class TestProcessor extends AbstractDocumentProcessor {

    @Override
    protected void process(@NotNull Document document, @NotNull JsonObject params, JsonObject.@NotNull Builder result) {

    }
  }

  @Test
  void noProcessorClassThrows() {
    assertThrows(CmdLineException.class, () -> {
      ProcessorServerOptions options = new ProcessorServerOptions();
      CmdLineParser parser = new CmdLineParser(options);
      parser.parseArgument();
    });
  }

  @Test
  void shouldHandleProcessorClass() throws CmdLineException {
    String[] args = new String[] {"edu.umn.nlpnewt.ProcessorServerOptionsTest$TestProcessor"};
    ProcessorServerOptions options = new ProcessorServerOptions();
    CmdLineParser parser = new CmdLineParser(options);
    parser.parseArgument(args);
    assertEquals(TestProcessor.class, options.getProcessorClass());
  }

  @Test
  void hasDefaultPort0() throws CmdLineException {
    String[] args = new String[] {"edu.umn.nlpnewt.ProcessorServerOptionsTest$TestProcessor"};
    ProcessorServerOptions options = new ProcessorServerOptions();
    CmdLineParser parser = new CmdLineParser(options);
    parser.parseArgument(args);
    assertEquals(0, options.getPort());
  }

  @Test
  void hasDefaultAddress() throws CmdLineException {
    String[] args = new String[] {"edu.umn.nlpnewt.ProcessorServerOptionsTest$TestProcessor"};
    ProcessorServerOptions options = new ProcessorServerOptions();
    CmdLineParser parser = new CmdLineParser(options);
    parser.parseArgument(args);
    assertEquals("127.0.0.1", options.getAddress());
  }
}

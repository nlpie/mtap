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

import java.nio.file.Paths;

import static org.junit.jupiter.api.Assertions.*;

class ProcessorServerOptionsTest {

  @Processor("test-processor")
  public static class TestProcessorBase extends DocumentProcessorBase {

    @Override
    protected void process(@NotNull Document document, @NotNull JsonObject params, @NotNull JsonObjectBuilder result) {

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
    String[] args = new String[] {"edu.umn.nlpnewt.ProcessorServerOptionsTest$TestProcessorBase"};
    ProcessorServerOptions options = new ProcessorServerOptions();
    CmdLineParser parser = new CmdLineParser(options);
    parser.parseArgument(args);
    assertEquals(TestProcessorBase.class, options.getProcessorClass());
  }

  @Test
  void badProcessorClassName() {
    String[] args = new String[] {"foo"};
    ProcessorServerOptions options = new ProcessorServerOptions();
    CmdLineParser parser = new CmdLineParser(options);
    assertThrows(CmdLineException.class, () -> parser.parseArgument(args));
  }

  @Test
  void hasDefaultPort0() throws CmdLineException {
    String[] args = new String[] {"edu.umn.nlpnewt.ProcessorServerOptionsTest$TestProcessorBase"};
    ProcessorServerOptions options = new ProcessorServerOptions();
    CmdLineParser parser = new CmdLineParser(options);
    parser.parseArgument(args);
    assertEquals(0, options.getPort());
  }

  @Test
  void hasDefaultAddress() throws CmdLineException {
    String[] args = new String[] {"edu.umn.nlpnewt.ProcessorServerOptionsTest$TestProcessorBase"};
    ProcessorServerOptions options = new ProcessorServerOptions();
    CmdLineParser parser = new CmdLineParser(options);
    parser.parseArgument(args);
    assertEquals("127.0.0.1", options.getAddress());
  }

  @Test
  void setProcessorClass() {
    ProcessorServerOptions options = ProcessorServerOptions.emptyOptions();
    options.setProcessorClass(TestProcessorBase.class);
    assertEquals(TestProcessorBase.class, options.getProcessorClass());
  }

  @Test
  void withProcessorClass() {
    ProcessorServerOptions options = ProcessorServerOptions.emptyOptions()
        .withProcessorClass(TestProcessorBase.class);
    assertEquals(TestProcessorBase.class, options.getProcessorClass());
  }

  @Test
  void withProcessorThenProcessorClass() {
    TestProcessorBase processor = new TestProcessorBase();
    ProcessorServerOptions options = ProcessorServerOptions.emptyOptions().withProcessor(processor);
    assertThrows(IllegalStateException.class,
        () -> options.withProcessorClass(TestProcessorBase.class));
  }

  @Test
  void setProcessor() {
    TestProcessorBase processor = new TestProcessorBase();
    ProcessorServerOptions options = ProcessorServerOptions.emptyOptions();
    options.setProcessor(processor);
    assertEquals(processor, options.getProcessor());
  }

  @Test
  void withProcessor() {
    TestProcessorBase processor = new TestProcessorBase();
    ProcessorServerOptions options = ProcessorServerOptions.emptyOptions()
        .withProcessor(processor);
    assertEquals(processor, options.getProcessor());
  }

  @Test
  void withProcessorClassThenProcessor() {
    ProcessorServerOptions options = ProcessorServerOptions.emptyOptions()
        .withProcessorClass(TestProcessorBase.class);
    TestProcessorBase processor = new TestProcessorBase();
    assertThrows(IllegalStateException.class,
        () -> options.withProcessor(processor));
  }

  @Test
  void setAddress() {
    ProcessorServerOptions options = ProcessorServerOptions.emptyOptions();
    options.setAddress("localhost");
    assertEquals("localhost", options.getAddress());
  }

  @Test
  void withAddress() {
    ProcessorServerOptions options = ProcessorServerOptions.emptyOptions();
    options.withAddress("localhost");
    assertEquals("localhost", options.getAddress());
  }

  @Test
  void setPort() {
    ProcessorServerOptions options = ProcessorServerOptions.emptyOptions();
    options.setPort(50555);
    assertEquals(50555, options.getPort());
  }

  @Test
  void withPort() {
    ProcessorServerOptions options = ProcessorServerOptions.emptyOptions().withPort(50555);
    assertEquals(50555, options.getPort());
  }

  @Test
  void defaultRegisterFalse() {
    ProcessorServerOptions options = ProcessorServerOptions.emptyOptions();
    assertFalse(options.getRegister());
  }

  @Test
  void setRegister() {
    ProcessorServerOptions options = ProcessorServerOptions.emptyOptions();
    options.setRegister(true);
    assertTrue(options.getRegister());
  }

  @Test
  void register() {
    ProcessorServerOptions options = ProcessorServerOptions.emptyOptions()
        .register();
    assertTrue(options.getRegister());
  }

  @Test
  void setEventsTarget() {
    ProcessorServerOptions options = ProcessorServerOptions.emptyOptions();
    options.setEventsTarget("localhost:9090");
    assertEquals("localhost:9090", options.getEventsTarget());
  }

  @Test
  void withEventsTarget() {
    ProcessorServerOptions options = ProcessorServerOptions.emptyOptions()
        .withEventsTarget("localhost:9090");
    assertEquals("localhost:9090", options.getEventsTarget());
  }

  @Test
  void setConfigFile() {
    ProcessorServerOptions options = ProcessorServerOptions.emptyOptions();
    options.setConfigFile(Paths.get("blub"));
    assertEquals(Paths.get("blub"), options.getConfigFile());
  }

  @Test
  void withConfigFile() {
    ProcessorServerOptions options = ProcessorServerOptions.emptyOptions()
        .withConfigFile(Paths.get("blub"));
    assertEquals(Paths.get("blub"), options.getConfigFile());
  }

  @Test
  void setIdentifier() {
    ProcessorServerOptions options = ProcessorServerOptions.emptyOptions();
    options.setIdentifier("foo");
    assertEquals("foo", options.getIdentifier());
  }

  @Test
  void withIdentifier() {
    ProcessorServerOptions options = ProcessorServerOptions.emptyOptions()
        .withIdentifier("foo");
    assertEquals("foo", options.getIdentifier());
  }
}


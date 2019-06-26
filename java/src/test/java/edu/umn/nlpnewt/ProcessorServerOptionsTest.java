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
  public static class TestProcessor extends DocumentProcessor {

    @Override
    protected void process(@NotNull Document document, @NotNull JsonObject params, @NotNull JsonObjectBuilder result) {

    }
  }

  @Test
  void hasDefaultPort0() throws CmdLineException {
    String[] args = new String[] {};
    ProcessorServerOptions options = new ProcessorServerOptions(new TestProcessor());
    CmdLineParser parser = new CmdLineParser(options);
    parser.parseArgument(args);
    assertEquals(0, options.getPort());
  }

  @Test
  void hasDefaultAddress() throws CmdLineException {
    String[] args = new String[] {};
    ProcessorServerOptions options = new ProcessorServerOptions(new TestProcessor());
    CmdLineParser parser = new CmdLineParser(options);
    parser.parseArgument(args);
    assertEquals("127.0.0.1", options.getAddress());
  }

  @Test
  void setAddress() {
    ProcessorServerOptions options = new ProcessorServerOptions(new TestProcessor());
    options.setAddress("localhost");
    assertEquals("localhost", options.getAddress());
  }

  @Test
  void withAddress() {
    ProcessorServerOptions options = new ProcessorServerOptions(new TestProcessor());
    options.withAddress("localhost");
    assertEquals("localhost", options.getAddress());
  }

  @Test
  void setPort() {
    ProcessorServerOptions options = new ProcessorServerOptions(new TestProcessor());
    options.setPort(50555);
    assertEquals(50555, options.getPort());
  }

  @Test
  void withPort() {
    ProcessorServerOptions options = new ProcessorServerOptions(new TestProcessor()).withPort(50555);
    assertEquals(50555, options.getPort());
  }

  @Test
  void defaultRegisterFalse() {
    ProcessorServerOptions options = new ProcessorServerOptions(new TestProcessor());
    assertFalse(options.getRegister());
  }

  @Test
  void setRegister() {
    ProcessorServerOptions options = new ProcessorServerOptions(new TestProcessor());
    options.setRegister(true);
    assertTrue(options.getRegister());
  }

  @Test
  void register() {
    ProcessorServerOptions options = new ProcessorServerOptions(new TestProcessor()).register();
    assertTrue(options.getRegister());
  }

  @Test
  void setEventsTarget() {
    ProcessorServerOptions options = new ProcessorServerOptions(new TestProcessor());
    options.setEventsTarget("localhost:9090");
    assertEquals("localhost:9090", options.getEventsTarget());
  }

  @Test
  void withEventsTarget() {
    ProcessorServerOptions options = new ProcessorServerOptions(new TestProcessor())
        .withEventsTarget("localhost:9090");
    assertEquals("localhost:9090", options.getEventsTarget());
  }

  @Test
  void setConfigFile() {
    ProcessorServerOptions options = new ProcessorServerOptions(new TestProcessor());
    options.setConfigFile(Paths.get("blub"));
    assertEquals(Paths.get("blub"), options.getConfigFile());
  }

  @Test
  void withConfigFile() {
    ProcessorServerOptions options = new ProcessorServerOptions(new TestProcessor())
        .withConfigFile(Paths.get("blub"));
    assertEquals(Paths.get("blub"), options.getConfigFile());
  }

  @Test
  void setIdentifier() {
    ProcessorServerOptions options = new ProcessorServerOptions(new TestProcessor());
    options.setIdentifier("foo");
    assertEquals("foo", options.getIdentifier());
  }

  @Test
  void withIdentifier() {
    ProcessorServerOptions options = new ProcessorServerOptions(new TestProcessor())
        .withIdentifier("foo");
    assertEquals("foo", options.getIdentifier());
  }
}


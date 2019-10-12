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

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.kohsuke.args4j.CmdLineException;
import org.kohsuke.args4j.CmdLineParser;
import org.kohsuke.args4j.Option;

import java.nio.file.Paths;

import static org.junit.jupiter.api.Assertions.*;

class ProcessorServerOptionsTest {
  private ProcessorServerOptions options;

  @BeforeEach
  void setUp() {
    options = ProcessorServerOptions.defaultOptions();
  }

  @Test
  void parseArgs() throws CmdLineException {
    CmdLineParser cmdLineParser = new CmdLineParser(options);
    cmdLineParser.parseArgument(
        "--events",
        "localhost:8080",
        "--register",
        "--port",
        "10",
        "--identifier",
        "blah",
        "--config",
        "/etc/config",
        "--unique-service-id",
        "2");
    assertEquals("localhost:8080", options.getEventsTarget());
    assertTrue(options.getRegister());
    assertEquals(10, options.getPort());
    assertEquals("blah", options.getIdentifier());
    assertEquals(Paths.get("/etc/config"), options.getConfigFile());
    assertEquals("2", options.getUniqueServiceId());
  }

  @Test
  void hasDefaultPort0() throws CmdLineException {
    String[] args = new String[]{};
    CmdLineParser parser = new CmdLineParser(options);
    parser.parseArgument(args);
    assertEquals(0, options.getPort());
  }

  @Test
  void setPort() {
    options.setPort(50555);
    assertEquals(50555, options.getPort());
  }

  @Test
  void defaultRegisterFalse() {
    assertFalse(options.getRegister());
  }

  @Test
  void setRegister() {
    options.setRegister(true);
    assertTrue(options.getRegister());
  }

  @Test
  void setEventsTarget() {
    options.setEventsTarget("localhost:9090");
    assertEquals("localhost:9090", options.getEventsTarget());
  }

  @Test
  void setConfigFile() {
    options.setConfigFile(Paths.get("blub"));
    assertEquals(Paths.get("blub"), options.getConfigFile());
  }

  @Test
  void setIdentifier() {
    options.setIdentifier("foo");
    assertEquals("foo", options.getIdentifier());
  }

  @Test
  void subclassing() throws CmdLineException {
    Subclass options = new Subclass();
    CmdLineParser parser = new CmdLineParser(options);
    parser.parseArgument(
        "--events",
        "localhost:8080",
        "--register",
        "--port",
        "10",
        "--identifier",
        "blah",
        "--config",
        "/etc/config",
        "--unique-service-id",
        "2",
        "--extra",
        "foo");
    assertEquals("localhost:8080", options.getEventsTarget());
    assertTrue(options.getRegister());
    assertEquals(10, options.getPort());
    assertEquals("blah", options.getIdentifier());
    assertEquals(Paths.get("/etc/config"), options.getConfigFile());
    assertEquals("2", options.getUniqueServiceId());
    assertEquals("foo", options.extra);
  }

  public static class Subclass extends ProcessorServerOptions {
    @Option(
        name = "--extra",
        required = true
    )
    private String extra;

  }
}


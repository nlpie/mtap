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

package edu.umn.nlpnewt.internal.processing;

import edu.umn.nlpnewt.Config;
import edu.umn.nlpnewt.EventProcessor;
import edu.umn.nlpnewt.ProcessorServerOptions;
import io.grpc.inprocess.InProcessServerBuilder;
import io.grpc.netty.NettyServerBuilder;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.yaml.snakeyaml.Yaml;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class NewtInternalProcessingTest {

  private Config config;
  private EventProcessor processor;

  @BeforeEach
  void setUp() {
    config = mock(Config.class);
    processor = mock(EventProcessor.class);
  }

  @Test
  void loadsConfigFile() throws IOException {
    Path path = Files.createTempFile(null, null);
    Map<String, Object> configMap = new HashMap<>();
    configMap.put("additionalParameter", 3);
    try (BufferedWriter writer = Files.newBufferedWriter(path)) {
      Yaml yaml = new Yaml();
      yaml.dump(configMap, writer);
    }

    ProcessorServerOptions options = ProcessorServerOptions.emptyOptions()
        .withProcessor(processor)
        .withConfigFile(path);

    NewtInternalProcessing processing = new NewtInternalProcessing(config, options);
    Config config = processing.getConfig();
    assertEquals(3, (int) config.getIntegerValue("additionalParameter"));

  }

  @Test
  void copyConstructor() throws IOException {
    ProcessorServerOptions options = ProcessorServerOptions.emptyOptions()
        .withProcessor(processor)
        .withIdentifier("foo")
        .withEventsTarget("bar");
    NewtInternalProcessing newtInternalProcessing = new NewtInternalProcessing(config, options);
    assertEquals("foo", newtInternalProcessing.getIdentifier());
    assertEquals("bar", newtInternalProcessing.getEventsTarget());
  }

  @Test
  void testDefaultServerBuilder() throws IOException {
    NewtInternalProcessing newtInternalProcessing = new NewtInternalProcessing(config);
    assertTrue(newtInternalProcessing.getServerBuilder() instanceof NettyServerBuilder);
  }

  @Test
  void testProvidedServerBuilder() throws IOException {
    String name = InProcessServerBuilder.generateName();
    InProcessServerBuilder builder = InProcessServerBuilder.forName(name);

    NewtInternalProcessing newtInternalProcessing = new NewtInternalProcessing(config);
    newtInternalProcessing.setServerBuilder(builder);
    assertTrue(newtInternalProcessing.getServerBuilder() instanceof InProcessServerBuilder);
  }

  @Test
  void testDefaultRegistrationAndHealthManagerFactory() {

  }

  @Test
  void testDefaultRegistrationAndHealthManager() throws IOException {
    NewtInternalProcessing newtInternalProcessing = new NewtInternalProcessing(config);
  }
}

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

import edu.umn.nlpie.mtap.examples.WordOccurrencesExampleProcessor;
import edu.umn.nlpie.mtap.processing.ProcessorBase;
import org.junit.jupiter.api.Test;
import org.yaml.snakeyaml.Yaml;

import java.io.IOException;
import java.io.InputStream;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

class PrintProcessorMetadataTest {
  @SuppressWarnings("rawtypes")
  @Test
  void toMap() throws IOException {
    try (InputStream is = Thread.currentThread().getContextClassLoader().getResourceAsStream("edu/umn/nlpie/mtap/ExampleMeta.yaml")) {
      Yaml yaml = new Yaml();
      List o = yaml.load(is);
      Map<String, Object> actual = ProcessorBase.metadataMap(WordOccurrencesExampleProcessor.class);
      assertEquals(o.get(0), actual);
    }
  }
}

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

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

class ConfigTest {
  Config config;

  @BeforeEach
  void setUp() {
    config = Config.emptyConfig();
  }

  @Test
  void getStringValueNull() {
    config.set("test", null);
    assertNull(config.getStringValue("test"));
  }

  @Test
  void getStringValue() {
    config.set("test", "foo");
    assertEquals("foo", config.getStringValue("test"));
  }

  @Test
  void getStringValueCastException() {
    config.set("test", 1);
    assertThrows(ClassCastException.class, () -> config.getStringValue("test"));
  }

  @Test
  void getIntegerValueNull() {
    config.set("test", null);
    assertNull(config.getIntegerValue("test"));
  }

  @Test
  void getIntegerValue() {
    config.set("test", 1);
    assertEquals(Integer.valueOf(1), config.getIntegerValue("test"));
  }

  @Test
  void getIntegerValueCastException() {
    config.set("test", "test");
    assertThrows(ClassCastException.class, () -> config.getIntegerValue("test"));
  }

  @Test
  void getDoubleValueNull() {
    config.set("test", null);
    assertNull(config.getDoubleValue("test"));
  }

  @Test
  void getDoubleValue() {
    config.set("test", 1.0);
    assertEquals(Double.valueOf(1.0), config.getDoubleValue("test"));
  }

  @Test
  void getDoubleValueClassCastException() {
    config.set("test", 1);
    assertThrows(ClassCastException.class, () -> config.getDoubleValue("test"));
  }

  @Test
  void getBooleanValueNull() {
    config.set("test", null);
    assertNull(config.getBooleanValue("test"));
  }

  @Test
  void getBooleanValue() {
    config.set("test", false);
    assertFalse(config.getBooleanValue("test"));
  }

  @Test
  void getBooleanValueCastException() {
    config.set("test", 1);
    assertThrows(ClassCastException.class, () -> config.getBooleanValue("test"));
  }

  @Test
  void update() {
    config.set("blah", 1);
    Map<String, Object> updateMap = new HashMap<>();
    updateMap.put("blah", 2);
    updateMap.put("foo", "bar");
    config.update(updateMap);
    assertEquals(Integer.valueOf(2), config.getIntegerValue("blah"));
    assertEquals("bar", config.getStringValue("foo"));
  }
}

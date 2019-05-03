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

package edu.umn.nlpnewt;

import com.google.protobuf.ListValue;
import com.google.protobuf.NullValue;
import com.google.protobuf.Struct;
import com.google.protobuf.Value;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import org.junit.jupiter.api.Test;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

class JsonObjectImplTest {
  @Test
  void stringValue() {
    JsonObjectImpl.Builder builder = JsonObjectImpl.newBuilder().setProperty("foo", "bar");
    assertEquals("bar", builder.getStringValue("foo"));
    JsonObjectImpl jsonObject = builder.build();
    assertEquals("bar", jsonObject.getStringValue("foo"));
  }

  @Test
  void doubleValue() {
    JsonObjectImpl.Builder builder = JsonObjectImpl.newBuilder().setProperty("foo", 1.0d);
    assertEquals(1.0d, builder.getNumberValue("foo").doubleValue());
    JsonObjectImpl jsonObject = builder.build();
    assertEquals(1.0d, jsonObject.getNumberValue("foo").doubleValue());
  }

  @Test
  void nullValue() {
    JsonObjectImpl.Builder builder = JsonObjectImpl.newBuilder().setProperty("foo", null);
    assertNull(builder.get("foo"));
    assertNull(builder.getNumberValue("foo"));
    assertNull(builder.getStringValue("foo"));
    assertNull(builder.getBooleanValue("foo"));
    assertNull(builder.getJsonObjectValue("foo"));
    assertNull(builder.getListValue("foo"));
    JsonObjectImpl jsonObject = builder.build();
    assertNull(jsonObject.get("foo"));
    assertNull(jsonObject.getNumberValue("foo"));
    assertNull(jsonObject.getStringValue("foo"));
    assertNull(jsonObject.getBooleanValue("foo"));
    assertNull(jsonObject.getJsonObjectValue("foo"));
    assertNull(jsonObject.getListValue("foo"));
  }

  @Test
  void mapValue() {
    HashMap<Object, Object> map = new HashMap<>();
    map.put("a", 1);
    map.put("b", 2);
    JsonObjectImpl.Builder builder = JsonObjectImpl.newBuilder().setProperty("foo", map);
    JsonObject m1 = builder.getJsonObjectValue("foo");
    assertEquals(2, m1.size());
    assertEquals(1, m1.getNumberValue("a").intValue());
    assertEquals(2, m1.getNumberValue("b").intValue());
    JsonObjectImpl jsonObject = builder.build();
    JsonObject m2 = jsonObject.getJsonObjectValue("foo");
    assertEquals(2, m2.size());
    assertEquals(1, m2.getNumberValue("a").intValue());
    assertEquals(2, m2.getNumberValue("b").intValue());
  }

  @Test
  void mapValueNonStringIndex() {
    HashMap<Object, Object> map = new HashMap<>();
    map.put("a", 1);
    map.put(2, 2);
    assertThrows(IllegalArgumentException.class,
        () -> JsonObjectImpl.newBuilder().setProperty("foo", map));
  }

  @Test
  void mapReferenceLoop() {
    HashMap<Object, Object> map = new HashMap<>();
    map.put("a", 1);
    map.put("b", map);
    assertThrows(IllegalArgumentException.class,
        () -> JsonObjectImpl.newBuilder().setProperty("foo", map));
  }

  @Test
  void jsonObjectValue() {
    JsonObjectImpl o1 = JsonObjectImpl.newBuilder().setProperty("a", 1).setProperty("b", 2).build();
    JsonObjectImpl.Builder builder = JsonObjectImpl.newBuilder().setProperty("foo", o1);
    assertEquals(o1, builder.getJsonObjectValue("foo"));
    JsonObjectImpl jsonObject = builder.build();
    assertEquals(o1, jsonObject.getJsonObjectValue("foo"));
  }

  @Test
  void jsonObjectReferenceLoop() {
    JsonObjectImpl.Builder builder = JsonObjectImpl.newBuilder();
    assertThrows(IllegalArgumentException.class, () ->
        builder.setProperty("blub", builder));
  }

  @Test
  void listValue() {
    JsonObjectImpl.Builder builder = JsonObjectImpl.newBuilder()
        .setProperty("foo", Arrays.asList(0, 1, 2, 3));
    assertEquals(Arrays.asList(0.0, 1.0, 2.0, 3.0), builder.getListValue("foo"));
    JsonObjectImpl jsonObject = builder.build();
    assertEquals(Arrays.asList(0.0, 1.0, 2.0, 3.0), jsonObject.getListValue("foo"));
  }

  @Test
  void listReferenceLoop() {
    List<Object> strings = new ArrayList<>(Arrays.asList("a", "b", "c", "d"));
    strings.add(strings);
    assertThrows(IllegalArgumentException.class,
        () -> JsonObjectImpl.newBuilder().setProperty("foo", strings));
  }

  @Test
  void longValue() {
    JsonObjectImpl.Builder builder = JsonObjectImpl.newBuilder().setProperty("foo", 1L);
    assertEquals(1L, builder.getNumberValue("foo").longValue());
    JsonObjectImpl jsonObject = builder.build();
    assertEquals(1L, jsonObject.getNumberValue("foo").longValue());
  }

  @Test
  void integerValue() {
    JsonObjectImpl.Builder builder = JsonObjectImpl.newBuilder().setProperty("foo", 1);
    assertEquals(1, builder.getNumberValue("foo").intValue());
    JsonObjectImpl jsonObject = builder.build();
    assertEquals(1, jsonObject.getNumberValue("foo").intValue());
  }

  @Test
  void shortValue() {
    JsonObjectImpl.Builder builder = JsonObjectImpl.newBuilder().setProperty("foo", (short) 1);
    assertEquals((short) 1, builder.getNumberValue("foo").shortValue());
    JsonObjectImpl jsonObject = builder.build();
    assertEquals((short) 1, jsonObject.getNumberValue("foo").shortValue());
  }

  @Test
  void byteValue() {
    JsonObjectImpl.Builder builder = JsonObjectImpl.newBuilder().setProperty("foo", (byte) 1);
    assertEquals((byte) 1, builder.getNumberValue("foo").byteValue());
    JsonObjectImpl jsonObject = builder.build();
    assertEquals((byte) 1, jsonObject.getNumberValue("foo").byteValue());
  }

  @Test
  void floatValue() {
    JsonObjectImpl.Builder builder = JsonObjectImpl.newBuilder().setProperty("foo", 10.0f);
    assertEquals(10.0f, builder.getNumberValue("foo").floatValue());
    JsonObjectImpl jsonObject = builder.build();
    assertEquals(10.0f, jsonObject.getNumberValue("foo").floatValue());
  }

  @Test
  void charValue() {
    JsonObjectImpl.Builder builder = JsonObjectImpl.newBuilder().setProperty("foo", 'a');
    assertEquals('a', builder.getStringValue("foo").charAt(0));
    JsonObjectImpl jsonObject = builder.build();
    assertEquals('a', jsonObject.getStringValue("foo").charAt(0));
  }

  @Test
  void boolValue() {
    JsonObjectImpl.Builder builder = JsonObjectImpl.newBuilder().setProperty("foo", true);
    assertTrue(builder.getBooleanValue("foo"));
    JsonObjectImpl jsonObject = builder.build();
    assertTrue(jsonObject.getBooleanValue("foo"));
  }

  @Test
  void otherValue() {
    UUID uuid = UUID.randomUUID();
    assertThrows(IllegalArgumentException.class,
        () -> JsonObjectImpl.newBuilder().setProperty("foo", uuid));
  }

  @Test
  void stringValueToStruct() {
    JsonObjectImpl jsonObject = JsonObjectImpl.newBuilder().setProperty("foo", "bar").build();
    Struct.Builder builder = Struct.newBuilder();
    jsonObject.copyToStruct(builder);
    Struct struct = builder.build();
    assertEquals("bar", struct.getFieldsOrThrow("foo").getStringValue());
  }

  @Test
  void stringValueFromStruct() {
    Struct struct = Struct.newBuilder()
        .putFields("foo", Value.newBuilder().setStringValue("bar").build())
        .build();
    JsonObjectImpl.Builder builder = JsonObjectImpl.newBuilder();
    builder.copyStruct(struct);
    JsonObjectImpl jsonObject = builder.build();
    assertEquals("bar", jsonObject.getStringValue("foo"));
  }

  @Test
  void doubleValueToStruct() {
    JsonObjectImpl jsonObject = JsonObjectImpl.newBuilder().setProperty("foo", 20.0d).build();
    Struct.Builder builder = Struct.newBuilder();
    jsonObject.copyToStruct(builder);
    Struct struct = builder.build();
    assertEquals(20.0d, struct.getFieldsOrThrow("foo").getNumberValue());
  }

  @Test
  void doubleValueFromStruct() {
    Struct struct = Struct.newBuilder()
        .putFields("foo", Value.newBuilder().setNumberValue(10.0).build())
        .build();
    JsonObjectImpl.Builder builder = JsonObjectImpl.newBuilder();
    builder.copyStruct(struct);
    JsonObjectImpl jsonObject = builder.build();
    assertEquals(10.0, jsonObject.getNumberValue("foo").doubleValue());
  }

  @Test
  void nullValueToStruct() {
    JsonObjectImpl jsonObject = JsonObjectImpl.newBuilder().setProperty("foo", null).build();
    Struct.Builder builder = Struct.newBuilder();
    jsonObject.copyToStruct(builder);
    Struct struct = builder.build();
    assertEquals(NullValue.NULL_VALUE, struct.getFieldsOrThrow("foo").getNullValue());
  }

  @Test
  void nullValueFromStruct() {
    Struct struct = Struct.newBuilder()
        .putFields("foo", Value.newBuilder().setNullValue(NullValue.NULL_VALUE).build())
        .build();
    JsonObjectImpl.Builder builder = JsonObjectImpl.newBuilder();
    builder.copyStruct(struct);
    JsonObjectImpl jsonObject = builder.build();
    assertNull(jsonObject.get("foo"));
  }

  @Test
  void mapValueToStruct() {
    HashMap<Object, Object> map = new HashMap<>();
    map.put("a", 1);
    map.put("b", 2);
    JsonObjectImpl jsonObject = JsonObjectImpl.newBuilder().setProperty("foo", map).build();
    Struct.Builder builder = Struct.newBuilder();
    jsonObject.copyToStruct(builder);
    Struct struct = builder.build();
    assertEquals(1, (int) struct.getFieldsOrThrow("foo").getStructValue()
        .getFieldsOrThrow("a").getNumberValue());
    assertEquals(2, (int) struct.getFieldsOrThrow("foo").getStructValue()
        .getFieldsOrThrow("b").getNumberValue());
  }

  @Test
  void mapValueFromStruct() {
    Struct struct = Struct.newBuilder()
        .putFields("foo", Value.newBuilder()
            .setStructValue(
                Struct.newBuilder()
                    .putFields("bar", Value.newBuilder().setStringValue("baz").build())
            ).build())
        .build();
    JsonObjectImpl.Builder builder = JsonObjectImpl.newBuilder();
    builder.copyStruct(struct);
    JsonObjectImpl jsonObject = builder.build();
    assertEquals("baz", 
        jsonObject.getJsonObjectValue("foo").getStringValue("bar"));
  }

  @Test
  void jsonObjectValueToStruct() {
    JsonObjectImpl o1 = JsonObjectImpl.newBuilder().setProperty("a", 1).setProperty("b", 2).build();
    JsonObjectImpl jsonObject = JsonObjectImpl.newBuilder().setProperty("foo", o1).build();
    Struct.Builder builder = Struct.newBuilder();
    jsonObject.copyToStruct(builder);
    Struct struct = builder.build();
    assertEquals(1, (int) struct.getFieldsOrThrow("foo").getStructValue()
        .getFieldsOrThrow("a").getNumberValue());
    assertEquals(2, (int) struct.getFieldsOrThrow("foo").getStructValue()
        .getFieldsOrThrow("b").getNumberValue());
  }

  @Test
  void listValueToStruct() {
    JsonObjectImpl jsonObject = JsonObjectImpl.newBuilder().setProperty("foo", Arrays.asList(0, 1, 2, 3))
        .build();
    Struct.Builder builder = Struct.newBuilder();
    jsonObject.copyToStruct(builder);
    Struct struct = builder.build();
    Value value = struct.getFieldsOrThrow("foo");
    assertEquals(0.0, value.getListValue().getValues(0).getNumberValue());
    assertEquals(1.0, value.getListValue().getValues(1).getNumberValue());
    assertEquals(2.0, value.getListValue().getValues(2).getNumberValue());
    assertEquals(3.0, value.getListValue().getValues(3).getNumberValue());
  }

  @Test
  void listValueFromStruct() {
    Struct struct = Struct.newBuilder()
        .putFields("foo", Value.newBuilder()
            .setListValue(ListValue.newBuilder()
                .addValues(Value.newBuilder().setNumberValue(1).build())
                .addValues(Value.newBuilder().setNumberValue(2).build())
                .addValues(Value.newBuilder().setNumberValue(3).build())
                .addValues(Value.newBuilder().setNumberValue(4).build())
                .build())
            .build())
        .build();
    JsonObjectImpl.Builder builder = JsonObjectImpl.newBuilder();
    builder.copyStruct(struct);
    JsonObjectImpl jsonObject = builder.build();
    assertEquals(Arrays.asList(1.0, 2.0, 3.0, 4.0), jsonObject.getListValue("foo"));
  }

  @Test
  void longValueToStruct() {
    JsonObjectImpl jsonObject = JsonObjectImpl.newBuilder().setProperty("foo", 1L).build();
    Struct.Builder builder = Struct.newBuilder();
    jsonObject.copyToStruct(builder);
    Struct struct = builder.build();
    assertEquals(1L, struct.getFieldsOrThrow("foo").getNumberValue());
  }

  @Test
  void longValueFromStruct() {
    Struct struct = Struct.newBuilder()
        .putFields("foo", Value.newBuilder()
            .setNumberValue(1L)
            .build())
        .build();
    JsonObjectImpl.Builder builder = JsonObjectImpl.newBuilder();
    builder.copyStruct(struct);
    JsonObjectImpl jsonObject = builder.build();
    assertEquals(1L, jsonObject.getNumberValue("foo").longValue());
  }

  @Test
  void integerValueToStruct() {
    JsonObjectImpl jsonObject = JsonObjectImpl.newBuilder().setProperty("foo", 1).build();
    Struct.Builder builder = Struct.newBuilder();
    jsonObject.copyToStruct(builder);
    Struct struct = builder.build();
    assertEquals(1, struct.getFieldsOrThrow("foo").getNumberValue());
  }

  @Test
  void integerValueFromStruct() {
    Struct struct = Struct.newBuilder()
        .putFields("foo", Value.newBuilder()
            .setNumberValue(1)
            .build())
        .build();
    JsonObjectImpl.Builder builder = JsonObjectImpl.newBuilder();
    builder.copyStruct(struct);
    JsonObjectImpl jsonObject = builder.build();
    assertEquals(1, jsonObject.getNumberValue("foo").intValue());
  }

  @Test
  void shortValueToStruct() {
    JsonObjectImpl jsonObject = JsonObjectImpl.newBuilder().setProperty("foo", (short) 1).build();
    Struct.Builder builder = Struct.newBuilder();
    jsonObject.copyToStruct(builder);
    Struct struct = builder.build();
    assertEquals((short) 1, struct.getFieldsOrThrow("foo").getNumberValue());
  }

  @Test
  void shortValueFromStruct() {
    Struct struct = Struct.newBuilder()
        .putFields("foo", Value.newBuilder()
            .setNumberValue((short) 1)
            .build())
        .build();
    JsonObjectImpl.Builder builder = JsonObjectImpl.newBuilder();
    builder.copyStruct(struct);
    JsonObjectImpl jsonObject = builder.build();
    assertEquals((short) 1, jsonObject.getNumberValue("foo").shortValue());
  }

  @Test
  void byteValueToStruct() {
    JsonObjectImpl jsonObject = JsonObjectImpl.newBuilder().setProperty("foo", (byte) 1).build();
    Struct.Builder builder = Struct.newBuilder();
    jsonObject.copyToStruct(builder);
    Struct struct = builder.build();
    assertEquals((byte) 1, struct.getFieldsOrThrow("foo").getNumberValue());
  }

  @Test
  void byteValueFromStruct() {
    Struct struct = Struct.newBuilder()
        .putFields("foo", Value.newBuilder()
            .setNumberValue((byte) 1)
            .build())
        .build();
    JsonObjectImpl.Builder builder = JsonObjectImpl.newBuilder();
    builder.copyStruct(struct);
    JsonObjectImpl jsonObject = builder.build();
    assertEquals((byte) 1, jsonObject.getNumberValue("foo").byteValue());
  }

  @Test
  void charValueToStruct() {
    JsonObjectImpl jsonObject = JsonObjectImpl.newBuilder().setProperty("foo", 'c').build();
    Struct.Builder builder = Struct.newBuilder();
    jsonObject.copyToStruct(builder);
    Struct struct = builder.build();
    assertEquals("c", struct.getFieldsOrThrow("foo").getStringValue());
  }

  @Test
  void charValueFromStruct() {
    Struct struct = Struct.newBuilder()
        .putFields("foo", Value.newBuilder()
            .setStringValue("" + 'a')
            .build())
        .build();
    JsonObjectImpl.Builder builder = JsonObjectImpl.newBuilder();
    builder.copyStruct(struct);
    JsonObjectImpl jsonObject = builder.build();
    assertEquals('a', jsonObject.getStringValue("foo").charAt(0));
  }

  @Test
  void boolValueToStruct() {
    JsonObjectImpl jsonObject = JsonObjectImpl.newBuilder().setProperty("foo", true).build();
    Struct.Builder builder = Struct.newBuilder();
    jsonObject.copyToStruct(builder);
    Struct struct = builder.build();
    assertTrue(struct.getFieldsOrThrow("foo").getBoolValue());
  }

  @Test
  void boolValueFromStruct() {
    Struct struct = Struct.newBuilder()
        .putFields("foo", Value.newBuilder()
            .setBoolValue(true)
            .build())
        .build();
    JsonObjectImpl.Builder builder = JsonObjectImpl.newBuilder();
    builder.copyStruct(struct);
    JsonObjectImpl jsonObject = builder.build();
    assertTrue(jsonObject.getBooleanValue("foo"));
  }

  @Test
  void testContainsKey() {
    JsonObjectImpl jsonObject = JsonObjectImpl.newBuilder().setProperty("foo", "bar").build();
    assertTrue(jsonObject.containsKey("foo"));
    assertFalse(jsonObject.containsKey("baz"));
  }

  @Test
  void testBuilderContainsKey() {
    JsonObjectImpl.Builder builder = JsonObjectImpl.newBuilder().setProperty("foo", "bar");
    assertTrue(builder.containsKey("foo"));
    assertFalse(builder.containsKey("baz"));
  }

  @Test
  void builderSetProperties() {
    HashMap<String, Object> map = new HashMap<>();
    map.put("foo", "bar");
    map.put("baz", "bot");
    JsonObjectImpl build = JsonObjectImpl.newBuilder().setProperties(map).build();
    assertEquals("bar", build.get("foo"));
    assertEquals("bot", build.get("baz"));
  }

  @Test
  void copyConstructor() {
    JsonObjectImpl jsonObject = JsonObjectImpl.newBuilder().setProperty("foo", "bar").build();
    JsonObjectImpl jsonObject1 = new JsonObjectImpl(jsonObject);
    assertEquals("bar", jsonObject1.get("foo"));
  }

  @Test
  void entrySet() {
    JsonObjectImpl.Builder builder = JsonObjectImpl.newBuilder()
        .setProperty("foo", "bar")
        .setProperty("baz", "bot");
    Set<Map.Entry<@NotNull String, @Nullable Object>> entries = builder.entrySet();
    assertTrue(entries.contains(new AbstractMap.SimpleImmutableEntry<String, Object>("foo", "bar")));
    assertTrue(entries.contains(new AbstractMap.SimpleImmutableEntry<String, Object>("baz", "bot")));
  }
}

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
package edu.umn.nlpie.mtap.common;

import com.google.protobuf.ListValue;
import com.google.protobuf.NullValue;
import com.google.protobuf.Struct;
import com.google.protobuf.Value;

import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.*;

/**
 * A immutable representation of a JSON object, this class provides the basis of generic labels and
 * the parameter and results dictionaries for processing.
 * <p>
 * JSON objects do not have references, this means that attempting to add object graphs which
 * contain reference loops will fail. It also means that the entire object graph will be
 * replicated in full, even if the references are shared between different objects. In the case of
 * labels, objects that share references to data prior to serialization will not share those
 * references after deserialization, copies of the data will exist on both objects.
 * <p>
 * Valid types for storage in a Json map are
 * <ul>
 * <li>Java primitive types</li>
 * <li>Maps of strings to valid types</li>
 * <li>Lists of valid types.</li>
 * </ul>
 * <p>
 * In Json, all numbers are stored as floating point, so {@link Byte}, {@link Short},
 * {@link Integer}, {@link Long} are all cast to a {@link Double} value. Likewise,
 * {@link Float} is converted to {@link Double}. {@link String} and {@link Boolean} are stored
 * directly. {@link Character} is converted to a {@link String} of length 1.
 */
public abstract class JsonObject extends AbstractMap<@NotNull String, @Nullable Object> {

  private final Map<String, Object> backingMap;

  /**
   * Method that can be used by subclasses.
   *
   * @param backingMap The backing map that stores the values of properties.
   */
  protected JsonObject(Map<String, Object> backingMap) {
    this.backingMap = backingMap;
  }

  /**
   * Method that can be used to create a new json object by copying an existing json object.
   *
   * @param abstractJsonObject The json object to copy.
   */
  public JsonObject(JsonObject abstractJsonObject) {
    backingMap = abstractJsonObject.backingMap;
  }

  private static Value createValue(Object from) {
    if (from == null) {
      return Value.newBuilder().setNullValue(NullValue.NULL_VALUE).build();
    } else if (from instanceof List) {
      ListValue.Builder builder = ListValue.newBuilder();
      List<?> fromList = (List<?>) from;
      for (Object item : fromList) {
        Value value = createValue(item);
        builder.addValues(value);
      }
      return Value.newBuilder().setListValue(builder).build();
    } else if (from instanceof JsonObject) {
      Struct.Builder builder = Struct.newBuilder();
      JsonObject abstractJsonObject = (JsonObject) from;
      for (Entry<String, ?> entry : abstractJsonObject.entrySet()) {
        String key = entry.getKey();
        Object value = entry.getValue();
        Value protoValue = createValue(value);
        builder.putFields(key, protoValue);
      }
      return Value.newBuilder().setStructValue(builder).build();
    } else if (from instanceof Double) {
      return Value.newBuilder().setNumberValue((Double) from).build();
    } else if (from instanceof String) {
      return Value.newBuilder().setStringValue((String) from).build();
    } else if (from instanceof Boolean) {
      return Value.newBuilder().setBoolValue((Boolean) from).build();
    } else {
      throw new IllegalStateException("Incompatible value type: " + from.getClass().getCanonicalName());
    }
  }

  /**
   * Turns the object into one that can be directly serialized to json.
   *
   * @param value   The value to convert.
   * @param parents The list of parents to check for reference cycles.
   *
   * @return The converted value.
   */
  protected static Object jsonify(Object value, Deque<Object> parents) {
    Object result;
    if (value == null || value instanceof Double || value instanceof String || value instanceof Boolean || value instanceof JsonObject) {
      result = value;
    } else if (value instanceof JsonObjectBuilder) {
      result = ((JsonObjectBuilder<?, ?>) value).build();
    } else if (value instanceof Map) {
      checkForReferenceCycle(value, parents);
      Map<?, ?> map = (Map<?, ?>) value;
      JsonObjectImpl.Builder jsonBuilder = new JsonObjectImpl.Builder();
      parents.push(value);
      for (Map.Entry<?, ?> entry : map.entrySet()) {
        Object key = entry.getKey();
        Object val = entry.getValue();
        if (!(key instanceof String)) {
          throw new IllegalArgumentException("Nested maps must have keys of String type.");
        }
        jsonBuilder.setProperty((String) key, jsonify(val, parents));
      }
      parents.pop();
      result = jsonBuilder.build();
    } else if (value instanceof List) {
      checkForReferenceCycle(value, parents);
      List<?> list = (List<?>) value;
      List<Object> out = new ArrayList<>(list.size());
      parents.push(list);
      for (Object o : list) {
        out.add(jsonify(o, parents));
      }
      result = out;
      parents.pop();
    } else if (value instanceof Long) {
      result = ((Long) value).doubleValue();
    } else if (value instanceof Integer) {
      result = ((Integer) value).doubleValue();
    } else if (value instanceof Short) {
      result = ((Short) value).doubleValue();
    } else if (value instanceof Byte) {
      result = ((Byte) value).doubleValue();
    } else if (value instanceof Float) {
      result = ((Float) value).doubleValue();
    } else if (value instanceof Character) {
      result = "" + value;
    } else throw new IllegalArgumentException("Value type cannot be represented in json: \""
        + value.getClass().getName() + "\". Valid types are Java primitive objects, " +
        " lists of objects of valid types, and maps of strings to objects of valid types");
    return result;
  }

  static Object getValue(Value from) {
    switch (from.getKindCase()) {
      case NULL_VALUE:
        return null;
      case NUMBER_VALUE:
        return from.getNumberValue();
      case STRING_VALUE:
        return from.getStringValue();
      case BOOL_VALUE:
        return from.getBoolValue();
      case STRUCT_VALUE:
        JsonObjectImpl.Builder builder = new JsonObjectImpl.Builder();
        builder.copyStruct(from.getStructValue());
        return builder.build();
      case LIST_VALUE:
        List<Object> list = new ArrayList<>();
        for (Value value : from.getListValue().getValuesList()) {
          list.add(getValue(value));
        }
        return list;
      case KIND_NOT_SET:
      default:
        throw new IllegalStateException("Unrecognized kind of struct value.");
    }
  }

  protected static void checkForReferenceCycle(Object value, Deque<Object> parents) {
    for (Object parent : parents) {
      if (parent == value) {
        throw new IllegalArgumentException("Detected reference cycle.");
      }
    }
  }

  public Struct.Builder copyToStruct(Struct.Builder structBuilder) {
    for (Entry<String, ?> entry : entrySet()) {
      String key = entry.getKey();
      Object value = entry.getValue();
      Value protoValue = createValue(value);
      structBuilder.putFields(key, protoValue);
    }
    return structBuilder;
  }

  public String getStringValue(@NotNull String propertyName) {
    return (String) backingMap.get(propertyName);
  }

  public Double getNumberValue(@NotNull String propertyName) {
    return (Double) backingMap.get(propertyName);
  }

  public Boolean getBooleanValue(@NotNull String propertyName) {
    return (Boolean) backingMap.get(propertyName);
  }

  public JsonObject getJsonObjectValue(@NotNull String propertyName) {
    return (JsonObject) backingMap.get(propertyName);
  }

  public List<?> getListValue(@NotNull String propertyName) {
    return (List<?>) backingMap.get(propertyName);
  }

  @Override
  public boolean containsKey(Object key) {
    return backingMap.containsKey(key);
  }

  @Override
  public Object get(Object key) {
    return backingMap.get(key);
  }

  /**
   * A view of all of the entries/properties in this object.
   *
   * @return Unmodifiable view of the properties in this object.
   */
  public @NotNull Set<Map.Entry<@NotNull String, @Nullable Object>> entrySet() {
    return Collections.unmodifiableMap(backingMap).entrySet();
  }
}

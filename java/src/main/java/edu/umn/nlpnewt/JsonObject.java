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
import org.jetbrains.annotations.Nullable;

import java.util.*;

/**
 * A representation of a JSON object, this class provides the basis of generic labels and the
 * parameter and results dictionaries for processing.
 * <p>
 * JSON objects do not have references, this means that attempting to add lists or
 * maps which contain reference loops will fail. It also means that the entire object graph will be
 * replicated in full, even if the references are shared between different objects. In the case of
 * labels, objects that share references to data prior to serialization will not share those
 * references after deserialization.
 */
public class JsonObject {

  private final Map<String, Object> backingMap;

  protected JsonObject(Map<String, Object> backingMap) {
    this.backingMap = backingMap;
  }

  protected JsonObject(JsonObject jsonObject) {
    backingMap = jsonObject.backingMap;
  }

  /**
   * Returns the
   *
   * @param key
   * @return
   */
  public @Nullable String getStringValue(@NotNull String key) {
    return (String) backingMap.get(key);
  }

  public @Nullable Double getNumberValue(@NotNull String key) {
    return (Double) backingMap.get(key);
  }

  public @Nullable JsonObject getJsonObjectValue(@NotNull String key) {
    return (JsonObject) backingMap.get(key);
  }

  public @Nullable Boolean getBooleanValue(@NotNull String key) {
    return (Boolean) backingMap.get(key);
  }

  public @Nullable List getListValue(@NotNull String key) {
    return (List) backingMap.get(key);
  }

  public Set<String> keySet() {
    return Collections.unmodifiableMap(backingMap).keySet();
  }

  public Collection<Object> values() {
    return Collections.unmodifiableMap(backingMap).values();
  }

  public Set<Map.Entry<String, Object>> entrySet() {
    return Collections.unmodifiableMap(backingMap).entrySet();
  }

  /**
   *
   * @param <T>
   * @param <U>
   */
  public abstract static class AbstractBuilder<T extends AbstractBuilder, U extends JsonObject> {
    protected Map<@NotNull String, @Nullable Object> backingMap = new HashMap<>();

    @SuppressWarnings("unchecked")
    @NotNull
    public final T setProperty(@NotNull String key, @Nullable Object value) {
      backingMap.put(key, jsonify(value));
      return (T) this;
    }

    @SuppressWarnings("unchecked")
    public final T setProperties(Map<@NotNull String, @Nullable Object> map) {
      backingMap.putAll(map);
      return (T) this;
    }

    public Set<Map.Entry<@NotNull String, @Nullable Object>> entrySet() {
      return backingMap.entrySet();
    }

    public abstract U build();
  }

  public final static class Builder extends AbstractBuilder<Builder, JsonObject> {
    public Builder() {}

    @Override
    public JsonObject build() {
      return new JsonObject(backingMap);
    }
  }

  protected static Object jsonify(Object value) {
    return internalJsonify(value, new LinkedList<>());
  }

  private static Object internalJsonify(Object value, Deque<Object> parents) {
    Object result;
    if (value instanceof Map) {
      Map<?, ?> map = (Map<?, ?>) value;
      Map<String, Object> out = new HashMap<>();
      parents.push(value);
      for (Map.Entry<?, ?> entry : map.entrySet()) {
        Object key = entry.getKey();
        Object val = entry.getValue();
        if (!(key instanceof String)) {
          throw new IllegalStateException("Nested maps must have keys of String type.");
        }
        out.put((String) key, internalJsonify(val, parents));
      }
      result = out;
    } else if (value instanceof JsonObject) {
      result = value;
    } else if (value instanceof List) {
      List<?> list = (List<?>) value;
      List<Object> out = new ArrayList<>(list.size());
      parents.push(value);
      for (Object o : list) {
        out.add(internalJsonify(o, parents));
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
    } else if (value instanceof Double || value instanceof String || value instanceof Boolean) {
      result = value;
    } else throw new IllegalArgumentException("Value type cannot be represented in json: \""
        + value.getClass().getName() + "\". Valid types are Java primitive objects, " +
        " lists of objects of valid types, and maps of strings to objects of valid types");
    return result;
  }

}

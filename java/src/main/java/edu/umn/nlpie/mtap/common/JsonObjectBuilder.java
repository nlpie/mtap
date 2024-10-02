package edu.umn.nlpie.mtap.common;

import java.util.AbstractMap;
import java.util.Collections;
import java.util.Deque;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import com.google.protobuf.Struct;
import com.google.protobuf.Value;

import edu.umn.nlpie.mtap.model.Builder;

/**
   * An abstract builder for json objects which can used by subclasses to provide builders.
   *
   * @param <T> The newBuilder type to be returned by newBuilder methods.
   */
  public abstract class JsonObjectBuilder<T extends JsonObjectBuilder<?, ?>, R extends JsonObject>
      extends AbstractMap<@NotNull String, @Nullable Object> implements Builder<R> {

    protected Map<@NotNull String, @Nullable Object> backingMap = new HashMap<>();

    @SuppressWarnings("unchecked")
    @NotNull
    public T copyStruct(Struct struct) {
      if (struct == null) {
        return (T) this;
      }
      Map<String, Value> fieldsMap = struct.getFieldsMap();
      for (Entry<String, Value> entry : fieldsMap.entrySet()) {
        setProperty(entry.getKey(), JsonObject.getValue(entry.getValue()));
      }
      return (T) this;
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

    @SuppressWarnings("unchecked")
    @NotNull
    public final T setProperty(@NotNull String propertyName, @Nullable Object value) {
      put(propertyName, value);
      return (T) this;
    }

    @Override
    public Object put(@NotNull String key, @Nullable Object value) {
      Deque<Object> parents = new LinkedList<>();
      parents.push(this);
      return backingMap.put(key, JsonObject.jsonify(value, parents));
    }

    @SuppressWarnings("unchecked")
    public final T setProperties(Map<@NotNull String, @Nullable Object> map) {
      putAll(map);
      return (T) this;
    }

    @Override
    public boolean containsKey(Object key) {
      return backingMap.containsKey(key);
    }

    @Override
    public Object get(Object key) {
      return backingMap.get(key);
    }

    @Override
    public Set<Map.Entry<@NotNull String, @Nullable Object>> entrySet() {
      return Collections.unmodifiableMap(backingMap).entrySet();
    }
  }
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

import com.google.protobuf.Struct;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.List;
import java.util.Map;

public interface JsonObjectBuilder<T extends JsonObjectBuilder, R extends JsonObject>
    extends Map<@NotNull String, @Nullable Object> {
  /**
   * Copies the contents of a protobuf struct to this builder.
   *
   * @param struct The protobuf struct message.
   *
   * @return A new json object containing all of the information from the struct.
   */
  T copyStruct(Struct struct);

  /**
   * Returns the property cast as a {@link String} object.
   *
   * @param propertyName The property name.
   *
   * @return Value stored under the property name given cast as a String.
   */
  String getStringValue(@NotNull String propertyName);

  /**
   * Returns the property cast as a {@link Double} object.
   *
   * @param propertyName The name the property is stored under.
   *
   * @return Value stored under the property name cast as a Double.
   */
  Double getNumberValue(@NotNull String propertyName);

  /**
   * Returns the property cast as a {@link Boolean} object.
   *
   * @param propertyName The name of the property.
   *
   * @return Value stored under the property name cast as a JsonObject.
   */
  Boolean getBooleanValue(@NotNull String propertyName);

  /**
   * Returns the property cast as a {@link AbstractJsonObject}.
   *
   * @param propertyName The name the property is stored under.
   *
   * @return Value stored under the property name cast as a JsonObject.
   */
  AbstractJsonObject getJsonObjectValue(@NotNull String propertyName);

  /**
   * Returns the property cast as a {@link List}.
   *
   * @param propertyName The name the property is stored under.
   *
   * @return Value stored under the property name cast as a {@link List}.
   */
  List getListValue(@NotNull String propertyName);

  /**
   * Builder method which sets a property keyed by {@code propertyName} to the {@code value}.
   *
   * @param propertyName The name the property should be stored under.
   * @param value        The value of the property.
   *
   * @return This builder.
   */
  T setProperty(@NotNull String propertyName, @Nullable Object value);

  /**
   * Builder method which sets all of the properties in {@code map}.
   *
   * @param map The map of string property names to property values.
   *
   * @return This builder.
   */
  T setProperties(Map<@NotNull String, @Nullable Object> map);

  /**
   * Creates the concrete json object type.
   *
   * @return The json object implementation type.
   */
  R build();
}

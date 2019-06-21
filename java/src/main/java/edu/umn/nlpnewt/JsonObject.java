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

/**
 * A immutable representation of a JSON object, this class provides the basis of generic labels and
 * the parameter and results dictionaries for processing.
 */
public interface JsonObject extends Map<@NotNull String, @Nullable Object> {
  /**
   * Copies a json object to a protobuf struct newBuilder.
   *
   * @param structBuilder The protobuf struct newBuilder.
   *
   * @return A struct builder containing all of the fields from the json object.
   */
  Struct.Builder copyToStruct(Struct.Builder structBuilder);

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
  JsonObject getJsonObjectValue(@NotNull String propertyName);

  /**
   * Returns the property cast as a {@link List}.
   *
   * @param propertyName The name the property is stored under.
   *
   * @return Value stored under the property name cast as a {@link List}.
   */
  List getListValue(@NotNull String propertyName);
}

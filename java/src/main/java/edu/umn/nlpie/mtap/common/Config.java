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

import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.Map;

public interface Config {
  /**
   * Creates a copy of this configuration object.
   *
   * @return A shallow copy of this configuration object.
   */
  Config copy();

  /**
   * The value for {@code key}. Null if the value is set to null or the configuration does not
   * contain {@code key}.
   *
   * @param key The key path.
   *
   * @return Object value or null.
   */
  Object get(@NotNull String key);

  /**
   * The value for {@code key} cast as a String. Null if the value is set to null, or the map does
   * not contain {@code key}
   *
   * @param key The key path.
   *
   * @return String value or null.
   */
  String getStringValue(@NotNull String key);

  /**
   * The value for {@code key} cast as a String. Null if the value is set to null, or the map does
   * not contain {@code key}.
   *
   * @param key The key path.
   *
   * @return String value or null.
   */
  Integer getIntegerValue(@NotNull String key);

  /**
   * The value for {@code key} cast as a Double. Null if the value is set to null, or if the map does
   * not contain {@code key}.
   *
   * @param key The key path.
   *
   * @return Double value or null.
   */
  Double getDoubleValue(@NotNull String key);

  /**
   * The value for {@code key} cast as a Boolean. Null if the value is set to null, or if the map
   * does not contain {@code key}.
   *
   * @param key The key path.
   *
   * @return Boolean value or null
   */
  Boolean getBooleanValue(@NotNull String key);

  /**
   * Sets the configuration values contained in {@code updates}.
   *
   * @param updates A Map of keys to their values, which should be {@link Integer}, {@link String},
   *                {@link Boolean}, {@link Double}, or {@code null}.
   */
  void update(Map<@NotNull String, @Nullable Object> updates);

  /**
   * Updates this config with the configuration stored in another config file.
   *
   * @param config Other config file.
   */
  void update(Config config);

  /**
   * Sets a configuration keyed by {@code key} to {@code value}.
   *
   * @param key   The key.
   * @param value a value, one of {@link Integer}, {@link String}, {@link Boolean},
   *              {@link Double}, or {@code null}.
   */
  void set(@NotNull String key, @Nullable Object value);

  /**
   * Returns this configuration object as a map.
   *
   * @return View of the config as a map.
   */
  Map<@NotNull String, @Nullable Object> asMap();
}

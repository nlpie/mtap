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
import org.yaml.snakeyaml.Yaml;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Global system configuration object.
 * <p>
 * By default, will attempt to load a configuration from the following locations:
 * <ol>
 * <li>The {@code NEWT-CONFIG} environment variable</li>
 * <li>{@code $PWD/newtConfig.yaml}</li>
 * <li>{@code $HOME/.newt/newtConfig.yaml}</li>
 * <li>{@code /etc/newt/newtConfig.yaml}</li>
 * </ol>
 * <p>
 * Nested objects in the configuration yaml file will be flattened, for example the map:
 * <pre>
 *   {
 *     'a' : {
 *       'b': 1,
 *       'c': 2
 *     }
 *   }
 * </pre>
 * Will become the map:
 * <pre>
 *   {
 *     'a.b': 1,
 *     'a.c': 2
 *   }
 * </pre>
 */
public final class Config {

  private final Map<String, Object> config;

  private Config(Map<String, Object> config) {
    this.config = config;
  }

  private Config(Config config) {
    this.config = new HashMap<>(config.config);
  }

  /**
   * Loads a configuration from one of the default locations if there is a configuration file
   * present.
   *
   * @return Configuration object containing the flattened key-values from the yaml file.
   *
   * @throws IOException If the first configuration file it finds fails to load.
   */
  public static @NotNull Config loadFromDefaultLocations() throws IOException {
    return loadConfigFromLocationOrDefaults(null);
  }

  /**
   * Loads a configuration from the parameter or one of the default locations if there is a
   * configuration file present. Will use the default config if none are present.
   *
   * @param configPath An optional path to a file to attempt to load configuration from.
   *
   * @return Configuration object containing the flattened key-values from the yaml file.
   *
   * @throws IOException If the first configuration file it finds fails to load.
   */
  public static @NotNull Config loadConfigFromLocationOrDefaults(
      @Nullable Path configPath
  ) throws IOException {
    String envVarPath = System.getenv("NEWT-CONFIG");
    List<Path> searchPaths = Arrays.asList(
        Paths.get("."),
        Paths.get(System.getProperty("user.home")).resolve(".newt"),
        Paths.get("/etc/newt/"));
    if (envVarPath != null) {
      searchPaths.add(0, Paths.get(envVarPath));
    }
    if (configPath != null) {
      searchPaths.add(0, configPath);
    }
    for (Path path : searchPaths) {
      Path configFile = path.resolve("newtConfig.yaml");
      if (Files.exists(configFile)) {
        return loadConfig(configFile);
      }
    }
    return defaultConfig();
  }

  /**
   * Loads a configuration from the specified configPath.
   *
   * @param configFile Path to a configuration yaml file.
   *
   * @return Configuration object containing the flattened key-values from the yaml file.
   *
   * @throws IOException If the file fails to load.
   */
  private static @NotNull Config loadConfig(Path configFile) throws IOException {
    try (InputStream inputStream = Files.newInputStream(configFile)) {
      Yaml yaml = new Yaml();
      Map<String, Object> yamlMap = yaml.load(inputStream);
      Map<String, Object> targetMap = new HashMap<>();
      flattenConfig(yamlMap, "", targetMap);
      return new Config(targetMap);
    }
  }

  /**
   * The default configuration for nlp-newt.
   *
   * @return Configuration object containing default configuration.
   */
  public static @NotNull Config defaultConfig() {
    Map<String, Object> map = new HashMap<>();
    map.put("discovery", "consul");
    map.put("consul.host", "localhost");
    map.put("consul.port", 8500);
    map.put("consul.scheme", "http");
    map.put("consul.dns_ip", "127.0.0.1");
    map.put("consul.dns_port", 8600);
    return new Config(map);
  }

  /**
   * A configuration containing no keys.
   *
   * @return Empty configuration object.
   */
  public static @NotNull Config emptyConfig() {
    return new Config(new HashMap<>());
  }

  @SuppressWarnings("unchecked")
  private static void flattenConfig(Map<String, Object> map,
                                    String prefix,
                                    Map<String, Object> targetMap) {
    for (Map.Entry<String, Object> entry : map.entrySet()) {
      String key = entry.getKey();
      Object value = entry.getValue();
      String newPrefix = prefix + (prefix.length() > 0 ? "." : "") + key;
      if (value instanceof Map) {
        flattenConfig((Map<String, Object>) value, newPrefix, targetMap);
      } else {
        targetMap.put(newPrefix, value);
      }
    }
  }

  /**
   * Creates a copy of this configuration object.
   *
   * @return A shallow copy of this configuration object.
   */
  public Config copy() {
    return new Config(this);
  }

  /**
   * The value for {@code key}. Null if the value is set to null or the configuration does not
   * contain {@code key}.
   *
   * @param key The key path.
   *
   * @return Object value or null.
   */
  public Object get(@NotNull String key) {
    return config.get(key);
  }

  /**
   * The value for {@code key} cast as a String. Null if the value is set to null, or the map does
   * not contain {@code key}
   *
   * @param key The key path.
   *
   * @return String value or null.
   */
  public String getStringValue(@NotNull String key) {
    return (String) config.get(key);
  }

  /**
   * The value for {@code key} cast as a String. Null if the value is set to null, or the map does
   * not contain {@code key}.
   *
   * @param key The key path.
   *
   * @return String value or null.
   */
  public Integer getIntegerValue(@NotNull String key) {
    return (Integer) config.get(key);
  }

  /**
   * The value for {@code key} cast as a Double. Null if the value is set to null, or if the map does
   * not contain {@code key}.
   *
   * @param key The key path.
   *
   * @return Double value or null.
   */
  public Double getDoubleValue(@NotNull String key) {
    return (Double) config.get(key);
  }

  /**
   * The value for {@code key} cast as a Boolean. Null if the value is set to null, or if the map
   * does not contain {@code key}.
   *
   * @param key The key path.
   *
   * @return Boolean value or null
   */
  public Boolean getBooleanValue(@NotNull String key) {
    return (Boolean) config.get(key);
  }

  /**
   * Sets the configuration values contained in {@code updates}.
   *
   * @param updates A Map of keys to their values, which should be {@link Integer}, {@link String},
   *                {@link Boolean}, {@link Double}, or {@code null}.
   */
  public void update(Map<@NotNull String, @Nullable Object> updates) {
    config.putAll(updates);
  }

  /**
   * Sets a configuration keyed by {@code key} to {@code value}.
   *
   * @param key   The key.
   * @param value a value, one of {@link Integer}, {@link String}, {@link Boolean},
   *              {@link Double}, or {@code null}.
   */
  public void set(@NotNull String key, @Nullable Object value) {
    config.put(key, value);
  }
}

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
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
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
public final class ConfigImpl implements Config {
  private static final Logger LOGGER = LoggerFactory.getLogger(ConfigImpl.class);

  private final Map<String, Object> config;

  private ConfigImpl(Map<String, Object> config) {
    this.config = config;
  }

  private ConfigImpl(ConfigImpl config) {
    this.config = new HashMap<>(config.config);
  }

  public static Config createByCopying(Config config) {
    ConfigImpl newConfig = new ConfigImpl(new HashMap<>());
    newConfig.update(config);
    return newConfig;
  }

  /**
   * Loads a configuration from one of the default locations if there is a configuration file
   * present.
   *
   * @return Configuration object containing the flattened key-values from the yaml file.
   */
  public static @NotNull Config loadFromDefaultLocations() {
    return loadConfigFromLocationOrDefaults(null);
  }

  /**
   * Loads a configuration from the parameter or one of the default locations if there is a
   * configuration file present. Will use the default config if none are present.
   *
   * @param configPath An optional path to a file to attempt to load configuration from.
   *
   * @return Configuration object containing the flattened key-values from the yaml file.
   */
  public static @NotNull Config loadConfigFromLocationOrDefaults(@Nullable Path configPath) {
    String envVarPath = System.getenv("NEWT-CONFIG");
    List<Path> searchPaths = Arrays.asList(
        Paths.get("./newtConfig.yaml"),
        Paths.get(System.getProperty("user.home")).resolve(".newt/newtConfig.yaml"),
        Paths.get("/etc/newt/newtConfig.yaml"));
    if (envVarPath != null) {
      searchPaths.add(0, Paths.get(envVarPath));
    }
    if (configPath != null) {
      searchPaths.add(0, configPath);
    }
    for (Path path : searchPaths) {
      if (Files.exists(path)) {
        LOGGER.info("Using configuration file: {}", path.toString());
        return loadConfig(path);
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
   */
  public static @NotNull ConfigImpl loadConfig(Path configFile) {
    try (InputStream inputStream = Files.newInputStream(configFile)) {
      Yaml yaml = new Yaml();
      Map<String, Object> yamlMap = yaml.load(inputStream);
      Map<String, Object> targetMap = new HashMap<>();
      flattenConfig(yamlMap, "", targetMap);
      return new ConfigImpl(targetMap);
    } catch (IOException e) {
      throw new IllegalStateException("Failed to load configuration.", e);
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
    return new ConfigImpl(map);
  }

  /**
   * A configuration containing no keys.
   *
   * @return Empty configuration object.
   */
  public static @NotNull Config emptyConfig() {
    return new ConfigImpl(new HashMap<>());
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

  @Override
  public Config copy() {
    return new ConfigImpl(this);
  }

  @Override
  public Object get(@NotNull String key) {
    return config.get(key);
  }

  @Override
  public String getStringValue(@NotNull String key) {
    return (String) config.get(key);
  }

  @Override
  public Integer getIntegerValue(@NotNull String key) {
    return (Integer) config.get(key);
  }

  @Override
  public Double getDoubleValue(@NotNull String key) {
    return (Double) config.get(key);
  }

  @Override
  public Boolean getBooleanValue(@NotNull String key) {
    return (Boolean) config.get(key);
  }

  @Override
  public void update(Map<@NotNull String, @Nullable Object> updates) {
    config.putAll(updates);
  }


  @Override
  public void update(Config config) {
    this.config.putAll(config.asMap());
  }

  @Override
  public void set(@NotNull String key, @Nullable Object value) {
    config.put(key, value);
  }

  @Override
  public Map<@NotNull String, @Nullable Object> asMap() {
    return config;
  }
}

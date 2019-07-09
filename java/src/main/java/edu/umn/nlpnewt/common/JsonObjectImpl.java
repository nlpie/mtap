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
package edu.umn.nlpnewt.common;

import java.util.Map;

/**
 * A concrete implementation of a JsonObject.
 * <p>
 * {@inheritDoc}
 */
public final class JsonObjectImpl extends AbstractJsonObject {


  private JsonObjectImpl(Map<String, Object> backingMap) {
    super(backingMap);
  }

  /**
   * Creates a new json object as a copy of the json object.
   *
   * @param jsonObject Json object to copy.
   */
  public JsonObjectImpl(AbstractJsonObject jsonObject) {
    super(jsonObject);
  }


  /**
   * Creates a new Builder for json objects.
   *
   * @return An empty Builder for a json object.
   */
  public static Builder newBuilder() {
    return new Builder();
  }

  /**
   * A concrete Builder for {@link JsonObjectImpl}.
   */
  public final static class Builder extends AbstractBuilder<Builder, JsonObjectImpl> {
    /**
     * Creates a {@link JsonObjectImpl}
     *
     * @return The finalized, immutable json object containing the properties that have been added
     * to this builder.
     */
    @Override
    public JsonObjectImpl build() {
      return new JsonObjectImpl(backingMap);
    }
  }
}

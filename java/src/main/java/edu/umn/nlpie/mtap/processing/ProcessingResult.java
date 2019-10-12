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

package edu.umn.nlpie.mtap.processing;

import edu.umn.nlpie.mtap.Internal;
import edu.umn.nlpie.mtap.common.JsonObject;

import java.time.Duration;
import java.util.List;
import java.util.Map;

@Internal
class ProcessingResult {
  private final Map<String, List<String>> createdIndices;
  private final Map<String, Duration> times;
  private final JsonObject result;

  ProcessingResult(
      Map<String, List<String>> createdIndices,
      Map<String, Duration> times,
      JsonObject result
  ) {
    this.createdIndices = createdIndices;
    this.times = times;
    this.result = result;
  }

  public Map<String, List<String>> getCreatedIndices() {
    return createdIndices;
  }

  public Map<String, Duration> getTimes() {
    return times;
  }

  public JsonObject getResult() {
    return result;
  }
}

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

import java.util.Map;

@Internal
public interface Runner extends AutoCloseable {
  ProcessingResult process(String eventID, JsonObject params);

  String getProcessorName();

  String getProcessorId();

  Map<String, Object> getProcessorMeta();

  @Override
  void close();
}

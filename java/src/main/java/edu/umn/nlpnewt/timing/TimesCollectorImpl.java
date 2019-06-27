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

package edu.umn.nlpnewt.timing;

import edu.umn.nlpnewt.Internal;
import edu.umn.nlpnewt.api.v1.Processing;

import java.util.AbstractMap;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Future;
import java.util.stream.Collectors;

@Internal
class TimesCollectorImpl implements TimesCollector {
  private final Map<String, RunningVariance> timesMap = new HashMap<>();
  private final ExecutorService executor;

  public TimesCollectorImpl(ExecutorService executor) {
    this.executor = executor;
  }

  @Override
  public void addTime(String key, long time) {
    executor.submit(() -> {
      RunningVariance runningVariance = timesMap.computeIfAbsent(key,
          unused -> new RunningVariance());
      runningVariance.addTime(time);
    });
  }

  @Override
  public Map<String, Processing.TimerStats> getTimerStats() {
    Future<Map<String, Processing.TimerStats>> future = executor.submit(
        () -> timesMap.entrySet().stream()
            .map(e -> new AbstractMap.SimpleImmutableEntry<>(
                e.getKey(),
                e.getValue().createStats())
            )
            .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue))
    );
    try {
      return future.get();
    } catch (InterruptedException | ExecutionException e) {
      throw new IllegalArgumentException(e);
    }
  }
}

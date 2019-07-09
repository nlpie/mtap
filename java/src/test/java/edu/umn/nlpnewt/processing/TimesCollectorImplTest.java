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

package edu.umn.nlpnewt.processing;

import com.google.protobuf.util.Durations;
import edu.umn.nlpnewt.api.v1.Processing;
import org.jetbrains.annotations.NotNull;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.concurrent.AbstractExecutorService;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

class TimesCollectorImplTest {

  private TimesCollectorImpl timesCollector;

  @BeforeEach
  void setUp() {
    timesCollector = new TimesCollectorImpl(new AbstractExecutorService() {
      @Override
      public void shutdown() {

      }

      @NotNull
      @Override
      public List<Runnable> shutdownNow() {
        return null;
      }

      @Override
      public boolean isShutdown() {
        return false;
      }

      @Override
      public boolean isTerminated() {
        return false;
      }

      @Override
      public boolean awaitTermination(long timeout, @NotNull TimeUnit unit) throws InterruptedException {
        return false;
      }

      @Override
      public void execute(@NotNull Runnable command) {
        command.run();
      }
    });
  }

  @Test
  void testAddTime() {
    for (Integer i : Arrays.asList(3156, 1289, 3778, 1526, 3882, 4625, 3214, 1426, 2982, 874, 1226,
        2774, 1013, 4719, 3393, 2622, 1010, 1011, 2941, 3775, 3467, 4547,
        4176, 703, 606, 1485, 137, 2640, 2052, 138, 4748, 3350, 4939,
        1838, 3423, 807, 1827, 4502, 2335, 4822, 399, 1742, 248, 2662,
        1935, 931, 595, 2740, 891, 738)) {
      timesCollector.addTime("test", i);
    }
    Map<String, Processing.TimerStats> timerStats = timesCollector.getTimerStats();
    Processing.TimerStats stats = timerStats.get("test");
    assertNotNull(stats);
    assertEquals(1450, Durations.toNanos(stats.getStd()));
    assertEquals(137, Durations.toNanos(stats.getMin()));
    assertEquals(4939, Durations.toNanos(stats.getMax()));
    assertEquals(2333, Durations.toNanos(stats.getMean()));
    assertEquals(116659, Durations.toNanos(stats.getSum()));
  }
}

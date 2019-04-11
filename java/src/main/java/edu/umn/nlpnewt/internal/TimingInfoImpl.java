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
package edu.umn.nlpnewt.internal;

import com.google.common.base.Stopwatch;
import edu.umn.nlpnewt.Internal;
import edu.umn.nlpnewt.Timer;
import edu.umn.nlpnewt.TimingInfo;

import java.time.Duration;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.TimeUnit;

@Internal
final class TimingInfoImpl implements TimingInfo, AutoCloseable {
  private static final ThreadLocal<TimingInfoImpl> THREAD_LOCAL = ThreadLocal.withInitial(TimingInfoImpl::new);
  static TimingInfoImpl getTimingInfo() {
    return THREAD_LOCAL.get();
  }


  private final Map<String, Duration> times = new HashMap<>();

  private String identifier = null;

  private boolean active = false;

  void activate(String identifier) {
    if (active) {
      throw new IllegalStateException("Timing info is already active");
    }
    this.identifier = identifier;
    times.clear();
    active = true;
  }

  @Override
  public Timer start(String key) {
    if (!active) {
      throw new IllegalStateException("Attempted to start a timer outside of a processing context.");
    }

    Stopwatch stopwatch = Stopwatch.createStarted();

    return () -> {

      if (!active) {
        throw new IllegalStateException("Attempted to stop a timer outside of a processing context.");
      }
      times.put(identifier + ":" + key, stopwatch.elapsed());
    };
  }

  Map<String, Duration> getTimes() {
    return times;
  }

  @Override
  public void close() {
    active = false;
  }
}

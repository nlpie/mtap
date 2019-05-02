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

package edu.umn.nlpnewt.internal;

import com.google.protobuf.util.Durations;
import edu.umn.nlpnewt.api.v1.Processing;

class RunningVariance {
  private long count = 0;
  private long min = Long.MAX_VALUE;
  private long max = 0;
  private double mean = 0;
  private double sse = 0;
  private long sum = 0;

  void addTime(long time) {
    if (time < min) {
      min = time;
    }
    if (time > max) {
      max = time;
    }

    count++;
    sum += time;
    double delta = time - mean;
    mean += delta / count;
    double delta2 = time - mean;
    sse += delta * delta2;
  }

  Processing.TimerStats createStats() {
    return Processing.TimerStats.newBuilder()
        .setMean(Durations.fromNanos(Math.round(mean)))
        .setStd(Durations.fromNanos(getStd()))
        .setMin(Durations.fromNanos(min))
        .setMax(Durations.fromNanos(max))
        .setSum(Durations.fromNanos(sum))
        .build();
  }

  long getStd() {
    return Math.round(Math.sqrt(sse / count));
  }

  long getCount() {
    return count;
  }

  long getMin() {
    return min;
  }

  long getMax() {
    return max;
  }

  double getMean() {
    return mean;
  }

  double getSse() {
    return sse;
  }

  long getSum() {
    return sum;
  }
}

package edu.umn.nlpie.mtap.processing;

import edu.umn.nlpie.mtap.api.v1.Processing;

import java.util.Map;
import java.util.concurrent.ExecutionException;

public interface TimingService {
  void addTime(String key, long nanos);

  Map<String, Processing.TimerStats> getTimerStats() throws InterruptedException, ExecutionException;
}

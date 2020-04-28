package edu.umn.nlpie.mtap.processing;

import edu.umn.nlpie.mtap.Internal;
import edu.umn.nlpie.mtap.api.v1.Processing;

import java.util.AbstractMap;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.stream.Collectors;

@Internal
public class DefaultTimingService implements TimingService {
  private final ExecutorService timingExecutor = Executors.newSingleThreadExecutor();
  private final Map<String, RunningVariance> timesMap = new HashMap<>();

  @Override
  public void addTime(String key, long nanos) {
    timingExecutor.submit(() -> {
      RunningVariance runningVariance = timesMap.computeIfAbsent(key,
          unused -> new RunningVariance());
      runningVariance.addTime(nanos);
    });
  }

  @Override
  public Map<String, Processing.TimerStats> getTimerStats() throws InterruptedException, ExecutionException {
    Future<Map<String, Processing.TimerStats>> future = timingExecutor.submit(
        () -> timesMap.entrySet().stream()
            .map(e -> new AbstractMap.SimpleImmutableEntry<>(
                e.getKey(),
                e.getValue().createStats())
            )
            .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue))
    );
    return future.get();
  }
}

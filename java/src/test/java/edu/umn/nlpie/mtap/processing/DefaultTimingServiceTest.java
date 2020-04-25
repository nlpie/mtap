package edu.umn.nlpie.mtap.processing;

import com.google.protobuf.util.Durations;
import edu.umn.nlpie.mtap.api.v1.Processing;
import org.junit.jupiter.api.Test;

import java.util.Arrays;
import java.util.Map;
import java.util.concurrent.ExecutionException;

import static org.junit.jupiter.api.Assertions.*;

class DefaultTimingServiceTest {
  @Test
  void testAddTime() throws ExecutionException, InterruptedException {
    TimingService tested = new DefaultTimingService();
    for (Integer i : Arrays.asList(3156, 1289, 3778, 1526, 3882, 4625, 3214, 1426, 2982, 874, 1226,
        2774, 1013, 4719, 3393, 2622, 1010, 1011, 2941, 3775, 3467, 4547,
        4176, 703, 606, 1485, 137, 2640, 2052, 138, 4748, 3350, 4939,
        1838, 3423, 807, 1827, 4502, 2335, 4822, 399, 1742, 248, 2662,
        1935, 931, 595, 2740, 891, 738)) {
      tested.addTime("test", i);
    }
    Map<String, Processing.TimerStats> timerStats = tested.getTimerStats();
    Processing.TimerStats stats = timerStats.get("test");
    assertNotNull(stats);
    assertEquals(1450, Durations.toNanos(stats.getStd()));
    assertEquals(137, Durations.toNanos(stats.getMin()));
    assertEquals(4939, Durations.toNanos(stats.getMax()));
    assertEquals(2333, Durations.toNanos(stats.getMean()));
    assertEquals(116659, Durations.toNanos(stats.getSum()));
  }
}
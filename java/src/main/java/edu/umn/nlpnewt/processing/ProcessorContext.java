package edu.umn.nlpnewt.processing;

import edu.umn.nlpnewt.Internal;
import org.jetbrains.annotations.NotNull;

import java.time.Duration;
import java.util.Map;

@Internal
public interface ProcessorContext extends AutoCloseable {
  void putTime(@NotNull String key, @NotNull Duration duration);

  @NotNull Map<String, Duration> getTimes();

  @Override
  void close();
}

package edu.umn.nlpie.mtap.processing;

import io.grpc.BindableService;
import org.jetbrains.annotations.NotNull;

public interface HealthService {
  void startedServing(@NotNull String processorId);

  void stoppedServing(@NotNull String processorId);

  BindableService getService();
}

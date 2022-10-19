package edu.umn.nlpie.mtap.processing;

import io.grpc.BindableService;
import io.grpc.health.v1.HealthCheckResponse;
import io.grpc.protobuf.services.HealthStatusManager;
import org.jetbrains.annotations.NotNull;

public class HSMHealthService implements HealthService {
  private final HealthStatusManager healthStatusManager = new HealthStatusManager();

  @Override
  public void startedServing(@NotNull String identifier) {
    healthStatusManager.setStatus(identifier, HealthCheckResponse.ServingStatus.SERVING);
  }

  @Override
  public void stoppedServing(@NotNull String identifier) {
    healthStatusManager.setStatus(identifier, HealthCheckResponse.ServingStatus.NOT_SERVING);
  }

  @Override
  public BindableService getService() {
    return healthStatusManager.getHealthService();
  }
}

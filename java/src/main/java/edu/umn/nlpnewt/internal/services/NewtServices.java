package edu.umn.nlpnewt.internal.services;

import edu.umn.nlpnewt.Config;
import edu.umn.nlpnewt.Internal;
import io.grpc.services.HealthStatusManager;

@Internal
public class NewtServices {
  private final Config config;
  private ServiceLifecycle serviceLifecycle = null;
  private DiscoveryMechanism discoveryMechanism = null;
  private HealthStatusManager healthStatusManager = null;

  public NewtServices(Config config) {
    this.config = config;
  }

  public Config getConfig() {
    return config;
  }

  public ServiceLifecycle getServiceLifecycle() {
    if (serviceLifecycle != null) {
      return serviceLifecycle;
    }
    return new ServiceLifecycleImpl(getHealthStatusManager(), getDiscoveryMechanism());
  }

  public void setServiceLifecycle(ServiceLifecycle serviceLifecycle) {
    this.serviceLifecycle = serviceLifecycle;
  }

  public DiscoveryMechanism getDiscoveryMechanism() {
    if (discoveryMechanism != null) {
      return discoveryMechanism;
    }
    switch (config.getStringValue("discovery")) {
      case "consul":
        discoveryMechanism = new ConsulDiscoveryMechanism(config);
      default:
        throw new IllegalArgumentException("Unrecognized discovery key.");
    }
  }

  public void setDiscoveryMechanism(DiscoveryMechanism discoveryMechanism) {
    this.discoveryMechanism = discoveryMechanism;
  }

  public HealthStatusManager getHealthStatusManager() {
    if (healthStatusManager != null) {
      return healthStatusManager;
    }
    return new HealthStatusManager();
  }

  public void setHealthStatusManager(HealthStatusManager healthStatusManager) {
    this.healthStatusManager = healthStatusManager;
  }
}

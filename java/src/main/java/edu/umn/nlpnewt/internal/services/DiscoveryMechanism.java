package edu.umn.nlpnewt.internal.services;

import io.grpc.NameResolver;

public interface DiscoveryMechanism {
  String getServiceTarget(String serviceName, String... tags);

  default String getServiceTarget(String serviceName) {
    return getServiceTarget(serviceName, (String[]) null);
  }

  void register(ServiceInfo serviceInfo);

  void deregister(ServiceInfo serviceInfo);

  NameResolver.Factory getNameResolverFactory();
}

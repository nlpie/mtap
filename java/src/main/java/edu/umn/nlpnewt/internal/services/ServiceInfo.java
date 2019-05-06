package edu.umn.nlpnewt.internal.services;

import java.util.List;

public final class ServiceInfo {
  private final String name;
  private final String identifier;
  private final String address;
  private final int port;
  private final List<String> tags;
  private final boolean register;

  public ServiceInfo(
      String name,
      String identifier,
      String address,
      int port,
      List<String> tags,
      boolean register
  ) {
    this.name = name;
    this.identifier = identifier;
    this.address = address;
    this.port = port;
    this.tags = tags;
    this.register = register;
  }

  public String getName() {
    return name;
  }

  public String getIdentifier() {
    return identifier;
  }

  public String getAddress() {
    return address;
  }

  public int getPort() {
    return port;
  }

  public List<String> getTags() {
    return tags;
  }

  public boolean isRegister() {
    return register;
  }
}

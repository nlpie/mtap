package edu.umn.nlpie.mtap.processing;

import edu.umn.nlpie.mtap.common.Config;
import edu.umn.nlpie.mtap.model.ChannelFactory;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.concurrent.TimeUnit;

public class StandardChannelFactory implements ChannelFactory {
  private static final Logger LOGGER = LoggerFactory.getLogger(StandardChannelFactory.class);

  private final Config config;

  public StandardChannelFactory(Config config) {
    this.config = config;
  }

  @Override
  public ManagedChannel createChannel(String address) {
    LOGGER.debug("Creating channel with address: {}", address);
    ManagedChannel eventsChannel;
    if (address == null || !(address instanceof String) || address.length() == 0) {
      throw new IllegalArgumentException("Address must be nonnull, nonempty String.");
    }
    ManagedChannelBuilder<?> builder = ManagedChannelBuilder.forTarget(address);
    Integer maxInboundMessageSize = config.getIntegerValue("grpc.events_options.grpc.max_receive_message_length");
    if (maxInboundMessageSize != null) {
      builder.maxInboundMessageSize(maxInboundMessageSize);
    }
    Integer keepAliveTime = config.getIntegerValue("grpc.events_options.grpc.keepalive_time_ms");
    if (keepAliveTime != null) {
      builder.keepAliveTime(keepAliveTime, TimeUnit.MILLISECONDS);
    }
    Integer keepAliveTimeout = config.getIntegerValue("grpc.events_options.grpc.keepalive_timeout_ms");
    if (keepAliveTimeout != null) {
      builder.keepAliveTimeout(keepAliveTimeout, TimeUnit.MILLISECONDS);
    }
    Boolean permitKeepAliveWithoutCalls = config.getBooleanValue("grpc.events_options.grpc.permit_keepalive_without_calls");
    if (permitKeepAliveWithoutCalls != null) {
      builder.keepAliveWithoutCalls(permitKeepAliveWithoutCalls);
    }
    eventsChannel = builder.usePlaintext().build();
    return eventsChannel;
  }
}

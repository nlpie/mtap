package edu.umn.nlpnewt.processing;

import com.google.common.base.Stopwatch;
import edu.umn.nlpnewt.ProcessorContext;
import edu.umn.nlpnewt.Timer;
import edu.umn.nlpnewt.services.ServiceLifecycle;
import io.grpc.health.v1.HealthCheckResponse;
import org.jetbrains.annotations.NotNull;

import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

class ContextManagerImpl implements ContextManager {
  private final ServiceLifecycle serviceLifecycle;
  private final ThreadLocal<ProcessorThreadContext> threadContext = new ThreadLocal<>();
  private final String identifier;
  private final ProcessorContext context = new Context();

  public ContextManagerImpl(ServiceLifecycle serviceLifecycle, String identifier) {
    this.serviceLifecycle = serviceLifecycle;
    this.identifier = identifier;
  }

  public ServiceLifecycle getServiceLifecycle() {
    return serviceLifecycle;
  }

  public String getIdentifier() {
    return identifier;
  }

  @Override
  public ProcessorContext enterContext() {
    ProcessorThreadContext processorThreadContext = new ProcessorThreadContext();
    threadContext.set(processorThreadContext);
    return processorThreadContext;
  }

  @Override
  public ProcessorContext getContext() {
    return context;
  }

  public ProcessorContext getCurrent() {
    ProcessorThreadContext local = threadContext.get();
    if (local == null) {
      throw new IllegalStateException("Attempting to use processor context outside of a " +
          "managed process call.");
    }
    return local;
  }

  private class Context implements ProcessorContext {
    @Override
    public void updateServingStatus(HealthCheckResponse.ServingStatus status) {
      if (serviceLifecycle != null) {
        serviceLifecycle.setStatus(identifier, status);
      }
    }

    @Override
    public @NotNull Timer startTimer(String key) {
      return getCurrent().startTimer(key);
    }

    @Override
    public Map<String, Duration> getTimes() {
      return getCurrent().getTimes();
    }

    @Override
    public void close() { }
  }

  private class ProcessorThreadContext extends Context {
    private final Map<String, Duration> times = new HashMap<>();

    private boolean active = true;

    @Override
    public void updateServingStatus(HealthCheckResponse.ServingStatus status) {
      if (serviceLifecycle != null) {
        serviceLifecycle.setStatus(identifier, status);
      }
    }

    @Override
    public @NotNull Timer startTimer(String key) {
      Stopwatch stopwatch = Stopwatch.createStarted();

      return new Timer() {
        @Override
        public void stop() {
          if (!active) {
            throw new IllegalStateException("Processor context has been exited prior to stop.");
          }
          times.put(identifier + ":" + key, stopwatch.elapsed());
        }

        @Override
        public void close() {
          stop();
        }
      };
    }

    @Override
    public Map<String, Duration> getTimes() {
      return times;
    }

    @Override
    public void close() {
      active = false;
      threadContext.remove();
    }
  }
}

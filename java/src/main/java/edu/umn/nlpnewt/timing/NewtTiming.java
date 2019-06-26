package edu.umn.nlpnewt.timing;

import java.util.concurrent.ExecutorService;

public class NewtTiming {

  private TimesCollector timesCollector = null;

  public TimesCollector getTimesCollector(ExecutorService executorService) {
    if (timesCollector == null) {
      timesCollector = new TimesCollectorImpl(executorService);
    }
    return timesCollector;
  }

  public NewtTiming setTimesCollector(TimesCollector timesCollector) {
    this.timesCollector = timesCollector;
    return this;
  }
}

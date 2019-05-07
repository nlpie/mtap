package edu.umn.nlpnewt.internal.processing;

import edu.umn.nlpnewt.ProcessorContext;

public interface ContextManager {
  ProcessorContext enterContext();

  ProcessorContext getContext();
}

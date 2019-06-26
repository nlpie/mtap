package edu.umn.nlpnewt.processing;

import edu.umn.nlpnewt.ProcessorContext;

public interface ContextManager {
  ProcessorContext enterContext();

  ProcessorContext getContext();
}

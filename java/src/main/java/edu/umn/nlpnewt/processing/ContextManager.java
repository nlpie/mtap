package edu.umn.nlpnewt.processing;

public interface ContextManager {
  ProcessorContext enterContext();

  ProcessorContext getContext();
}

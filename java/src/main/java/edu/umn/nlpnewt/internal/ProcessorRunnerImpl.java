/*
 * Copyright 2019 Regents of the University of Minnesota.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package edu.umn.nlpnewt.internal;

import edu.umn.nlpnewt.*;
import edu.umn.nlpnewt.ProcessorContextManager.ProcessorThreadContext;

import java.io.IOException;

class ProcessorRunnerImpl implements ProcessorRunner {

  private final ProcessorContextManager processorContextManager;
  private final EventProcessor processor;
  private final NewtEvents events;
  private final String name;
  private final String identifier;

  ProcessorRunnerImpl(
      EventProcessor processor,
      ProcessorContextManager processorContextManager,
      NewtEvents events,
      String name,
      String identifier
  ) {
    this.processor = processor;
    this.processorContextManager = processorContextManager;
    this.events = events;
    this.name = name;
    this.identifier = identifier;
  }

  @Override
  public ProcessingResult process(String eventID, JsonObject params) throws IOException {
    JsonObject.Builder resultBuilder = JsonObject.newBuilder();
    try (ProcessorThreadContext context = processorContextManager.enterContext()) {
      try (Event event = events.openEvent(eventID)) {
        Timer timer = context.startTimer("process_method");
        processor.process(event, params, resultBuilder);
        timer.stop();
        return new ProcessingResult(event.getCreatedIndices(), context.getTimes(),
            resultBuilder.build());
      }
    }
  }

  @Override
  public String getProcessorName() {
    return name;
  }

  @Override
  public String getProcessorId() {
    return identifier;
  }

  @Override
  public void close() {
    processor.shutdown();
  }
}

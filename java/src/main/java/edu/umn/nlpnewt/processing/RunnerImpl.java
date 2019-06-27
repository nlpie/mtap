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

package edu.umn.nlpnewt.processing;

import edu.umn.nlpnewt.*;

@Internal
class RunnerImpl implements Runner {
  private final EventsClient client;
  private final EventProcessor processor;
  private final ContextManager contextManager;
  private final String processorName;
  private final String processorId;

  RunnerImpl(
      EventProcessor processor,
      EventsClient client,
      ContextManager contextManager,
      String processorName,
      String processorId
  ) {
    this.processor = processor;
    this.client = client;
    this.contextManager = contextManager;
    this.processorName = processorName;
    this.processorId = processorId;
  }

  @Override
  public ProcessingResult process(String eventID, JsonObject params) {
    try (ProcessorContext context = contextManager.enterContext()) {
      try (Event event = Event.open(client, eventID)) {
        JsonObjectBuilder resultBuilder = JsonObjectImpl.newBuilder();
        Timer timer = context.startTimer("process_method");
        processor.process(event, params, resultBuilder);
        timer.stop();
        return new ProcessingResult(
            event.getCreatedIndices(),
            context.getTimes(),
            resultBuilder.build()
        );
      }
    }
  }

  EventProcessor getProcessor() {
    return processor;
  }

  ContextManager getContextManager() {
    return contextManager;
  }

  @Override
  public String getProcessorName() {
    return processorName;
  }

  @Override
  public String getProcessorId() {
    return processorId;
  }

  @Override
  public void close() {
    processor.shutdown();
  }

}

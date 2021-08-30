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

package edu.umn.nlpie.mtap.processing;

import edu.umn.nlpie.mtap.Internal;
import edu.umn.nlpie.mtap.common.JsonObject;
import edu.umn.nlpie.mtap.common.JsonObjectBuilder;
import edu.umn.nlpie.mtap.common.JsonObjectImpl;
import edu.umn.nlpie.mtap.model.Event;
import edu.umn.nlpie.mtap.model.EventsClientPool;
import org.jetbrains.annotations.NotNull;

import java.util.Map;

@Internal
class LocalProcessorRunner implements ProcessorRunner {
  private final EventsClientPool clientPool;
  private final EventProcessor processor;
  private final Map<String, Object> processorMeta;

  LocalProcessorRunner(
      EventsClientPool clientPool,
      EventProcessor processor
  ) {
    this.clientPool = clientPool;
    this.processor = processor;

    processorMeta = processor.getProcessorMetadata();
  }

  @Override
  public ProcessingResult process(
      @NotNull String eventID,
      @NotNull String eventInstanceID,
      @NotNull JsonObject params
  ) {
    try (ProcessorContext context = ProcessorBase.enterContext();
         Event event = Event.newBuilder().eventID(eventID).eventInstanceID(eventInstanceID).clientPool(clientPool)
             .defaultAdapters(processor.getDefaultAdapters()).build()
    ) {
      JsonObjectBuilder<?, ?> resultBuilder = JsonObjectImpl.newBuilder();
      Stopwatch stopwatch = ProcessorBase.startedStopwatch("process_method");
      processor.process(event, params, resultBuilder);
      stopwatch.stop();
      return new ProcessingResult(
          event.getCreatedIndices(),
          context.getTimes(),
          resultBuilder.build()
      );
    }
  }

  @Override
  public Map<String, Object> getProcessorMeta() {
    return processorMeta;
  }

  @Override
  public EventProcessor getProcessor() {
    return processor;
  }

  @Override
  public void close() throws InterruptedException {
    clientPool.close();
    processor.shutdown();
  }
}

/*
 * Copyright 2019 Regents of the University of Minnesota
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
package edu.umn.nlpnewt;

import edu.umn.nlpnewt.model.EventsClientBuilder;
import edu.umn.nlpnewt.processing.EventProcessor;
import edu.umn.nlpnewt.processing.ProcessorServerBuilder;
import edu.umn.nlpnewt.processing.ProcessorServerOptions;

/**
 * The main class and entry points for the NLP-NEWT framework.
 * <p>
 * This object provides methods for interacting with a newt events service and for launching newt
 * processors written in Java.
 */
public final class Newt {
  /**
   * The name used by the events service for discovery.
   */
  public static final String EVENTS_SERVICE_NAME = "nlpnewt-events";

  /**
   * The name used by the processor services for discovery.
   */
  public static final String PROCESSOR_SERVICE_TAG = "v1-nlpnewt-processor";

  public static EventsClientBuilder eventsClientBuilder() {
    return EventsClientBuilder.newBuilder();
  }

  public static ProcessorServerBuilder processorServerBuilder(EventProcessor eventProcessor,
                                                              ProcessorServerOptions options) {
    return ProcessorServerBuilder.forProcessor(eventProcessor, options);
  }
}

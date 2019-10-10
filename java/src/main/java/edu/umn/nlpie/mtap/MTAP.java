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
package edu.umn.nlpie.mtap;

import edu.umn.nlpie.mtap.model.EventsClient;
import edu.umn.nlpie.mtap.model.EventsClientBuilder;
import edu.umn.nlpie.mtap.processing.ProcessorServer;
import edu.umn.nlpie.mtap.model.EventBuilder;
import edu.umn.nlpie.mtap.model.GenericLabel;
import edu.umn.nlpie.mtap.processing.EventProcessor;
import edu.umn.nlpie.mtap.processing.ProcessorServerBuilder;
import edu.umn.nlpie.mtap.processing.ProcessorServerOptions;
import org.jetbrains.annotations.NotNull;

/**
 * The main class and entry points for the MTAP framework.
 * <p>
 * This object provides methods for interacting with a MTAP events service and for launching MTAP
 * processors written in Java.
 */
public final class MTAP {
  /**
   * The name used by the events service for discovery.
   */
  public static final String EVENTS_SERVICE_NAME = "mtap-events";

  /**
   * The name used by the processor services for discovery.
   */
  public static final String PROCESSOR_SERVICE_TAG = "v1-mtap-processor";

  /**
   * A builder for events clients.
   *
   * @return A builder that can be used to configure the events client.
   *
   * @see EventsClient
   */
  public static @NotNull EventsClientBuilder eventsClientBuilder() {
    return EventsClientBuilder.newBuilder();
  }

  /**
   * A builder for a processor server.
   *
   * @param eventProcessor The processor to host.
   * @param options        The basic / command line options for the processing server.
   *
   * @return A builder object.
   *
   * @see ProcessorServer
   */
  public static @NotNull ProcessorServerBuilder processorServerBuilder(
      EventProcessor eventProcessor,
      ProcessorServerOptions options
  ) {
    return ProcessorServerBuilder.forProcessor(eventProcessor, options);
  }

  /**
   * A builder for event objects.
   *
   * @return A new builder that can be used to create events.
   */
  public static @NotNull EventBuilder eventBuilder() {
    return EventBuilder.newBuilder();
  }

  /**
   * A builder for generic labels.
   *
   * @param startIndex The start index of the label.
   * @param endIndex   The end index of the label.
   *
   * @return Builder for labels.
   */
  public static @NotNull GenericLabel.Builder genericLabelBuilder(int startIndex, int endIndex) {
    return GenericLabel.withSpan(startIndex, endIndex);
  }
}

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

package edu.umn.nlpie.mtap.model;

import edu.umn.nlpie.mtap.exc.EventExistsException;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.Collections;
import java.util.Map;
import java.util.UUID;

/**
 * A builder for events, whether they are local objects, or distributed objects shared via an
 * events service.
 * <p>
 * The {@link #getEventsClient()} property controls whether the object will be local or
 * distributed. If it is not set / {@code null}, the object will be local, if it is set, the object
 * will be shared with the events service.
 */
public class EventBuilder {
  private @Nullable String eventID = null;
  private @Nullable EventsClient eventsClient = null;
  private boolean onlyCreateNew = false;
  private Map<String, ProtoLabelAdapter<?>> defaultAdapters;

  public static @NotNull EventBuilder newBuilder() {
    return new EventBuilder();
  }

  /**
   * Gets the unique event identifier, using a random UUID string if the event id has not been set.
   *
   * @return The unique event identifier that will be used for the created event.
   */
  public @NotNull String getEventID() {
    if (eventID == null) {
      eventID = UUID.randomUUID().toString();
    }
    return eventID;
  }

  /**
   * Sets the unique event identifier.
   *
   * @param eventID The unique event identifier that will be used for the created event.
   */
  public void setEventID(@NotNull String eventID) {
    this.eventID = eventID;
  }

  /**
   * Sets the unique event identifier.
   *
   * @param eventID The unique event identifier that will be used for the created event.
   *
   * @return this builder.
   */
  public @NotNull EventBuilder withEventID(@NotNull String eventID) {
    this.eventID = eventID;
    return this;
  }

  /**
   * The events client that will be used to connect to an events service and share data added to
   * the event with other services and processors. If it is not set, the
   *
   * @return The events client or {@code null} if it has not been set.
   */
  public @Nullable EventsClient getEventsClient() {
    return eventsClient;
  }

  /**
   * The events client that will be used to connect to an events service and share data added to
   * the event with other services and processors.
   *
   * @param eventsClient Events client object.
   */
  public void setEventsClient(@Nullable EventsClient eventsClient) {
    this.eventsClient = eventsClient;
  }

  /**
   * The events client that will be used to connect to an events service and share data added to
   * the event with other services and processors.
   *
   * @param eventsClient Events client object.
   *
   * @return This builder.
   */
  public @NotNull EventBuilder withEventsClient(@Nullable EventsClient eventsClient) {
    this.eventsClient = eventsClient;
    return this;
  }

  /**
   * If the events client is set, this controls whether the builder will fail if the event already
   * exists.
   *
   * @return Boolean indicator of whether it should fail, {@code true} causes failure if an event
   * already exists with the same identifier.
   */
  public boolean isOnlyCreateNew() {
    return onlyCreateNew;
  }

  /**
   * If the events client is set, this controls whether the builder will fail if the event already
   * exists.
   *
   * @param onlyCreateNew Boolean indicator of whether it should fail, {@code true} causes failure
   *                      if an event already exists with the same identifier.
   */
  public void setOnlyCreateNew(boolean onlyCreateNew) {
    this.onlyCreateNew = onlyCreateNew;
  }


  /**
   * Sets the only create new flag, causing failure if an event already exists with the identifier.
   *
   * @return this builder.
   */
  public @NotNull EventBuilder onlyCreateNew() {
    this.onlyCreateNew = true;
    return this;
  }

  /**
   * Sets a map of label index names to default adapters, that will be used by any documents on
   * this event.
   *
   * @param defaultAdapters a map from strings to proto label adapters.
   */
  public void setDefaultAdapters(Map<String, ProtoLabelAdapter<?>> defaultAdapters) {
    this.defaultAdapters = defaultAdapters;
  }

  /**
   * Builder method which sets a map of label index names to default adapters, that will be used by
   * any documents on this event.
   *
   * @param defaultAdapters a map from strings to proto label adapters.
   * @return this builder.
   */
  public @NotNull EventBuilder withDefaultAdapters(
      Map<String, ProtoLabelAdapter<?>> defaultAdapters
  ) {
    this.defaultAdapters = defaultAdapters;
    return this;
  }

  /**
   * Creates a new event.
   *
   * @return The event object.
   * @throws EventExistsException if the event already exists on the events
   *                                                  service and only create new is set.
   */
  public @NotNull Event build() {
    String eventID = getEventID();
    if (eventsClient != null) {
      eventsClient.openEvent(eventID, onlyCreateNew);
    }
    Map<String, ProtoLabelAdapter<?>> defaultAdapters = this.defaultAdapters;
    if (defaultAdapters == null) {
      defaultAdapters = Collections.emptyMap();
    }
    return new Event(eventID, eventsClient, defaultAdapters);
  }
}

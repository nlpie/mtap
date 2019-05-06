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
package edu.umn.nlpnewt.internal.events;

import edu.umn.nlpnewt.*;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.UUID;

@Internal
final class EventsImpl implements Events {

  private final EventsClient eventsClient;

  public EventsImpl(EventsClient eventsClient) {
    this.eventsClient = eventsClient;
  }

  @Override
  @NotNull
  public Event openEvent(@Nullable String eventID) {
    return openEvent(eventID, false);
  }

  @Override
  @NotNull
  public Event createEvent(@Nullable String eventID) {
    return openEvent(eventID, true);
  }

  @NotNull
  private Event openEvent(@Nullable String eventID, boolean onlyCreateNew) {
    if (eventID == null) {
      eventID = UUID.randomUUID().toString();
    }
    eventsClient.openEvent(eventID, onlyCreateNew);
    return new EventImpl(eventsClient, eventID);
  }

  @Override
  public void close() {
    eventsClient.close();
  }
}

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

import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.io.Closeable;

/**
 * A client to an events service.
 * <p>
 * Usage:
 * <pre>
 *   {@code
 *   try (Events events = newt.events("localhost:9090")) {
 *     // interact with events service.
 *   }
 *   }
 * </pre>
 * <p>
 * Implements {@link Closeable} and will close the connection to the events service when closed.
 */
public interface Events extends Closeable {

  /**
   * Opens a new event with a random identifier.
   *
   * @return An object that can be used to interact with the created Event.
   */
  @NotNull Event createEvent();

  /**
   * Opens the event, creating it if it does not already exist.
   *
   * @param eventID The string unique event identifier.
   *
   * @return An object that can be used to interact with the Event.
   */
  @NotNull Event openEvent(@NotNull String eventID);

  /**
   * Opens the event, creating it or failing if it already exists.
   *
   * @param eventID The string unique event identifier.
   *
   * @return An object that can be used to interact with the Event.
   */
  @NotNull Event createEvent(@NotNull String eventID);
}

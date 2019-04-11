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

import java.io.Closeable;
import java.util.List;
import java.util.Map;

/**
 * A client to access the data stored on a specific event on the events service.
 * <p>
 * The Event object functions as a map from string document names to {@link Document} objects that
 * can be used to access document data from the events server.
 * <p>
 * This is a closeable object because the events service keeps reference counts of the number of
 * clients actively using an event. When the event is closed, the reference count is decremented,
 * and if the reference count hits 0 the events service will deallocate the event.
 */
public interface Event extends Map<@NotNull String, @NotNull Document>, Closeable {
  /**
   * Returns the unique identifier for the event.
   *
   * @return The string unique event identifier.
   */
  @NotNull String getEventID();

  /**
   * Returns the metadata associated with the event. Metadata is contextual information relevant to
   * the event for example, source file names, timestamps, database entries that are .
   *
   * @return A map view of the metadata
   */
  @NotNull Map<@NotNull String, @NotNull String> getMetadata();

  /**
   * Adds a document keyed by {@code documentName} and containing {@code text}.
   *
   * @param documentName The key to store the document under.
   * @param text The text of the document.
   * @return A document object that can be used to interact with the documents service.
   */
  @NotNull Document addDocument(@NotNull String documentName, @NotNull String text);

  /**
   * Returns the indices that have been created on all documents on this event.
   *
   * @return A map of document names to a list of documents that have been created on that index.
   */
  @NotNull Map<@NotNull String, @NotNull List<@NotNull String>> getCreatedIndices();
}

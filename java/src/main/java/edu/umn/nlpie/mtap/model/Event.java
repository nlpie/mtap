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

import com.google.common.collect.AbstractIterator;
import edu.umn.nlpie.mtap.exc.EventExistsException;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.*;

/**
 * A processing event, containing related documents, binaries, and associated metadata. Akin to a
 * record.
 * <p>
 * The Event object functions as a map from string document names to {@link Document} objects that
 * can be used to access document data from the events server.
 * <p>
 * This is a closeable object because the events service keeps reference counts of the number of
 * clients actively using an event. When the event is closed, the reference count is decremented,
 * and if the reference count hits 0 the events service will deallocate the event. If event is not
 * local and the events client is {@code null} / not set, the close method is a no-op and does not
 * need to be called.
 *
 * @see Builder
 */
public class Event implements AutoCloseable {
  private final String eventID;

  @Nullable
  private final EventsClient client;
  private final Map<String, ProtoLabelAdapter<?>> defaultAdapters;

  private Metadata metadata = null;
  private BinaryData binaryData = null;
  private Documents documents = null;


  Event(@NotNull String eventID,
        @Nullable EventsClient client,
        Map<String, ProtoLabelAdapter<?>> defaultAdapters) {
    this.eventID = eventID;
    this.client = client;
    this.defaultAdapters = defaultAdapters;
  }

  /**
   * Creates a new builder for an event.
   *
   * @return Builder object for an event.
   */
  public static Builder newBuilder() {
    return new Builder();
  }

  /**
   * Returns the events client (if set).
   *
   * @return Events client or {@code null} if it is not set.
   */
  public @Nullable EventsClient getClient() {
    return client;
  }

  /**
   * Returns the unique identifier for the event.
   *
   * @return The string unique event identifier.
   */
  public @NotNull String getEventID() {
    return eventID;
  }

  /**
   * Returns the metadata associated with the event. Metadata is contextual information relevant to
   * the event for example, source file names, timestamps, database entries that are .
   *
   * @return A map view of the metadata
   */
  public @NotNull Map<@NotNull String, @NotNull String> getMetadata() {
    if (metadata == null) {
      metadata = new Metadata();
    }
    return metadata;
  }

  /**
   * Returns a map used to manipulate and retrieve the binary data stored with the event.
   *
   * @return A map view of the binary data on the event.
   */
  public @NotNull Map<@NotNull String, byte[]> getBinaryData() {
    if (binaryData == null) {
      binaryData = new BinaryData();
    }
    return binaryData;
  }

  /**
   * Returns a map used to manipulate and retrieve the documents stored on this event.
   *
   * @return A map view of document names to documents.
   */
  public @NotNull Map<@NotNull String, @NotNull Document> getDocuments() {
    if (documents == null) {
      documents = new Documents();
    }
    return documents;
  }

  /**
   * Adds a new document keyed by {@code documentName} and containing {@code text}.
   *
   * @param documentName The key to store the document under.
   * @param text         The text of the document.
   *
   * @return A document object that can be used to interact with the documents service.
   */
  public @NotNull Document createDocument(@NotNull String documentName, @NotNull String text) {
    Document document = new Document(documentName, text);
    getDocuments().put(documentName, document);
    return document;
  }

  /**
   * Returns the indices that have been created on all documents on this event.
   *
   * @return A map of document names to a list of documents that have been created on that index.
   */
  public @NotNull Map<@NotNull String, List<@NotNull String>> getCreatedIndices() {
    HashMap<String, List<String>> createdIndices = new HashMap<>();
    for (Document document : getDocuments().values()) {
      createdIndices.put(document.getName(), document.getCreatedIndices());
    }
    return createdIndices;
  }

  /**
   * Returns an unmodifiable map from index name to default adapters
   *
   * @return a view of the default adapters map.
   */
  public @NotNull Map<String, ProtoLabelAdapter<?>> getDefaultAdapters() {
    return Collections.unmodifiableMap(defaultAdapters);
  }

  @Override
  public void close() {
    if (client != null) {
      client.closeEvent(eventID);
    }
  }


  private class Metadata extends AbstractMap<String, String> {
    private final Map<String, String> metadata = new HashMap<>();

    private Metadata() {
      if (client != null) {
        metadata.putAll(client.getAllMetadata(eventID));
      }
    }

    @Override
    public String get(Object key) {
      String s = metadata.get(key);
      if (s == null) {
        refreshMetadata();
        s = metadata.get(key);
      }
      return s;
    }

    @Override
    public String put(String key, String value) {
      metadata.put(key, value);
      if (client != null) {
        client.addMetadata(eventID, key, value);
      }
      return null;
    }

    @Override
    public boolean containsKey(Object key) {
      boolean contains = metadata.containsKey(key);
      if (!contains) {
        refreshMetadata();
        contains = metadata.containsKey(key);
      }
      return contains;
    }

    @Override
    public @NotNull Set<Entry<String, String>> entrySet() {
      refreshMetadata();
      return metadata.entrySet();
    }

    private void refreshMetadata() {
      if (client != null) {

        metadata.putAll(client.getAllMetadata(eventID));
      }
    }
  }

  private class BinaryData extends AbstractMap<String, byte[]> {
    private final Map<String, byte[]> binaryData = new HashMap<>();

    @Override
    public byte[] get(Object key) {
      if (!(key instanceof String)) {
        return null;
      }
      byte[] bytes = binaryData.get(key);
      if (bytes == null && client != null) {
        bytes = client.getBinaryData(eventID, (String) key);
        binaryData.put((String) key, bytes);
      }
      return bytes;
    }

    @Override
    public byte[] put(String key, byte[] value) {
      binaryData.put(key, value);
      if (client != null) {
        client.addBinaryData(eventID, key, value);
      }
      return null;
    }

    @Override
    public boolean containsKey(Object key) {
      if (!(key instanceof String)) {
        return false;
      }
      if (binaryData.containsKey(key)) {
        return true;
      }
      if (client != null) {
        Collection<String> names = client.getAllBinaryDataNames(eventID);
        return names.contains(key);
      }
      return false;
    }

    @Override
    public @NotNull Set<Entry<String, byte[]>> entrySet() {
      if (client != null) {
        Collection<String> names = client.getAllBinaryDataNames(eventID);
        for (String name : names) {
          byte[] bytes = client.getBinaryData(eventID, name);
          binaryData.put(name, bytes);
        }
      }
      return binaryData.entrySet();
    }
  }

  private class Documents extends AbstractMap<@NotNull String, @NotNull Document> {
    private final List<Document> documents = new ArrayList<>();
    private EntrySet entries = null;

    @Override
    public Document put(String key, Document document) {
      if (document == null) {
        throw new IllegalArgumentException("Document cannot be null.");
      }
      if (document.getEvent() != null) {
        throw new IllegalArgumentException(
            "Document '" + document.getName() + "' is already on event: " + document.getEvent().getEventID()
        );
      }

      refreshDocuments();
      for (Document d : documents) {
        if (d.getName().equals(document.getName())) {
          throw new IllegalArgumentException("Already has document with name");
        }
      }

      if (client != null) {
        client.addDocument(eventID, document.getName(), document.getText());
      }
      document.setEvent(Event.this);
      documents.add(document);
      return null;
    }

    @Override
    public int size() {
      return documents.size();
    }

    @Override
    public Document get(Object key) {
      if (!(key instanceof String)) {
        return null;
      }
      Document document = null;
      for (Document d : documents) {
        if (d.getName().equals(key)) {
          document = d;
        }
      }
      if (document != null) {
        return document;
      }
      refreshDocuments();
      for (Document d : documents) {
        if (d.getName().equals(key)) {
          document = d;
        }
      }
      return document;
    }

    @Override
    public @NotNull Set<Entry<String, Document>> entrySet() {
      if (entries == null) {
        entries = new EntrySet();
      }
      refreshDocuments();
      return entries;
    }

    private void refreshDocuments() {
      if (client != null) {
        Collection<String> allDocuments = client.getAllDocumentNames(eventID);
        DOCUMENT_NAMES:
        for (String documentName : allDocuments) {
          for (Document document : documents) {
            if (document.getName().equals(documentName)) {
              continue DOCUMENT_NAMES;
            }
          }
          Document document = new Document(documentName);
          document.setEvent(Event.this);
          documents.add(document);
        }
      }
    }

    private class EntrySet extends AbstractSet<Map.Entry<String, Document>> {
      @Override
      public @NotNull Iterator<Map.Entry<String, Document>> iterator() {
        Iterator<Document> it = documents.iterator();
        return new AbstractIterator<Map.Entry<String, Document>>() {
          @Override
          protected Map.Entry<String, Document> computeNext() {
            if (!it.hasNext()) {
              endOfData();
              return null;
            }
            Document document = it.next();
            String documentName = document.getName();
            return new AbstractMap.SimpleEntry<>(documentName, document);
          }
        };
      }

      @Override
      public int size() {
        return Documents.this.size();
      }
    }
  }

  /**
   * A builder for events, whether they are local objects, or distributed objects shared via an
   * events service.
   * <p>
   * The {@link #getEventsClient()} property controls whether the object will be local or
   * distributed. If it is not set / {@code null}, the object will be local, if it is set, the object
   * will be shared with the events service.
   */
  public static class Builder {
    private @Nullable String eventID = null;
    private @Nullable EventsClient eventsClient = null;
    private boolean onlyCreateNew = false;
    private Map<String, ProtoLabelAdapter<?>> defaultAdapters;

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
    public @NotNull Event.Builder eventID(@NotNull String eventID) {
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
    public @NotNull Event.Builder eventsClient(@Nullable EventsClient eventsClient) {
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
     * If the events client is set, this controls whether the builder will fail if the event already
     * exists.
     *
     * @param onlyCreateNew only create new flag.
     * @return this builder.
     */
    public @NotNull Event.Builder onlyCreateNew(boolean onlyCreateNew) {
      this.onlyCreateNew = onlyCreateNew;
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
    public @NotNull Event.Builder defaultAdapters(
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
}

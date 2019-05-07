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

import com.google.common.collect.AbstractIterator;
import edu.umn.nlpnewt.Document;
import edu.umn.nlpnewt.Event;
import edu.umn.nlpnewt.Events;
import edu.umn.nlpnewt.Internal;
import org.jetbrains.annotations.NotNull;

import javax.print.Doc;
import javax.swing.event.DocumentEvent;
import java.util.*;

@Internal
final class EventImpl extends AbstractMap<@NotNull String, @NotNull Document> implements Event {

  private final EventsClient client;

  private final String eventID;
  private final DocumentFactory documentFactory;

  private transient List<Document> documents = null;
  private transient Metadata metadata = null;
  private transient EntrySet entrySet = null;

  EventImpl(EventsClient client, String eventID, DocumentFactory documentFactory) {
    this.client = client;
    this.eventID = eventID;
    this.documentFactory = documentFactory;
  }

  @Override
  public @NotNull String getEventID() {
    return eventID;
  }

  @Override
  public @NotNull Map<@NotNull String, @NotNull String> getMetadata() {
    if (metadata == null) {
      metadata = new Metadata();
    }
    return metadata;
  }

  @Override
  public @NotNull Document addDocument(@NotNull String documentName, @NotNull String text) {
    if (containsKey(documentName)) {
      throw new IllegalArgumentException("DocumentName " + documentName + " already exists on event: " + eventID);
    }

    client.addDocument(eventID, documentName, text);
    Document document = documentFactory.createDocument(client, this, documentName);
    getDocuments().add(document);
    return document;
  }

  @Override
  public boolean containsKey(Object key) {
    if (!(key instanceof String)) {
      return false;
    }
    return get(key) != null;
  }

  @Override
  public Document get(Object key) {
    for (Document document : getDocuments()) {
      if (document.getName().equals(key)) {
        return document;
      }
    }
    refreshDocuments();
    for (Document document : getDocuments()) {
      if (document.getName().equals(key)) {
        return document;
      }
    }
    return null;
  }

  @Override
  public Set<Entry<String, Document>> entrySet() {
    refreshDocuments();
    if (entrySet == null) {
      entrySet = new EntrySet();
    }
    return entrySet;
  }

  @Override
  public @NotNull Map<@NotNull String, List<@NotNull String>> getCreatedIndices() {
    HashMap<String, List<String>> createdIndices = new HashMap<>();
    for (Document document : getDocuments()) {
      createdIndices.put(document.getName(), document.getCreatedIndices());
    }
    return createdIndices;
  }

  @Override
  public void close() {
    client.closeEvent(eventID);
  }

  private List<Document> getDocuments() {
    if (documents == null) {
      documents = new ArrayList<>();
    }
    return documents;
  }

  private void refreshDocuments() {
    Collection<String> allDocuments = client.getAllDocuments(eventID);
    DOCUMENT_NAMES:
    for (String documentName : allDocuments) {
      for (Document document : getDocuments()) {
        if (document.getName().equals(documentName)) {
          continue DOCUMENT_NAMES;
        }
      }

      getDocuments().add(documentFactory.createDocument(client, this, documentName));
    }
  }

  private class Metadata extends AbstractMap<String, String> {
    private Map<String, String> metadata = client.getAllMetadata(eventID);

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
      client.addMetadata(eventID, key, value);
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
    public Set<Entry<String, String>> entrySet() {
      refreshMetadata();
      return metadata.entrySet();
    }

    private void refreshMetadata() {
      metadata = client.getAllMetadata(eventID);
    }
  }

  private class EntrySet extends AbstractSet<Entry<String, Document>> {
    @Override
    public @NotNull Iterator<Entry<String, Document>> iterator() {
      Iterator<Document> it = getDocuments().iterator();
      return new AbstractIterator<Entry<String, Document>>() {
        @Override
        protected Entry<String, Document> computeNext() {
          if (!it.hasNext()) {
            endOfData();
            return null;
          }
          Document document = it.next();
          String documentName = document.getName();
          return new SimpleEntry<>(documentName, document);
        }
      };
    }

    @Override
    public int size() {
      return getDocuments().size();
    }
  }
}

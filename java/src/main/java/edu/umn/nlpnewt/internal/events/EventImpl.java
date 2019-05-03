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
import edu.umn.nlpnewt.Internal;
import org.jetbrains.annotations.NotNull;

import java.util.*;

@Internal
final class EventImpl extends AbstractMap<@NotNull String, @NotNull Document> implements Event {

  private final EventsClient client;

  private final String eventID;

  private transient List<Document> documents;

  EventImpl(EventsClient client, String eventID) {
    this.client = client;
    this.eventID = eventID;
    this.documents = new ArrayList<>();
  }

  @Override
  public @NotNull String getEventID() {
    return eventID;
  }

  @Override
  public @NotNull Map<@NotNull String, @NotNull String> getMetadata() {
    return new AbstractMap<String, String>() {
      private Map<String, String> metadata = client.getAllMetadata(eventID);
      @Override
      public String get(Object key) {
        String s = metadata.get(key);
        if (s == null) {
          metadata = client.getAllMetadata(eventID);
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
          metadata = client.getAllMetadata(eventID);
          contains = metadata.containsKey(key);
        }
        return contains;
      }

      @Override
      public Set<Entry<String, String>> entrySet() {
        return metadata.entrySet();
      }
    };
  }


  @Override
  public @NotNull Document addDocument(@NotNull String documentName, @NotNull String text) {
    if (containsKey(documentName)) {
      throw new IllegalArgumentException("DocumentName " + documentName + " already exists on event: " + eventID);
    }

    client.addDocument(eventID, documentName, text);
    DocumentImpl document = new DocumentImpl(client, this, documentName);
    documents.add(document);
    return document;
  }

  @Override
  public @NotNull Map<@NotNull String, List<@NotNull String>> getCreatedIndices() {
    HashMap<String, List<String>> createdIndices = new HashMap<>();
    for (Document document : documents) {
      createdIndices.put(document.getName(), document.getCreatedIndices());
    }
    return createdIndices;
  }

  @Override
  public void close() {
    client.closeEvent(eventID);
  }

  @Override
  public Set<Entry<String, Document>> entrySet() {
    Collection<String> allDocuments = client.getAllDocuments(eventID);

    return new AbstractSet<Entry<String, Document>>() {
      @Override
      public @NotNull Iterator<Entry<String, Document>> iterator() {
        Iterator<String> it = allDocuments.iterator();
        return new AbstractIterator<Entry<String, Document>>() {
          @Override
          protected Entry<String, Document> computeNext() {
            if (!it.hasNext()) {
              endOfData();
              return null;
            }
            String documentName = it.next();
            return new AbstractMap.SimpleEntry<>(documentName,
                new DocumentImpl(client, EventImpl.this, documentName));
          }
        };
      }

      @Override
      public int size() {
        return allDocuments.size();
      }
    };
  }

  @Override
  public boolean containsKey(Object key) {
    if (!(key instanceof String)) {
      throw new IllegalArgumentException("Key is not of type String.");
    }
    for (Document document : documents) {
      if (document.getName().equals(key)) {
        return true;
      }
    }

    Collection<String> allDocuments = client.getAllDocuments(eventID);
    return allDocuments.contains(key);
  }

  @Override
  public Document get(Object key) {
    for (Document document : documents) {
      if (document.getName().equals(key)) {
        return document;
      }
    }
    if (containsKey(key)) {
      DocumentImpl document = new DocumentImpl(client, this, (String) key);
      documents.add(document);
      return document;
    }
    return null;
  }
}

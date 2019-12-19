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

import org.jetbrains.annotations.NotNull;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class EventTest {

  private EventsClient mockClient;
  private Event tested;

  @BeforeEach
  void setUp() {
    mockClient = mock(EventsClient.class);
    tested = EventBuilder.newBuilder().withEventID("1").withEventsClient(mockClient).build();
  }

  @Test
  void getEventID() {
    assertEquals("1", tested.getEventID());
  }

  @Test
  void metadataGet() {
    Map<String, String> metadata = new HashMap<>();
    metadata.put("foo", "bar");
    when(mockClient.getAllMetadata("1")).thenReturn(metadata);

    String s = tested.getMetadata().get("foo");
    assertEquals("bar", s);
  }

  @Test
  @SuppressWarnings("unchecked")
  void metadataRefetch() {
    Map<String, String> metadata = new HashMap<>();
    metadata.put("foo", "bar");
    when(mockClient.getAllMetadata("1")).thenReturn(Collections.emptyMap(), metadata);
    tested.getMetadata().get("foo");
    verify(mockClient, times(2)).getAllMetadata("1");
  }

  @Test
  void metadataCaches() {
    Map<String, String> metadata = new HashMap<>();
    metadata.put("foo", "bar");
    when(mockClient.getAllMetadata("1")).thenReturn(metadata);
    tested.getMetadata().get("foo");
    verify(mockClient).getAllMetadata("1");
    tested.getMetadata().get("foo");
  }

  @Test
  void metadataPut() {
    tested.getMetadata().put("foo", "bar");
    verify(mockClient).addMetadata("1", "foo", "bar");
  }

  @Test
  void metadataContains() {
    Map<String, String> metadata = new HashMap<>();
    metadata.put("foo", "bar");
    when(mockClient.getAllMetadata("1")).thenReturn(metadata);
    assertTrue(tested.getMetadata().containsKey("foo"));
  }

  @Test
  void metadataNotContains() {
    Map<String, String> metadata = new HashMap<>();
    metadata.put("foo", "bar");
    when(mockClient.getAllMetadata("1")).thenReturn(metadata);
    assertFalse(tested.getMetadata().containsKey("baz"));
  }

  @Test
  @SuppressWarnings("unchecked")
  void metadataContainsRefetch() {
    Map<String, String> metadata = new HashMap<>();
    metadata.put("foo", "bar");
    when(mockClient.getAllMetadata("1")).thenReturn(Collections.emptyMap(), metadata);
    assertTrue(tested.getMetadata().containsKey("foo"));
    verify(mockClient, times(2)).getAllMetadata("1");
  }

  @Test
  @SuppressWarnings("unchecked")
  void metadataEntrySet() {
    Map<String, String> metadata = new HashMap<>();
    metadata.put("foo", "bar");
    when(mockClient.getAllMetadata("1")).thenReturn(Collections.emptyMap(), metadata);
    Set<Map.Entry<@NotNull String, @NotNull String>> entries = tested.getMetadata().entrySet();
    verify(mockClient, times(2)).getAllMetadata("1");
    assertEquals(1, entries.size());
    Map.Entry<@NotNull String, @NotNull String> entry = entries.iterator().next();
    assertEquals("foo", entry.getKey());
    assertEquals("bar", entry.getValue());
  }

  @Test
  void addDocument() {
    Document document = tested.createDocument("plaintext", "Some text.");
    verify(mockClient).addDocument("1", "plaintext", "Some text.");
    assertEquals("plaintext", document.getName());
    assertEquals("Some text.", document.getText());
  }

  @Test
  void addDocumentCache() {
    tested.createDocument("plaintext", "Some text.");
    tested.getDocuments().get("plaintext");
    verify(mockClient).getAllDocumentNames("1");
    verify(mockClient).addDocument("1", "plaintext", "Some text.");
  }

  @Test
  void addDocumentExisting() {
    when(mockClient.getAllDocumentNames("1")).thenReturn(Collections.singletonList("plaintext"));
    assertThrows(IllegalArgumentException.class,
        () -> tested.createDocument("plaintext", "Some text."));
  }

  @Test
  void containsKeyNotString() {
    assertFalse(tested.getDocuments().containsKey(3));
  }

  @Test
  void getDocumentFetch() {
    when(mockClient.getAllDocumentNames("1")).thenReturn(Collections.singletonList("plaintext"));
    tested.getDocuments().get("plaintext");
    verify(mockClient).getAllDocumentNames("1");
  }

  @Test
  void getDocumentMissing() {
    when(mockClient.getAllDocumentNames("1")).thenReturn(Collections.emptyList());
    assertNull(tested.getDocuments().get("plaintext"));
  }

  @Test
  void emptyEntrySetIterator() {
    when(mockClient.getAllDocumentNames("1")).thenReturn(Collections.emptyList());
    for (Map.Entry<String, Document> ignored : tested.getDocuments().entrySet()) {
      fail();
    }
  }

  @Test
  void entrySet() {
    when(mockClient.getAllDocumentNames("1")).thenReturn(Collections.singletonList("plaintext"));
    Set<Map.Entry<String, Document>> entries = tested.getDocuments().entrySet();
    assertEquals(1, entries.size());
    assertEquals("plaintext", entries.iterator().next().getKey());
  }

  @Test
  void getCreatedIndices() {
    Document document = tested.createDocument("plaintext", "Some text");
    List<String> createdIndices = Arrays.asList("sentences", "pos_tags");
    document.addCreatedIndices(createdIndices);
    Map<@NotNull String, List<@NotNull String>> indices = tested.getCreatedIndices();
    assertEquals(createdIndices, indices.get("plaintext"));
  }

  @Test
  void close() {
    tested.close();
    verify(mockClient).closeEvent("1");
  }
}

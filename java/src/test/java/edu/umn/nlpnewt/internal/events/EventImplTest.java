package edu.umn.nlpnewt.internal.events;

import edu.umn.nlpnewt.Document;
import org.jetbrains.annotations.NotNull;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class EventImplTest {

  private EventsClient client;
  private EventImpl tested;
  private DocumentFactory documentFactory;
  private Document document;

  @BeforeEach
  void setUp() {
    client = mock(EventsClient.class);
    documentFactory = mock(DocumentFactory.class);
    document = mock(Document.class);
    when(documentFactory.createDocument(any(), any(), any())).thenReturn(document);
    when(document.getName()).thenReturn("plaintext");
    tested = new EventImpl(client, "1", documentFactory);
  }

  @Test
  void getEventID() {
    assertEquals("1", tested.getEventID());
  }

  @Test
  void metadataGet() {
    Map<String, String> metadata = new HashMap<>();
    metadata.put("foo", "bar");
    when(client.getAllMetadata("1")).thenReturn(metadata);

    String s = tested.getMetadata().get("foo");
    assertEquals("bar", s);
  }

  @Test
  @SuppressWarnings("unchecked")
  void metadataRefetch() {
    Map<String, String> metadata = new HashMap<>();
    metadata.put("foo", "bar");
    when(client.getAllMetadata("1")).thenReturn(Collections.emptyMap(), metadata);
    tested.getMetadata().get("foo");
    verify(client, times(2)).getAllMetadata("1");
  }

  @Test
  void metadataCaches() {
    Map<String, String> metadata = new HashMap<>();
    metadata.put("foo", "bar");
    when(client.getAllMetadata("1")).thenReturn(metadata);
    tested.getMetadata().get("foo");
    verify(client).getAllMetadata("1");
    tested.getMetadata().get("foo");
    verifyNoMoreInteractions(client);
  }

  @Test
  void metadataPut() {
    tested.getMetadata().put("foo", "bar");
    verify(client).addMetadata("1", "foo", "bar");
  }

  @Test
  void metadataContains() {
    Map<String, String> metadata = new HashMap<>();
    metadata.put("foo", "bar");
    when(client.getAllMetadata("1")).thenReturn(metadata);
    assertTrue(tested.getMetadata().containsKey("foo"));
  }

  @Test
  void metadataNotContains() {
    Map<String, String> metadata = new HashMap<>();
    metadata.put("foo", "bar");
    when(client.getAllMetadata("1")).thenReturn(metadata);
    assertFalse(tested.getMetadata().containsKey("baz"));
  }

  @Test
  @SuppressWarnings("unchecked")
  void metadataContainsRefetch() {
    Map<String, String> metadata = new HashMap<>();
    metadata.put("foo", "bar");
    when(client.getAllMetadata("1")).thenReturn(Collections.emptyMap(), metadata);
    assertTrue(tested.getMetadata().containsKey("foo"));
    verify(client, times(2)).getAllMetadata("1");
  }

  @Test
  @SuppressWarnings("unchecked")
  void metadataEntrySet() {
    Map<String, String> metadata = new HashMap<>();
    metadata.put("foo", "bar");
    when(client.getAllMetadata("1")).thenReturn(Collections.emptyMap(), metadata);
    Set<Map.Entry<@NotNull String, @NotNull String>> entries = tested.getMetadata().entrySet();
    verify(client, times(2)).getAllMetadata("1");
    assertEquals(1, entries.size());
    Map.Entry<@NotNull String, @NotNull String> entry = entries.iterator().next();
    assertEquals("foo", entry.getKey());
    assertEquals("bar", entry.getValue());
  }

  @Test
  void addDocument() {
    tested.addDocument("plaintext", "Some text.");
    verify(client).addDocument("1", "plaintext", "Some text.");
    verify(documentFactory).createDocument(client, tested, "plaintext");
  }

  @Test
  void addDocumentCache() {
    tested.addDocument("plaintext", "Some text.");
    tested.get("plaintext");
    verify(client).getAllDocumentNames("1");
    verify(client).addDocument("1", "plaintext", "Some text.");
    verify(documentFactory).createDocument(client, tested, "plaintext");
    verifyNoMoreInteractions(client);
  }

  @Test
  void addDocumentExisting() {
    when(client.getAllDocumentNames("1")).thenReturn(Collections.singletonList("plaintext"));
    assertThrows(IllegalArgumentException.class,
        () -> tested.addDocument("plaintext", "Some text."));
  }

  @Test
  void containsKeyNotString() {
    assertFalse(tested.containsKey(3));
  }

  @Test
  void getDocumentFetch() {
    when(client.getAllDocumentNames("1")).thenReturn(Collections.singletonList("plaintext"));
    tested.get("plaintext");
    verify(client).getAllDocumentNames("1");
    verify(documentFactory).createDocument(client, tested, "plaintext");
  }

  @Test
  void getDocumentMissing() {
    when(client.getAllDocumentNames("1")).thenReturn(Collections.emptyList());
    assertNull(tested.get("plaintext"));
  }

  @Test
  void emptyEntrySetIterator() {
    when(client.getAllDocumentNames("1")).thenReturn(Collections.emptyList());
    for (Map.Entry<String, Document> ignored : tested.entrySet()) {
      fail();
    }
  }

  @Test
  void entrySet() {
    when(client.getAllDocumentNames("1")).thenReturn(Collections.singletonList("plaintext"));
    Set<Map.Entry<String, Document>> entries = tested.entrySet();
    assertEquals(1, entries.size());
    assertEquals("plaintext", entries.iterator().next().getKey());
  }

  @Test
  void getCreatedIndices() {
    tested.addDocument("plaintext", "Some text");
    List<String> createdIndices = Arrays.asList("sentences", "pos_tags");
    when(document.getCreatedIndices()).thenReturn(createdIndices);
    Map<@NotNull String, List<@NotNull String>> indices = tested.getCreatedIndices();
    assertEquals(createdIndices, indices.get("plaintext"));
  }

  @Test
  void close() {
    tested.close();
    verify(client).closeEvent("1");
  }
}

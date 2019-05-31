package edu.umn.nlpnewt.internal.events;

import edu.umn.nlpnewt.*;
import org.jetbrains.annotations.NotNull;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

import java.util.Arrays;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class DocumentImplTest {

  private EventsClient eventsClient;
  private Event event;
  private ProtoLabelAdapter standardLabelAdapter;
  private ProtoLabelAdapter distinctLabelAdapter;

  private DocumentImpl tested;
  private ProtoLabelAdapter labelAdapter;
  private LabelIndex labelIndex;

  @BeforeEach
  @SuppressWarnings("unchecked")
  void setUp() {
    eventsClient = mock(EventsClient.class);
    event = mock(Event.class);
    when(event.getEventID()).thenReturn("1");
    standardLabelAdapter = mock(ProtoLabelAdapter.class);
    distinctLabelAdapter = mock(ProtoLabelAdapter.class);

    labelAdapter = mock(ProtoLabelAdapter.class);
    labelIndex = mock(LabelIndex.class);

    tested = new DocumentImpl(eventsClient, event, "plaintext", standardLabelAdapter, distinctLabelAdapter);
  }

  @Test
  void getEvent() {
assertSame(event, tested.getEvent());
  }

  @Test
  void getName() {
    assertEquals("plaintext", tested.getName());
  }

  @Test
  void getText() {
    when(eventsClient.getDocumentText("1", "plaintext")).thenReturn("Some text.");
    assertEquals("Some text.", tested.getText());
    verify(eventsClient).getDocumentText("1", "plaintext");
  }

  @Test
  void getTextCaches() {
    when(eventsClient.getDocumentText("1", "plaintext")).thenReturn("Some text.");
    tested.getText();
    verify(eventsClient).getDocumentText("1", "plaintext");
    tested.getText();
    verifyNoMoreInteractions(eventsClient);
  }

  @Test
  void getLabelIndicesInfos() {
    when(eventsClient.getLabelIndicesInfos(anyString(), anyString())).thenReturn(
        Arrays.asList(new LabelIndexInfo("foo", LabelIndexInfo.LabelIndexType.JSON),
            new LabelIndexInfo("bar", LabelIndexInfo.LabelIndexType.OTHER),
            new LabelIndexInfo("baz", LabelIndexInfo.LabelIndexType.UNKNOWN))
    );
    List<@NotNull LabelIndexInfo> infos = tested.getLabelIndicesInfo();
    verify(eventsClient).getLabelIndicesInfos("1", "plaintext");
    assertEquals(3, infos.size());
    assertEquals(new LabelIndexInfo("foo", LabelIndexInfo.LabelIndexType.JSON),
        infos.get(0));
    assertEquals(new LabelIndexInfo("bar", LabelIndexInfo.LabelIndexType.OTHER),
        infos.get(1));
    assertEquals(new LabelIndexInfo("baz", LabelIndexInfo.LabelIndexType.UNKNOWN),
        infos.get(2));
  }

  @Test
  @SuppressWarnings("unchecked")
  void getLabelIndex() {
    when(eventsClient.getLabels(anyString(), anyString(), anyString(), any())).thenReturn(labelIndex);
    assertSame(labelIndex, tested.getLabelIndex("index", labelAdapter));
    verify(eventsClient).getLabels("1", "plaintext", "index", labelAdapter);
  }

  @Test
  @SuppressWarnings("unchecked")
  void getLabelIndexCaches() {
    when(eventsClient.getLabels(anyString(), anyString(), anyString(), any())).thenReturn(labelIndex);
    tested.getLabelIndex("index", labelAdapter);
    verify(eventsClient).getLabels("1", "plaintext", "index", labelAdapter);
    tested.getLabelIndex("index", labelAdapter);
    verifyNoMoreInteractions(eventsClient);
  }

  @Test
  @SuppressWarnings("unchecked")
  void getGenericLabelIndex() {
    when(eventsClient.getLabels(anyString(), anyString(), anyString(), same(standardLabelAdapter))).thenReturn(labelIndex);
    assertSame(labelIndex, tested.getLabelIndex("index"));
    verify(eventsClient).getLabels("1", "plaintext", "index", standardLabelAdapter);
  }

  @Test
  @SuppressWarnings("unchecked")
  void getGenericLabelIndexCaches() {
    when(eventsClient.getLabels(anyString(), anyString(), anyString(), same(standardLabelAdapter))).thenReturn(labelIndex);
    tested.getLabelIndex("index");
    verify(eventsClient).getLabels("1", "plaintext", "index", standardLabelAdapter);
    tested.getLabelIndex("index");
    verifyNoMoreInteractions(eventsClient);
  }

  @Test
  @SuppressWarnings("unchecked")
  void getLabeler() {
    when(labelAdapter.createLabelIndex(anyList())).thenReturn(labelIndex);
    try (Labeler labeler = tested.getLabeler("index", labelAdapter)) {
      labeler.add(Span.of(10, 20));
      labeler.add(Span.of(0, 10));
    }
    ArgumentCaptor<List> captor = ArgumentCaptor.forClass(List.class);
    verify(eventsClient).addLabels(eq("1"), eq("plaintext"), eq("index"),
        captor.capture(), same(labelAdapter));
    List value = captor.getValue();
    assertEquals(Arrays.asList(Span.of(0, 10), Span.of(10, 20)), value);
    tested.getLabelIndex("index");
    verifyNoMoreInteractions(eventsClient);
  }

  @Test
  @SuppressWarnings("unchecked")
  void genericDistinct() {
    when(distinctLabelAdapter.createLabelIndex(anyList())).thenReturn(labelIndex);
    try (Labeler labeler = tested.getLabeler("index", true)) {
      labeler.add(Span.of(10, 20));
      labeler.add(Span.of(0, 10));
    }
    ArgumentCaptor<List> captor = ArgumentCaptor.forClass(List.class);
    verify(eventsClient).addLabels(eq("1"), eq("plaintext"), eq("index"),
        captor.capture(), same(distinctLabelAdapter));
    List value = captor.getValue();
    assertEquals(Arrays.asList(Span.of(0, 10), Span.of(10, 20)), value);
    tested.getLabelIndex("index");
    verifyNoMoreInteractions(eventsClient);
  }
}

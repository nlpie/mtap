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

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class DocumentTest {

  private EventsClient eventsClient;
  private Event event;

  private Document tested;
  private ProtoLabelAdapter<Label> labelAdapter;
  private LabelIndex<Label> labelIndex;
  private LabelIndex<GenericLabel> genericLabelIndex;

  @BeforeEach
  @SuppressWarnings("unchecked")
  void setUp() {
    eventsClient = mock(EventsClient.class);
    event = mock(Event.class);
    when(event.getClient()).thenReturn(eventsClient);
    when(event.getEventID()).thenReturn("1");

    labelAdapter = mock(ProtoLabelAdapter.class);
    labelIndex = mock(LabelIndex.class);
    genericLabelIndex = mock(LabelIndex.class);
    when(labelIndex.iterator()).thenReturn(Collections.emptyIterator());
    when(genericLabelIndex.iterator()).thenReturn(Collections.emptyIterator());

    tested = new Document("plaintext");
    tested.setEvent(event);
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
        Arrays.asList(new LabelIndexInfo("foo", LabelIndexInfo.LabelIndexType.GENERIC),
            new LabelIndexInfo("bar", LabelIndexInfo.LabelIndexType.CUSTOM),
            new LabelIndexInfo("baz", LabelIndexInfo.LabelIndexType.UNKNOWN))
    );
    Map<String, LabelIndex<?>> labelIndices = tested.getLabelIndices();
    assertEquals(3, labelIndices.size());
    assertTrue(labelIndices.containsKey("foo"));
    assertTrue(labelIndices.containsKey("bar"));
    assertTrue(labelIndices.containsKey("baz"));
    verify(eventsClient).getLabelIndicesInfos("1", "plaintext");
  }

  @Test
  @SuppressWarnings("unchecked")
  void getLabelIndex() {
    when(eventsClient.getLabelIndicesInfos(eq(event.getEventID()), eq("plaintext")))
        .thenReturn(
            Collections.singletonList(
                new LabelIndexInfo("index", LabelIndexInfo.LabelIndexType.GENERIC)
            )
        );
    when(eventsClient.getLabels(eq(tested), anyString(), any())).thenReturn(labelIndex);
    assertSame(labelIndex, tested.getLabelIndex("index"));
    verify(eventsClient).getLabelIndicesInfos("1", "plaintext");
    verify(eventsClient).getLabels(eq(tested), eq("index"), any(ProtoLabelAdapter.class));
  }

  @Test
  @SuppressWarnings("unchecked")
  void getLabelIndexCaches() {
    when(eventsClient.getLabelIndicesInfos(eq(event.getEventID()), eq("plaintext")))
        .thenReturn(
            Collections.singletonList(
                new LabelIndexInfo("index", LabelIndexInfo.LabelIndexType.GENERIC)
            )
        );
    when(eventsClient.getLabels(eq(tested), anyString(), any())).thenReturn(labelIndex);
    tested.getLabelIndex("index");
    verify(eventsClient).getLabelIndicesInfos("1", "plaintext");
    verify(eventsClient).getLabels(eq(tested), eq("index"), any(ProtoLabelAdapter.class));
    tested.getLabelIndex("index");
    verifyNoMoreInteractions(eventsClient);
  }

  @Test
  @SuppressWarnings("unchecked")
  void getGenericLabelIndex() {
    when(eventsClient.getLabelIndicesInfos(eq(event.getEventID()), eq("plaintext")))
        .thenReturn(
            Collections.singletonList(
                new LabelIndexInfo("index", LabelIndexInfo.LabelIndexType.GENERIC)
            )
        );
    when(eventsClient.getLabels(any(Document.class), anyString(), any(ProtoLabelAdapter.class))).thenReturn(labelIndex);
    LabelIndex<GenericLabel> index = tested.getLabelIndex("index");
    assertSame(labelIndex, index);
    verify(eventsClient).getLabels(eq(tested), eq("index"), eq(GenericLabelAdapter.NOT_DISTINCT_ADAPTER));
  }

  @Test
  void getGenericLabelIndexCaches() {
    when(eventsClient.getLabelIndicesInfos(eq(event.getEventID()), eq("plaintext")))
        .thenReturn(
            Collections.singletonList(
                new LabelIndexInfo("index", LabelIndexInfo.LabelIndexType.GENERIC)
            )
        );
    when(eventsClient.getLabels(eq(tested), anyString(), same(GenericLabelAdapter.NOT_DISTINCT_ADAPTER))).thenReturn(genericLabelIndex);
    tested.getLabelIndex("index");
    verify(eventsClient).getLabelIndicesInfos("1", "plaintext");
    verify(eventsClient).getLabels(tested, "index", GenericLabelAdapter.NOT_DISTINCT_ADAPTER);
    tested.getLabelIndex("index");
    verifyNoMoreInteractions(eventsClient);
  }

  @Test
  @SuppressWarnings({ "unchecked", "rawtypes" })
  void getLabeler() {
    when(labelAdapter.createLabelIndex(anyList())).thenReturn(labelIndex);
    tested.getDefaultAdapters().put("index", labelAdapter);
    try (Labeler<GenericLabel> labeler = tested.getLabeler("index")) {
      labeler.add(GenericLabel.createSpan(10, 20));
      labeler.add(GenericLabel.createSpan(0, 10));
    }
    ArgumentCaptor<List> captor = ArgumentCaptor.forClass(List.class);
    verify(eventsClient).getLabelIndicesInfos("1", "plaintext");
    verify(eventsClient).addLabels(eq("1"), eq("plaintext"), eq("index"),
        captor.capture(), same(labelAdapter));
    List value = captor.getValue();
    assertEquals(Arrays.asList(GenericLabel.createSpan(0, 10), GenericLabel.createSpan(10, 20)),
        value);
    tested.getLabelIndex("index");
    verifyNoMoreInteractions(eventsClient);
  }

  @Test
  @SuppressWarnings({ "unchecked", "rawtypes" })
  void genericDistinct() {
    try (Labeler<GenericLabel> labeler = tested.getLabeler("index", true)) {
      labeler.add(GenericLabel.withSpan(10, 20));
      labeler.add(GenericLabel.withSpan(0, 10));
    }
    ArgumentCaptor<List> captor = ArgumentCaptor.forClass(List.class);
    verify(eventsClient).getLabelIndicesInfos("1", "plaintext");
    verify(eventsClient).addLabels(eq("1"), eq("plaintext"), eq("index"),
        captor.capture(), same(GenericLabelAdapter.DISTINCT_ADAPTER));
    List value = captor.getValue();
    assertEquals(
        Arrays.asList(GenericLabel.createSpan(0, 10), GenericLabel.createSpan(10, 20)),
        value
    );
    tested.getLabelIndex("index");
    verifyNoMoreInteractions(eventsClient);
  }

  @Test
  @SuppressWarnings({ "unchecked", "rawtypes" })
  void addLabels() {
    List<GenericLabel> labels = Arrays.asList(
        GenericLabel.createSpan(10, 20),
        GenericLabel.createSpan(0, 10)
    );
    tested.addLabels("index", false, labels);
    ArgumentCaptor<List> captor = ArgumentCaptor.forClass(List.class);
    verify(eventsClient).getLabelIndicesInfos("1", "plaintext");
    verify(eventsClient).addLabels(eq("1"), eq("plaintext"), eq("index"),
        captor.capture(), same(GenericLabelAdapter.NOT_DISTINCT_ADAPTER));
    List value = captor.getValue();
    assertEquals(
        Arrays.asList(GenericLabel.createSpan(0, 10), GenericLabel.createSpan(10, 20)),
        value
    );
    tested.getLabelIndex("index");
    verifyNoMoreInteractions(eventsClient);
  }

  @Test
  @SuppressWarnings("unchecked")
  void addReferenceLabels() {
    List<GenericLabel> labels = Arrays.asList(
        GenericLabel.createSpan(0, 10),
        GenericLabel.createSpan(10, 20),
        GenericLabel.createSpan(21, 30)
    );
    List<GenericLabel> referencingLabels = Arrays.asList(
        GenericLabel.withSpan(0, 20)
            .setReference("a", Arrays.asList(labels.get(0), labels.get(1)))
            .build(),
        GenericLabel.withSpan(21, 30)
            .setReference("a", Collections.singletonList(labels.get(2)))
            .build()
    );
    tested.addLabels("ref_index", false, referencingLabels);
    verify(eventsClient).getLabelIndicesInfos("1", "plaintext");
    verifyNoMoreInteractions(eventsClient);
    tested.addLabels("index", false, labels);
    ArgumentCaptor<List<GenericLabel>> captor = ArgumentCaptor.forClass(List.class);
    verify(eventsClient).addLabels(eq("1"), eq("plaintext"), eq("index"),
        captor.capture(), same(GenericLabelAdapter.NOT_DISTINCT_ADAPTER));
    List<GenericLabel> value = captor.getValue();
    assertEquals(
        Arrays.asList(GenericLabel.createSpan(0, 10), GenericLabel.createSpan(10, 20), GenericLabel.createSpan(21, 30)),
        value
    );
    ArgumentCaptor<List<GenericLabel>> captor2 = ArgumentCaptor.forClass(List.class);
    verify(eventsClient).addLabels(eq("1"), eq("plaintext"), eq("ref_index"),
        captor2.capture(), same(GenericLabelAdapter.NOT_DISTINCT_ADAPTER));
  }
}

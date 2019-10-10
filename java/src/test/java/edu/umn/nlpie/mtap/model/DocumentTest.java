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
import org.mockito.ArgumentCaptor;

import java.util.Arrays;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.mockito.Mockito.*;

class DocumentTest {

  private EventsClient eventsClient;
  private Event event;

  private Document tested;
  private ProtoLabelAdapter labelAdapter;
  private LabelIndex labelIndex;

  @BeforeEach
  @SuppressWarnings("unchecked")
  void setUp() {
    eventsClient = mock(EventsClient.class);
    event = mock(Event.class);
    when(event.getClient()).thenReturn(eventsClient);
    when(event.getEventID()).thenReturn("1");

    labelAdapter = mock(ProtoLabelAdapter.class);
    labelIndex = mock(LabelIndex.class);

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
    when(eventsClient.getLabels(anyString(), anyString(), anyString(), any(ProtoLabelAdapter.class))).thenReturn(labelIndex);
    assertSame(labelIndex, tested.getLabelIndex("index"));
    verify(eventsClient).getLabels(eq("1"), eq("plaintext"), eq("index"), eq(GenericLabelAdapter.NOT_DISTINCT_ADAPTER));
  }

  @Test
  @SuppressWarnings("unchecked")
  void getGenericLabelIndexCaches() {
    when(eventsClient.getLabels(anyString(), anyString(), anyString(), same(GenericLabelAdapter.NOT_DISTINCT_ADAPTER))).thenReturn(labelIndex);
    tested.getLabelIndex("index");
    verify(eventsClient).getLabels("1", "plaintext", "index", GenericLabelAdapter.NOT_DISTINCT_ADAPTER);
    tested.getLabelIndex("index");
    verifyNoMoreInteractions(eventsClient);
  }

  @Test
  @SuppressWarnings("unchecked")
  void getLabeler() {
    when(labelAdapter.createLabelIndex(anyList())).thenReturn(labelIndex);
    try (Labeler<GenericLabel> labeler = tested.getLabeler("index", labelAdapter)) {
      labeler.add(GenericLabel.createSpan(10, 20));
      labeler.add(GenericLabel.createSpan(0, 10));
    }
    ArgumentCaptor<List> captor = ArgumentCaptor.forClass(List.class);
    verify(eventsClient).addLabels(eq("1"), eq("plaintext"), eq("index"),
        captor.capture(), same(labelAdapter));
    List value = captor.getValue();
    assertEquals(Arrays.asList(GenericLabel.createSpan(0, 10), GenericLabel.createSpan(10, 20)),
        value);
    tested.getLabelIndex("index");
    verifyNoMoreInteractions(eventsClient);
  }

  @Test
  @SuppressWarnings("unchecked")
  void genericDistinct() {
    try (Labeler<GenericLabel> labeler = tested.getLabeler("index", true)) {
      labeler.add(GenericLabel.withSpan(10, 20));
      labeler.add(GenericLabel.withSpan(0, 10));
    }
    ArgumentCaptor<List> captor = ArgumentCaptor.forClass(List.class);
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
  @SuppressWarnings("unchecked")
  void addLabels() {
    List<GenericLabel> labels = Arrays.asList(
        GenericLabel.createSpan(10, 20),
        GenericLabel.createSpan(0, 10)
    );
    tested.addLabels("index", false, labels);
    ArgumentCaptor<List> captor = ArgumentCaptor.forClass(List.class);
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
}

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

import edu.umn.nlpnewt.*;
import org.jetbrains.annotations.NotNull;

import java.util.*;

/**
 * Internal implementation of a document.
 * <p>
 * Users should create documents on {@link Event} objects.
 */
@Internal
final class DocumentImpl implements Document {

  private final EventsClient client;

  private final Event event;

  private final String documentName;

  private final Map<String, Labeler<?>> labelers = new HashMap<>();

  private final Map<String, LabelIndex<?>> labelIndexMap = new HashMap<>();

  private final List<String> createdIndices = new ArrayList<>();

  private String text = null;

  DocumentImpl(EventsClient client, Event event, String documentName) {
    this.client = client;
    this.event = event;
    this.documentName = documentName;
  }

  @Override
  public @NotNull Event getEvent() {
    return event;
  }

  @Override
  public @NotNull String getName() {
    return documentName;
  }

  @Override
  public @NotNull String getText() {
    if (text == null) {
      text = client.getDocumentText(event.getEventID(), documentName);
    }
    return text;
  }

  @SuppressWarnings("unchecked")
  @Override
  public @NotNull <L extends Label> LabelIndex<L> getLabelIndex(
      @NotNull String labelIndexName,
      @NotNull ProtoLabelAdapter<L> labelAdapter
  ) {
    LabelIndex<?> index = labelIndexMap.get(labelIndexName);
    if (index == null) {
      index = client.getLabels(event.getEventID(), documentName, labelIndexName, labelAdapter);
      labelIndexMap.put(labelIndexName, index);
    }
    return (LabelIndex<L>) index;
  }

  @SuppressWarnings("unchecked")
  @Override
  public @NotNull LabelIndex<GenericLabel> getLabelIndex(@NotNull String labelIndexName) {
    LabelIndex<?> index = labelIndexMap.get(labelIndexName);
    if (index == null) {
      index = client.getLabels(event.getEventID(), documentName, labelIndexName);
    }
    return (LabelIndex<GenericLabel>) index;
  }

  @Override
  public @NotNull <L extends Label> Labeler<L> getLabeler(@NotNull String labelIndexName,
                                                          @NotNull ProtoLabelAdapter<L> adapter) {
    @SuppressWarnings("unchecked")
    Labeler<L> existing = (Labeler<L>) labelers.get(labelIndexName);
    if (existing == null) {
      existing = new LabelerImpl<>(labelIndexName, adapter);
      labelers.put(labelIndexName, existing);
    }
    return existing;
  }

  @Override
  public @NotNull List<@NotNull String> getCreatedIndices() {
    return Collections.unmodifiableList(createdIndices);
  }

  @Override
  public @NotNull Labeler<GenericLabel> getLabeler(@NotNull String labelIndexName,
                                                   boolean isDistinct) {
    return getLabeler(labelIndexName,
        isDistinct ? GenericLabelAdapter.DISTINCT_ADAPTER : GenericLabelAdapter.NOT_DISTINCT_ADAPTER);
  }

  private class LabelerImpl<L extends Label> implements Labeler<L> {
    private final String labelIndexName;

    private final ProtoLabelAdapter<L> labelAdapter;

    private final List<L> labels = new ArrayList<>();

    private boolean done = false;

    LabelerImpl(String labelIndexName, ProtoLabelAdapter<L> labelAdapter) {
      this.labelIndexName = labelIndexName;
      this.labelAdapter = labelAdapter;
    }

    @Override
    public void add(L label) {
      if (done) throw new IllegalStateException("Labeler has already been finalized");
      labels.add(label);
    }

    @Override
    public void done() {
      if (!done) {
        done = true;

        labels.sort((Comparator<Label>) Label::compareLocation);

        labelIndexMap.put(labelIndexName, labelAdapter.createLabelIndex(labels));

        client.addLabels(event.getEventID(), documentName, labelIndexName, labels, labelAdapter);
        createdIndices.add(labelIndexName);
      }
    }

    @Override
    public @NotNull Class<L> getLabelType() {
      return labelAdapter.getLabelType();
    }

    @Override
    public void close() {
      done();
    }
  }
}

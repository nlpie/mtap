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

import edu.umn.nlpie.mtap.ExperimentalApi;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.*;


/**
 * A document of text and labels in the NEWT system.
 * <p>
 * Documents are keyed by their name, this is to allow pipelines to store different pieces of
 * related text on a single processing event. An example would be storing the English text
 * on one document keyed "English", and the translation in another language on another document.
 * <p>
 * Both label indices, once added, and the document text are immutable. This is to enable
 * parallelization and distribution of processing, and to prevent changes to upstream data that
 * has already been used in the creation of downstream data.
 * <p>
 * Documents can be added to Events using the {@link Event#getDocuments()} map.
 */
public class Document {
  private final String documentName;

  @Nullable
  private String text = null;

  @Nullable
  private Event event = null;

  private Map<String, LabelIndex<?>> labelIndexMap = null;

  private Map<String, Labeler<?>> labelers = null;

  private List<String> createdIndices = null;

  /**
   * Constructor for existing documents used by Event class.
   *
   * @param documentName The name of the document.
   */
  Document(@NotNull String documentName) {
    this.documentName = documentName;
  }

  /**
   * Creates a new document.
   *
   * @param documentName The document name.
   * @param text         The document text.
   */
  public Document(@NotNull String documentName, @NotNull String text) {
    this.documentName = documentName;
    this.text = text;
  }

  /**
   * Get the parent event.
   *
   * @return Event object.
   */
  public @Nullable Event getEvent() {
    return event;
  }

  /**
   * Set the parent event object.
   *
   * @param event The event.
   */
  public void setEvent(@Nullable Event event) {
    this.event = event;
  }

  /**
   * Gets the event-unique document name of this document.
   *
   * @return String document name.
   */
  public @NotNull String getName() {
    return documentName;
  }

  /**
   * Get the text of the document.
   *
   * @return String entire text of the document.
   */
  public @NotNull String getText() {
    if (text == null) {
      if (event == null || event.getClient() == null) {
        throw new AssertionError(
            "Text is null and event or events client is null, should not happen."
        );
      }
      text = event.getClient().getDocumentText(event.getEventID(), documentName);
    }
    return text;
  }

  /**
   * Gets information about the label indices in this document.
   *
   * @return A list of objects containing information about the label indices.
   */
  public @NotNull List<@NotNull LabelIndexInfo> getLabelIndicesInfo() {
    if (event != null && event.getClient() != null) {
      return event.getClient().getLabelIndicesInfos(event.getEventID(), documentName);
    }

    ArrayList<LabelIndexInfo> list = new ArrayList<>();
    for (Map.Entry<String, LabelIndex<?>> entry : labelIndexMap.entrySet()) {
      list.add(new LabelIndexInfo(entry.getKey(), LabelIndexInfo.LabelIndexType.JSON));
    }
    return list;
  }

  /**
   * Gets a label index from the events service.
   *
   * @param labelIndexName The name of the label index.
   * @param labelAdapter   The adapter to use.
   * @param <L>            The type of label in the index.
   *
   * @return The existing label index with the specified name.
   */
  @ExperimentalApi
  @SuppressWarnings("unchecked")
  public @NotNull <L extends Label> LabelIndex<L> getLabelIndex(
      @NotNull String labelIndexName,
      @NotNull ProtoLabelAdapter<L> labelAdapter
  ) {
    LabelIndex<?> index = getLabelIndexMap().get(labelIndexName);
    if (index == null && event != null && event.getClient() != null) {
      index = event.getClient()
          .getLabels(event.getEventID(), documentName, labelIndexName, labelAdapter);
      getLabelIndexMap().put(labelIndexName, index);
    }
    if (index == null) {
      throw new NoSuchElementException();
    }
    return (LabelIndex<L>) index;
  }

  /**
   * Gets a label index containing {@link GenericLabel} from the document service.
   *
   * @param labelIndexName The name identifier of the label index.
   *
   * @return The existing label index with the specified name.
   */
  public @NotNull LabelIndex<GenericLabel> getLabelIndex(@NotNull String labelIndexName) {
    return getLabelIndex(labelIndexName, GenericLabelAdapter.NOT_DISTINCT_ADAPTER);
  }

  /**
   * Returns a labeler for the type specified by {@code <L>} to the label index keyed by
   * {@code labelIndexName} using {@code adapter} to perform message adapting.
   * <p>
   * Example:
   * <pre>
   *     {@code
   *     try (Labeler<GenericLabel> labeler = document.getLabeler("sentences", Sentence.ADAPTER)) {
   *        labeler.add(GenericLabel.newBuilder(0, 22).build());
   *        labeler.add(GenericLabel.newBuilder(33, 55).build());
   *        labeler.add(GenericLabel.newBuilder(56, 88).build());
   *     }
   *     }
   * </pre>
   *
   * @param labelIndexName The label index name that the labels will be uploaded to.
   * @param adapter        The adapter.
   * @param <L>            The label type.
   *
   * @return Labeler object.
   *
   * @see ProtoLabelAdapter
   */
  @ExperimentalApi
  public @NotNull <L extends Label> Labeler<L> getLabeler(@NotNull String labelIndexName,
                                                          @NotNull ProtoLabelAdapter<L> adapter) {
    @SuppressWarnings("unchecked")
    Labeler<L> existing = (Labeler<L>) getLabelers().get(labelIndexName);
    if (existing == null) {
      existing = new LabelerImpl<>(labelIndexName, adapter);
      getLabelers().put(labelIndexName, existing);
    }
    return existing;
  }


  /**
   * Returns a labeler for non-distinct {@link GenericLabel} objects stored on
   * {@code labelIndexName}.
   * <p>
   * Example:
   * <pre>
   * try (Labeler&lt;GenericLabel&gt; labeler = document.getLabeler("pos_tags")) {
   *   labeler.add(GenericLabel.newBuilder(0, 4).setProperty("tag", "NOUN").build());
   *   labeler.add(GenericLabel.newBuilder(5, 9).setProperty("tag", "VERB").build());
   *   labeler.add(GenericLabel.newBuilder(10, 12).setProperty("tag", "ADP").build());
   *   labeler.add(GenericLabel.newBuilder(13, 16).setProperty("tag", "DET").build());
   *   labeler.add(GenericLabel.newBuilder(17, 22).setProperty("tag", "NOUN").build());
   * </pre>
   *
   * @param labelIndexName The index name to store the labels under.
   *
   * @return Labeler object, must be "closed" to send labels to server.
   */
  public @NotNull Labeler<GenericLabel> getLabeler(@NotNull String labelIndexName) {
    return getLabeler(labelIndexName, false);
  }

  /**
   * Returns a labeler for {@link GenericLabel} objects stored on {@code labelIndexName} with
   * distinctness specified by {@code isDistinct}.
   * <p>
   * The technical definition of distinctness is that there is an ordering of the labels in
   * the index in which the zipped start indices and end indices is non-decreasing, and there
   * are no labels of length 0.
   * <p>
   * Example:
   * <pre>
   *     {@code
   *     try (Labeler<GenericLabel> labeler = document.getLabeler("sentences", true)) {
   *        labeler.add(GenericLabel.newBuilder(0, 22).build());
   *        labeler.add(GenericLabel.newBuilder(33, 55).build());
   *        labeler.add(GenericLabel.newBuilder(56, 88).build());
   *     }
   *     }
   * </pre>
   *
   * @param labelIndexName The index name.
   * @param isDistinct     {@code true} if the labels are distinct (non-overlapping), {@code false}
   *                       otherwise.
   *
   * @return Labeler object.
   */
  public @NotNull Labeler<GenericLabel> getLabeler(@NotNull String labelIndexName,
                                                   boolean isDistinct) {
    ProtoLabelAdapter<GenericLabel> adapter;
    if (isDistinct) {
      adapter = GenericLabelAdapter.DISTINCT_ADAPTER;
    } else {
      adapter = GenericLabelAdapter.NOT_DISTINCT_ADAPTER;
    }
    return getLabeler(labelIndexName, adapter);
  }

  /**
   * Adds the list of generic labels as a new label index.
   *
   * @param labelIndexName The index name.
   * @param isDistinct     {@code true} if the labels are distinct (non-overlapping), {@code false}
   *                       otherwise
   * @param labels         The list of labels.
   *
   * @return A label index of the labels.
   */
  public @NotNull LabelIndex<GenericLabel> addLabels(@NotNull String labelIndexName,
                                                     boolean isDistinct,
                                                     @NotNull List<@NotNull GenericLabel> labels) {
    ProtoLabelAdapter<GenericLabel> adapter;
    if (isDistinct) {
      adapter = GenericLabelAdapter.DISTINCT_ADAPTER;
    } else {
      adapter = GenericLabelAdapter.NOT_DISTINCT_ADAPTER;
    }
    return addLabels(labelIndexName, adapter, labels);
  }

  /**
   * Adds a list of labels as a new label index.
   *
   * @param labelIndexName The index name.
   * @param labelAdapter   The adapter to use to convert the labels to proto messages.
   * @param labels         The labels.
   * @param <L>            The label type.
   *
   * @return A label index of the labels.
   */
  public <L extends Label> @NotNull LabelIndex<L> addLabels(
      @NotNull String labelIndexName,
      @NotNull ProtoLabelAdapter<L> labelAdapter,
      @NotNull List<@NotNull L> labels
  ) {
    labels.sort((Comparator<Label>) Label::compareLocation);

    LabelIndex<L> index = labelAdapter.createLabelIndex(labels);
    getLabelIndexMap().put(labelIndexName, index);
    if (event != null && event.getClient() != null) {
      event.getClient().addLabels(event.getEventID(), documentName, labelIndexName, labels,
          labelAdapter);
    }
    getCreatedIndices().add(labelIndexName);
    return index;
  }

  /**
   * The list of the names of all label indices that have been added to this document locally.
   *
   * @return An unmodifiable list of index names that have been added to this document.
   */
  public @NotNull List<@NotNull String> getCreatedIndices() {
    if (createdIndices == null) {
      createdIndices = new ArrayList<>();
    }
    return createdIndices;
  }

  public void addCreatedIndices(@NotNull Collection<@NotNull String> createdIndices) {
    getCreatedIndices().addAll(createdIndices);
  }

  private Map<String, LabelIndex<?>> getLabelIndexMap() {
    if (labelIndexMap == null) {
      labelIndexMap = new HashMap<>();
    }
    return labelIndexMap;
  }

  private Map<String, Labeler<?>> getLabelers() {
    if (labelers == null) {
      labelers = new HashMap<>();
    }
    return labelers;
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
        addLabels(labelIndexName, labelAdapter, labels);
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

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
 * A document of text and labels in the MTAP system.
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

  @Nullable
  private LabelIndices labelIndices = null;

  private Map<String, Labeler<?>> labelers = null;

  private List<String> createdIndices = null;

  private List<WaitingIndex<?>> waitingIndices = new ArrayList<>();

  private Map<String, ProtoLabelAdapter<?>> defaultAdapters = new HashMap<>();

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
   * Gets a label index from the events service.
   *
   * @param labelIndexName The name of the label index.
   * @param labelAdapter   This parameter doesn't do anything and will be removed.
   * @param <L>            The type of label in the index.
   * @return The existing label index with the specified name.
   */
  @ExperimentalApi
  @SuppressWarnings("unchecked")
  public @NotNull <L extends Label> LabelIndex<L> getLabelIndex(
      @NotNull String labelIndexName,
      @NotNull ProtoLabelAdapter<L> labelAdapter
  ) {
    return (LabelIndex<L>) getLabelIndices().get(labelIndexName);
  }

  /**
   * Gets a label index containing {@link GenericLabel} from the document service.
   *
   * @param labelIndexName The name identifier of the label index.
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
   * @return Labeler object.
   * @see ProtoLabelAdapter
   */
  @ExperimentalApi
  @SuppressWarnings("unchecked")
  public @NotNull <L extends Label> Labeler<L> getLabeler(@NotNull String labelIndexName,
                                                          @Nullable ProtoLabelAdapter<L> adapter) {
    if (adapter == null) {
      adapter = (ProtoLabelAdapter<L>) getDefaultAdapter(labelIndexName);
    }
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
   * Adds the list of Generic labels, looking up the label adapter from the default adapters map.
   *
   * @param labelIndexName The name of the label index.
   * @param labels The labels.
   */
  public void addLabels(@NotNull String labelIndexName,
                        @NotNull List<@NotNull ? extends Label> labels) {
    addLabels(labelIndexName, null, labels);
  }

  /**
   * Adds the list of generic labels as a new label index.
   *
   * @param labelIndexName The index name.
   * @param isDistinct     {@code true} if the labels are distinct (non-overlapping), {@code false}
   *                       otherwise
   * @param labels         The list of labels.
   */
  public void addLabels(@NotNull String labelIndexName,
                        boolean isDistinct,
                        @NotNull List<@NotNull GenericLabel> labels) {
    ProtoLabelAdapter<GenericLabel> adapter;
    if (isDistinct) {
      adapter = GenericLabelAdapter.DISTINCT_ADAPTER;
    } else {
      adapter = GenericLabelAdapter.NOT_DISTINCT_ADAPTER;
    }
    addLabels(labelIndexName, adapter, labels);
  }

  /**
   * Adds a list of labels as a new label index.
   *
   * @param labelIndexName The index name.
   * @param labelAdapter   The adapter to use to convert the labels to proto messages.
   * @param labels         The labels.
   * @param <L>            The label type.
   */
  @SuppressWarnings("unchecked")
  public <L extends Label> void addLabels(
      @NotNull String labelIndexName,
      @Nullable ProtoLabelAdapter<L> labelAdapter,
      @NotNull List<@NotNull L> labels
  ) {
    if (getLabelIndices().containsKey(labelIndexName)) {
      throw new IllegalArgumentException("Already contains index with name: " + labelIndexName);
    }

    if (labelAdapter == null) {
      labelAdapter = (ProtoLabelAdapter<L>) getDefaultAdapter(labelIndexName);
    }

    Set<Integer> waitingOn = staticize(labels, labelIndexName);
    if (waitingIndices.size() > 0) {
      Set<Integer> updatedIds = new HashSet<>();
      for (Label label : labels) {
        updatedIds.add(System.identityHashCode(label));
      }
      checkWaitingIndices(updatedIds);
    }

    getCreatedIndices().add(labelIndexName);
    LabelIndex<L> labelIndex = labelAdapter.createLabelIndex(labels);
    getLabelIndices().cache.put(labelIndexName, labelIndex);
    getLabelIndices().nameCache.add(labelIndexName);

    WaitingIndex<@NotNull L> waitingIndex = new WaitingIndex<>(labelIndexName, labels, labelAdapter, waitingOn);
    if (waitingOn.size() > 0) {
      waitingIndices.add(waitingIndex);
    } else {
      waitingIndex.finalizeLabels();
    }
  }

  private void checkWaitingIndices(Set<Integer> updatedIds) {
    List<WaitingIndex<?>> newWaitingIndices = new ArrayList<>();
    for (WaitingIndex<?> waitingIndex : waitingIndices) {
      waitingIndex.waitingOn.removeAll(updatedIds);
      if (waitingIndex.waitingOn.size() == 0) {
        waitingIndex.finalizeLabels();
      } else {
        newWaitingIndices.add(waitingIndex);
      }
    }
    waitingIndices = newWaitingIndices;
  }

  private Set<Integer> staticize(@NotNull List<@NotNull ? extends Label> labels,
                                 String labelIndexName) {
    labels.sort(Label::compareLocation);
    Set<Integer> waitingOn = new HashSet<>();
    int i = 0;
    for (Label label : labels) {
      label.setDocument(this);
      label.setIdentifier(i);
      label.setLabelIndexName(labelIndexName);
      i++;
    }
    for (Label label : labels) {
      label.collectFloatingReferences(waitingOn);
    }
    return waitingOn;
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

  private Map<String, Labeler<?>> getLabelers() {
    if (labelers == null) {
      labelers = new HashMap<>();
    }
    return labelers;
  }

  public LabelIndices getLabelIndices() {
    if (labelIndices == null) {
      labelIndices = new LabelIndices();
    }
    return labelIndices;
  }

  private @NotNull ProtoLabelAdapter<?> getDefaultAdapter(String labelIndexName) {
    ProtoLabelAdapter<?> adapter = defaultAdapters.get(labelIndexName);
    if (adapter != null) {
      return adapter;
    }
    Event event = getEvent();
    if (event != null) {
      adapter = event.getDefaultAdapters().get(labelIndexName);
      if (adapter != null) {
        return adapter;
      }
    }
    return GenericLabelAdapter.NOT_DISTINCT_ADAPTER;
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

  public class LabelIndices extends AbstractMap<String, LabelIndex<?>> {
    private final Map<String, LabelIndex<?>> cache = new HashMap<>();
    private final Set<String> nameCache = new HashSet<>();

    @NotNull
    @Override
    public Set<Entry<String, LabelIndex<?>>> entrySet() {
      refreshNames();
      return new AbstractSet<Entry<String, LabelIndex<?>>>() {
        @Override
        public Iterator<Entry<String, LabelIndex<?>>> iterator() {
          Iterator<String> it = nameCache.iterator();
          return new Iterator<Entry<String, LabelIndex<?>>>() {
            @Override
            public boolean hasNext() {
              return it.hasNext();
            }

            @Override
            public Entry<String, LabelIndex<?>> next() {
              String name = it.next();
              return new DelayedLabelIndexEntry(name);
            }
          };
        }

        @Override
        public int size() {
          return nameCache.size();
        }
      };
    }

    @Override
    public int size() {
      refreshNames();
      return nameCache.size();
    }

    @Override
    public LabelIndex<?> get(Object key) {
      if (!(key instanceof String)) {
        return null;
      }
      if (!containsKey(key)) {
        return null;
      }
      String labelIndexName = (String) key;
      LabelIndex<?> index = cache.get(key);
      if (index == null && event != null && event.getClient() != null) {
        index = event.getClient().getLabels(Document.this, labelIndexName, getDefaultAdapter(labelIndexName));
        for (Label label : index) {
          label.setDocument(Document.this);
          label.setLabelIndexName(labelIndexName);
        }
        nameCache.add(labelIndexName);
        cache.put(labelIndexName, index);
      }
      return index;
    }

    @Override
    public boolean containsKey(Object key) {
      if (!(key instanceof String)) {
        return false;
      }
      if (nameCache.contains(key)) {
        return true;
      }
      refreshNames();
      return nameCache.contains(key);
    }

    @NotNull
    @Override
    public Set<String> keySet() {
      refreshNames();
      return Collections.unmodifiableSet(nameCache);
    }

    private void refreshNames() {
      if (event != null && event.getClient() != null) {
        List<@NotNull LabelIndexInfo> infos = event.getClient().getLabelIndicesInfos(event.getEventID(), documentName);
        for (LabelIndexInfo info : infos) {
          nameCache.add(info.getIndexName());
        }
      }
    }


    private class DelayedLabelIndexEntry implements Map.Entry<String, LabelIndex<?>> {
      private final String labelIndexName;

      DelayedLabelIndexEntry(String labelIndexName) {
        this.labelIndexName = labelIndexName;
      }

      @Override
      public String getKey() {
        return labelIndexName;
      }

      @Override
      public LabelIndex<?> getValue() {
        return get(labelIndexName);
      }

      @Override
      public LabelIndex<?> setValue(LabelIndex<?> value) {
        throw new UnsupportedOperationException();
      }
    }
  }

  private class WaitingIndex<L extends Label> {
    private final String labelIndexName;
    private final List<L> labels;
    private final ProtoLabelAdapter<L> adapter;
    private final Set<Integer> waitingOn;

    public WaitingIndex(String labelIndexName,
                        List<L> labels,
                        ProtoLabelAdapter<L> adapter,
                        Set<Integer> waitingOn) {
      this.labelIndexName = labelIndexName;
      this.labels = labels;
      this.adapter = adapter;
      this.waitingOn = waitingOn;
    }

    private void finalizeLabels() {
      if (event != null && event.getClient() != null) {
        event.getClient().addLabels(event.getEventID(), documentName, labelIndexName, labels,
            adapter);
      }
    }
  }
}

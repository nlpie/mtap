/*
 * Copyright 2019 Regents of the University of Minnesota
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
package edu.umn.nlpnewt;

import org.jetbrains.annotations.NotNull;

import java.util.List;

/**
 * A document of text and labels in the NEWT system.
 * <p>
 * Documents are stored on accessed via creation or retrieval on an {@link Event} object using
 * {@link Event#addDocument(String, String)} or {@link Event#get(Object)}.
 * <p>
 * Documents are keyed by their name, this is to allow pipelines to store different pieces of
 * related text on a single processing event. An example would be storing the text of one language
 * on one document, and the text of another language on another, or, for example, storing the
 * plaintext.
 * <p>
 * Both label indices, once added, and the document text are immutable. This is to enable
 * parallelization and distribution of processing, and to prevent changes to upstream data that
 * has already been used in the creation of downstream data.
 */
public interface Document {
  /**
   * Get the parent event.
   *
   * @return Event object.
   */
  @NotNull Event getEvent();

  /**
   * Gets the event-unique document name of this document.
   *
   * @return String document name.
   */
  @NotNull String getName();

  /**
   * Get the text of the document.
   *
   * @return String entire text of the document.
   */
  @NotNull String getText();

  /**
   * Gets a label index containing {@link GenericLabel} from the document service.
   *
   * @param labelIndexName The name identifier of the label index.
   *
   * @return The existing label index with the specified name.
   */
  @NotNull LabelIndex<GenericLabel> getLabelIndex(@NotNull String labelIndexName);

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
  <L extends Label> @NotNull LabelIndex<L> getLabelIndex(
      @NotNull String labelIndexName,
      @NotNull ProtoLabelAdapter<L> labelAdapter
  );

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
  @NotNull
  default Labeler<GenericLabel> getLabeler(@NotNull String labelIndexName) {
    return getLabeler(labelIndexName, false);
  }

  /**
   * Returns a labeler for {@link GenericLabel} objects stored on {@code labelIndexName} with
   * distinctness specified by {@code isDistinct}.
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
  @NotNull Labeler<GenericLabel> getLabeler(@NotNull String labelIndexName, boolean isDistinct);

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
  <L extends Label> @NotNull Labeler<L> getLabeler(
      @NotNull String labelIndexName,
      @NotNull ProtoLabelAdapter<L> adapter
  );

  /**
   * The list of the names of all label indices that have been added to this document locally.
   *
   * @return An unmodifiable list of index names that have been added to this document.
   */
  @NotNull List<@NotNull String> getCreatedIndices();

}

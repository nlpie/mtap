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

import java.io.Closeable;

/**
 * An interface that is used to add labels to a document.
 * <p>
 * Usage:
 * <pre>
 *     {@code
 *     try (Labeler<GenericLabel> labeler = document.getLabeler("sentences", true)) {
 *        labeler.add(GenericLabel.newBuilder(0, 22).build());
 *        labeler.add(GenericLabel.newBuilder(33, 55).build());
 *        labeler.add(GenericLabel.newBuilder(56, 88).build());
 *     }
 *     }
 * </pre>
 * @param <T> The type of label.
 */
public interface Labeler<T extends Label> extends Closeable {
  /**
   * Adds the label to this labeler, it will be uploaded to the server when this labeler is closed
   * or {@link #done()} is called.
   *
   * @param label The label to add.
   */
  void add(T label);

  /**
   * Calls {@link Builder#build()} and then adds the result to the labeler.
   *
   * @param builder A builder for the label type.
   */
  default void add(Builder<T> builder) {
    add(builder.build());
  }

  /**
   * Closes this labeler, uploading any labels that have been added to the events service.
   */
  void done();

  /**
   * The type of label that should be added to this labeler.
   *
   * @return Class of the label type.
   */
  @NotNull Class<T> getLabelType();

  /**
   * Closes the labeler sending any labels to the server.
   */
  @Override
  void close();
}

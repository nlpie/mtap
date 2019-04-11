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
 * An immutable index of labels on text.
 *
 * @param <L> The label type.
 */
public interface LabelIndex<L extends Label> extends List<@NotNull L> {
  /**
   * Returns whether or not the index is distinct.
   * <p>
   * Index distinctness is based on whether the labels in the index can overlap or cannot overlap.
   * In the case of distinct, non-overlapping labels significant enhancements can be made to the
   * process of searching for labels.
   *
   * @return Returns {@code true} if the index is distinct, {@code false} if the index is not
   * distinct.
   */
  boolean isDistinct();
}

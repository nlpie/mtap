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
package edu.umn.nlpnewt.internal;

import edu.umn.nlpnewt.Internal;
import edu.umn.nlpnewt.Label;
import edu.umn.nlpnewt.LabelIndex;

import java.util.ArrayList;
import java.util.List;

/**
 * Internal implementation of standard (overlapping) label indices.
 * <p>
 * Users should get label indices via {@link edu.umn.nlpnewt.Document#getLabelIndex(String)} or
 * {@link edu.umn.nlpnewt.Newt#standardLabelIndex(List)}.
 *
 * @param <T> label type
 */
@Internal
final class StandardLabelIndex<T extends Label> extends AbstractLabelIndex<T> {
  StandardLabelIndex(List<T> labels) {
    super(labels);
  }

  static <L extends Label> LabelIndex<L> create(List<L> labels) {
    ArrayList<L> copy = new ArrayList<>(labels);
    copy.sort(Label.POSITION_COMPARATOR);
    return new StandardLabelIndex<>(copy);
  }

  @Override
  public int indexOf(Object o) {
    // TODO: This needs to be replaced with a binary search implementation.
    return super.indexOf(o);
  }

  @Override
  public boolean contains(Object o) {
    // TODO: This needs to replaced with a binary search implementation.
    return super.contains(o);
  }

  @Override
  public boolean isDistinct() {
    return false;
  }
}

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

import java.util.AbstractList;
import java.util.List;
import java.util.RandomAccess;

/**
 * An ordered collection of labels on text.
 *
 * @param <L> The type of label in the index.
 */
@Internal
abstract class AbstractLabelIndex<L extends Label>
    extends AbstractList<L>
    implements LabelIndex<L>, RandomAccess {
  protected final List<L> labels;

  AbstractLabelIndex(List<L> labels) {
    this.labels = labels;
  }

  @Override
  public L get(int index) {
    return labels.get(index);
  }

  @Override
  public int size() {
    return labels.size();
  }
}

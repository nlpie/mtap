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
import org.jetbrains.annotations.Nullable;

import java.util.AbstractCollection;
import java.util.Iterator;
import java.util.List;

@Internal
abstract class AbstractLabelIndex<L extends Label>
    extends AbstractCollection<@NotNull L> implements LabelIndex<L> {
  @Override
  public @NotNull List<@NotNull L> atLocation(int startIndex, int endIndex) {
    return atLocation(Span.of(startIndex, endIndex));
  }

  @Override
  public @NotNull LabelIndex<L> covering(int startIndex, int endIndex) {
    return covering(Span.of(startIndex, endIndex));
  }

  @Override
  public @NotNull LabelIndex<L> inside(@NotNull Label label) {
    return inside(label.getStartIndex(), label.getEndIndex());
  }

  @Override
  public @NotNull LabelIndex<L> beginningInside(@NotNull Label label) {
    return beginningInside(label.getStartIndex(), label.getEndIndex());
  }

  @Override
  public boolean containsSpan(int startIndex, int endIndex) {
    return containsSpan(Span.of(startIndex, endIndex));
  }

  @Override
  public @Nullable L firstAtLocation(@NotNull Label label) {
    Iterator<@NotNull L> it = atLocation(label).iterator();
    if (!it.hasNext()) {
      return null;
    }
    return it.next();
  }

  @Override
  public @Nullable L firstAtLocation(int startIndex, int endIndex) {
    return firstAtLocation(Span.of(startIndex, endIndex));
  }
}

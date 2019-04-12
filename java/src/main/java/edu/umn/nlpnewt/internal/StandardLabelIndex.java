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
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.*;

/**
 * Internal implementation of standard (overlapping) label indices.
 * <p>
 * Users should get label indices via {@link edu.umn.nlpnewt.Document#getLabelIndex(String)} or
 * {@link edu.umn.nlpnewt.Newt#standardLabelIndex(List)}.
 *
 * @param <L> label type
 */
@Internal
final class StandardLabelIndex<L extends Label>
    extends AbstractCollection<L> implements LabelIndex<L> {

  private final List<L> labels;

  StandardLabelIndex(List<L> labels) {
    this.labels = labels;
  }

  static <L extends Label> LabelIndex<L> create(List<L> labels) {
    ArrayList<L> copy = new ArrayList<>(labels);
    copy.sort((Comparator<Label>) Label::compareLocation);
    return new StandardLabelIndex<>(copy);
  }

  @Override
  public boolean isDistinct() {
    return false;
  }

  @Override
  public @NotNull LabelIndex<L> covering(int startIndex, int endIndex) {
    return null;
  }

  @Override
  public @NotNull LabelIndex<L> covering(@NotNull Label label) {
    return null;
  }

  @Override
  public @NotNull LabelIndex<L> inside(int startIndex, int endIndex) {
    return null;
  }

  @Override
  public @NotNull LabelIndex<L> inside(@NotNull Label label) {
    return null;
  }

  @Override
  public @NotNull LabelIndex<L> beginsInside(int startIndex, int endIndex) {
    return null;
  }

  @Override
  public @NotNull LabelIndex<L> beginsInside(@NotNull Label label) {
    return null;
  }

  @Override
  public @NotNull LabelIndex<L> ascendingStartIndex() {
    return null;
  }

  @Override
  public @NotNull LabelIndex<L> descendingStartIndex() {
    return null;
  }

  @Override
  public @NotNull LabelIndex<L> ascendingEndIndex() {
    return null;
  }

  @Override
  public @NotNull LabelIndex<L> descendingEndIndex() {
    return null;
  }

  @Nullable
  @Override
  public L first() {
    return null;
  }

  @Nullable
  @Override
  public L last() {
    return null;
  }

  @Override
  public boolean containsSpan(int startIndex, int endIndex) {
    return false;
  }

  @Override
  public boolean containsSpan(@NotNull Label label) {
    return false;
  }

  @Override
  public @NotNull Collection<L> atLocation(int startIndex, int endIndex) {
    return null;
  }

  @Override
  public @NotNull Collection<L> atLocation(@NotNull Label label) {
    return null;
  }

  @Nullable
  @Override
  public L firstAtLocation(int startIndex, int endIndex) {
    return null;
  }

  @Nullable
  @Override
  public L firstAtLocation(@NotNull Label label) {
    return null;
  }

  @Override
  public @NotNull List<L> asList() {
    return null;
  }


  @Override
  public Iterator<L> iterator() {
    return null;
  }

  @Override
  public int size() {
    return 0;
  }
}

package edu.umn.nlpnewt.internal;

import edu.umn.nlpnewt.Internal;
import edu.umn.nlpnewt.Label;
import edu.umn.nlpnewt.LabelIndex;
import org.jetbrains.annotations.NotNull;

import java.util.AbstractCollection;
import java.util.Collection;

@Internal
abstract class AbstractLabelIndex<L extends Label>
    extends AbstractCollection<L> implements LabelIndex<L> {
  @Override
  public @NotNull Collection<@NotNull L> atLocation(@NotNull Label label) {
    return atLocation(label.getStartIndex(), label.getEndIndex());
  }
}

package edu.umn.nlpnewt.internal;

import edu.umn.nlpnewt.Internal;
import edu.umn.nlpnewt.Label;
import edu.umn.nlpnewt.LabelIndex;
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

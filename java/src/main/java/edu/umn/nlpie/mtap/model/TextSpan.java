package edu.umn.nlpie.mtap.model;

import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

/**
 * A simple immutable label which only marks a location in text.
 */
public final class TextSpan implements Label {
  private final @NotNull String text;
  private final int startIndex;
  private final int endIndex;

  public TextSpan(@NotNull String text, int startIndex, int endIndex) {
    this.text = text;
    this.startIndex = startIndex;
    this.endIndex = endIndex;
  }

  @Override
  public @Nullable Document getDocument() {
    throw new UnsupportedOperationException();
  }

  @Override
  public void setDocument(@Nullable Document document) {
    throw new UnsupportedOperationException();
  }

  @Override
  public @Nullable String getLabelIndexName() {
    throw new UnsupportedOperationException();
  }

  @Override
  public void setLabelIndexName(@Nullable String labelIndexName) {
    throw new UnsupportedOperationException();
  }

  @Override
  public @Nullable Integer getIdentifier() {
    throw new UnsupportedOperationException();
  }

  @Override
  public void setIdentifier(@Nullable Integer identifier) {
    throw new UnsupportedOperationException();
  }

  @Override
  public int getStartIndex() {
    return startIndex;
  }

  @Override
  public int getEndIndex() {
    return endIndex;
  }

  @NotNull
  @Override
  public String getText() {
    return text.substring(startIndex, endIndex);
  }
}

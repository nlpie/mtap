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

import edu.umn.nlpie.mtap.common.JsonObjectImpl;
import org.junit.jupiter.api.Test;

import java.util.HashMap;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

/**
 * Tests {@link GenericLabel} and {@link Label} default methods via that subclass.
 *
 */
class GenericLabelTest {
  @Test
  void builderFromLabel() {
    GenericLabel span = GenericLabel.createSpan(0, 5);
    GenericLabel label = GenericLabel.withSpan(span).setProperty("foo", "bar").build();
    assertEquals(0, label.getStartIndex());
    assertEquals(5, label.getEndIndex());
  }

  @Test
  void createGenericLabel() {
    GenericLabel genericLabel = GenericLabel.withSpan(0, 5).setProperty("foo", "bar").build();
    assertEquals(0, genericLabel.getStartIndex());
    assertEquals(5, genericLabel.getEndIndex());
  }

  @Test
  void createGenericLabelCopy() {
    JsonObjectImpl jsonObject = JsonObjectImpl.newBuilder()
        .setProperty("foo", "bar")
        .build();
    GenericLabel genericLabel = new GenericLabel(jsonObject, new HashMap<>(), null, 0, 5);
    assertEquals(0, genericLabel.getStartIndex());
    assertEquals(5, genericLabel.getEndIndex());
    assertEquals("bar", genericLabel.getStringValue("foo"));
  }

  @Test
  void createGenericBadIndices() {
    assertThrows(IllegalArgumentException.class,
        () -> GenericLabel.withSpan(6, 5).build());
    assertThrows(IllegalArgumentException.class,
        () -> GenericLabel.withSpan(-1, 5).build());
  }

  @Test
  void locationEquals() {
    GenericLabel first = GenericLabel.createSpan(0, 5);
    GenericLabel second = GenericLabel.createSpan(0, 5);
    GenericLabel third = GenericLabel.createSpan(1, 5);
    GenericLabel fourth = GenericLabel.createSpan(0, 6);
    GenericLabel fifth = GenericLabel.createSpan(1, 6);

    assertTrue(first.locationEquals(second));
    assertFalse(first.locationEquals(third));
    assertFalse(first.locationEquals(fourth));
    assertFalse(first.locationEquals(fifth));
  }

  @Test
  void covers() {
    GenericLabel span = GenericLabel.createSpan(0, 6);
    assertTrue(span.covers(4, 6));
    assertFalse(span.covers(4, 8));
  }

  @Test
  void coversLabel() {
    GenericLabel span = GenericLabel.createSpan(0, 6);
    assertTrue(span.covers(GenericLabel.createSpan(4, 6)));
    assertFalse(span.covers(GenericLabel.createSpan(4, 8)));
  }

  @Test
  void isInside() {
    GenericLabel first = GenericLabel.createSpan(0, 10);
    assertTrue(first.isInside(0, 20));
    assertFalse(first.isInside(0, 5));
  }

  @Test
  void coveredText() {
    Document document = new Document("text", "foo bar");
    GenericLabel span = GenericLabel.withSpan(4, 7).build();
    span.setDocument(document);
    assertEquals("bar", span.getText());
  }

  @Test
  void coveredTextDocument() {
    Document document = mock(Document.class);
    GenericLabel span = GenericLabel.withSpan(4, 7).build();
    span.setDocument(document);
    when(document.getText()).thenReturn("foo bar");
    assertEquals("bar", span.getText());
  }

  @Test
  void compareLocation() {
    assertTrue(GenericLabel.createSpan(0, 6).compareLocation(GenericLabel.createSpan(4, 8)) < 0);
    assertTrue(GenericLabel.createSpan(4, 10).compareLocation(GenericLabel.createSpan(0, 4)) > 0);
    assertTrue(GenericLabel.createSpan(0, 6).compareLocation(GenericLabel.createSpan(0, 3)) > 0);
    assertEquals(0, GenericLabel.createSpan(0, 4).compareLocation(GenericLabel.createSpan(0, 4)));
  }

  @Test
  void compareStart() {
    assertTrue(GenericLabel.createSpan(0, 4).compareStart(GenericLabel.createSpan(1, 4)) < 0);
    assertTrue(GenericLabel.createSpan(1, 4).compareStart(GenericLabel.createSpan(0, 4)) > 0);
    assertEquals(0, GenericLabel.createSpan(1, 4).compareStart(GenericLabel.createSpan(1, 4)));
  }

  @Test
  void failOnReservedField() {
    assertThrows(IllegalStateException.class,
        () -> GenericLabel.withSpan(0, 0).setProperty("text", "").build());
    assertThrows(IllegalStateException.class,
        () -> GenericLabel.withSpan(0, 0).setProperty("document", "").build());
    assertThrows(IllegalStateException.class,
        () -> GenericLabel.withSpan(0, 0).setProperty("location", "").build());
  }
}

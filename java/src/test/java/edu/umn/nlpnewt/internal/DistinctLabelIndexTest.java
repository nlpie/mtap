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

package edu.umn.nlpnewt.internal;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class DistinctLabelIndexTest {
  DistinctLabelIndex<Span> tested = new DistinctLabelIndex<Span>(
      Span.of(0, 3),
      Span.of(3, 5),
      Span.of(6, 10),
      Span.of(11, 15),
      Span.of(16, 20)
  );

  @Test
  void higherIndexTwoEqual() {
    assertEquals(1, tested.higherIndex(3, null, null));
  }

  @Test
  void higherIndexBeginEquals() {
    assertEquals(2, tested.higherIndex(6, 1, 3));
  }

  @Test
  void higherIndexInside() {
    assertEquals(3, tested.higherIndex(7, 1, 4));
  }

  @Test
  void higherIndexEndEquals() {
    assertEquals(2, tested.higherIndex(5, 1, 3));
  }

  @Test
  void higherIndexBeforeFirst() {
    assertEquals(1, tested.higherIndex(2, 1, 3));
  }

  @Test
  void higherIndexAfterEnd() {
    assertEquals(-1, tested.higherIndex(16, 1, 3));
  }

  @Test
  void lowerIndexTwoEqual() {
    assertEquals(0, tested.lowerIndex(3, null, null));
  }

  @Test
  void lowerIndexBeginEquals() {
    assertEquals(1, tested.lowerIndex(6, 1, 3));
  }

  @Test
  void lowerIndexEndEquals() {
    assertEquals(1, tested.lowerIndex(5, 1, 3));
  }

  @Test
  void lowerIndexInside() {
    assertEquals(1, tested.lowerIndex(7, 1, 3));
  }

  @Test
  void lowerIndexBeforeFirst() {
    assertEquals(-1, tested.lowerIndex(2, 1, 3));
  }

  @Test
  void lowerIndexAfterEnd() {
    assertEquals(2, tested.lowerIndex(16, 1, 3));
  }

  @Test
  void lowerStartTwoEqual() {
    assertEquals(0, tested.lowerStart(0, null, null));
  }

  @Test
  void lowerStartBeginEquals() {
    assertEquals(2, tested.lowerStart(6, 1, 3));
  }

  @Test
  void lowerStartEndEquals() {
    assertEquals(2, tested.lowerStart(10, 1, 3));
  }

  @Test
  void lowerStartInside() {

  }
}
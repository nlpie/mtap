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
package edu.umn.nlpnewt.processing;

import java.io.Closeable;

/**
 * A timer that is used to time some piece of work in a processing context and automatically add
 * the time to the processing response.
 * <p>
 * It is closeable so that the timer can be used via the try-with-resources block:
 * <pre>
 *   {@code
 *   try (Timer timer = Newt.timingInfo().start("process_step_1")) {
 *     // do process step one.
 *   }
 *   }
 * </pre>
 */
public interface Timer extends Closeable {
  /**
   * Stops the timer, recording the time elapsed. Alias for {@link #close()}.
   */
  void stop();

  /**
   * Stops the timer, recording the time elapsed.
   */
  @Override
  void close();
}

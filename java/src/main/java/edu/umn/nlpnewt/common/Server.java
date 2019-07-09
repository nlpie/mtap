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
package edu.umn.nlpnewt.common;

import java.io.IOException;

/**
 * A generic server.
 */
public interface Server {
  /**
   * Starts the server, begins hosting.
   *
   * @throws IOException If there is some failure doing the set-up for the server, i.e. the port
   *                     cannot be bound, etc.
   */
  void start() throws IOException;

  /**
   * Tells the server to shutdown receiving requests and to shut down.
   */
  void shutdown();

  /**
   * Waits until the server has shutdown.
   *
   * @throws InterruptedException If the thread is interrupted while waiting for the shutdown to
   *                              finish.
   */
  void blockUntilShutdown() throws InterruptedException;

  /**
   * Gets the port that the server is bound to.
   *
   * @return The integer port.
   */
  int getPort();
}

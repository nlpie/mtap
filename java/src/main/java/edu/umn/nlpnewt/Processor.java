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


import java.lang.annotation.*;

/**
 * Annotation which marks a {@link AbstractEventProcessor} or {@link AbstractDocumentProcessor} as
 * available for service discovery registration.
 */
@Documented
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
public @interface Processor {
  /**
   * The processor name. This will be the default name that the processor identifies under with
   * service discovery. It should be a valid dns path component, i.e. only consisting of
   * alphanumeric characters and dashes.
   *
   * @return String processor name.
   */
  String value();
}

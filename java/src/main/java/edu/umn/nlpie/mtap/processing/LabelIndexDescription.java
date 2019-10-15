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

package edu.umn.nlpie.mtap.processing;


import java.lang.annotation.*;

/**
 * A description of the input and output label indices of a processor.
 */
@Documented
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
public @interface LabelIndexDescription {
  /**
   * The default name of the label index.
   *
   * @return A label index name identifier.
   */
  String name() default "";

  /**
   * If this is an output of another processor, that processor's name followed by a slash
   * and the default output name of the index go here. Example: "sentence-detector/sentences".
   *
   * @return A string reference.
   */
  String reference() default "";

  /**
   * If the name comes from a parameter, the key for that parameter.
   *
   * @return A string key.
   */
  String nameFromParameter() default "";

  /**
   * Whether the label index is an optional input.
   *
   * @return True if optional, false if required.
   */
  boolean optional() default false;

  /**
   * A description of the label index.
   *
   * @return String description of the label index.
   */
  String description() default "";

  /**
   * The properties of the labels.
   *
   * @return array of PropertyDescription
   */
  PropertyDescription[] properties() default {};
}

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
 * Annotation which marks a {@link EventProcessor} or {@link DocumentProcessor} as
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

  /**
   * A human-readable name for the processor.
   *
   * @return String human readable name like "Part of Speech Tagger"
   */
  String humanName() default "";

  /**
   * A short description of what the processor does.
   *
   * @return String description.
   */
  String description() default "";

  /**
   * The processor's entry point / main class.
   *
   * @return A string of the fully qualified class name.
   */
  String entryPoint() default "";

  /**
   * The processor's language. Defaults to "java".
   *
   * @return String identifier for the language.
   */
  String language() default "java";

  /**
   * Descriptions of the processor's parameters.
   *
   * @return Array of parameter descriptions.
   */
  ParameterDescription[] parameters() default {};

  /**
   * Descriptions of the input label indices.
   *
   * @return Array of descriptions for the label indices the processor uses.
   */
  LabelIndexDescription[] inputs() default {};

  /**
   * Descriptions of the output label indices.
   *
   * @return Array of descriptions for label indices the processor creates.
   */
  LabelIndexDescription[] outputs() default {};
}

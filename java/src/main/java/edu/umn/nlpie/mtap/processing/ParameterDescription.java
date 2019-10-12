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
 * A description of processor parameters.
 */
@Documented
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
public @interface ParameterDescription {
  /**
   * The parameter name / key.
   *
   * @return String name / key for the parameter.
   */
  String name();

  /**
   * A short description of the parameter and what it does.
   *
   * @return String description of the parameter.
   */
  String description() default "";

  /**
   * The expected data type of the parameter.
   *
   * @return String expected data; str, float, or bool; List[T] or Mapping[T1, T2] of those.
   */
  String dataType() default "";

  /**
   * Whether the parameter is required, i.e. needed by the processor in order to function.
   *
   * @return True if parameter is required, False if not required.
   */
  boolean required() default false;
}

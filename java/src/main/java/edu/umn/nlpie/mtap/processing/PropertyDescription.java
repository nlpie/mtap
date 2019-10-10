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
 * A description of the properties of labels.
 */
@Documented
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
public @interface PropertyDescription {
  /**
   * The name of the property.
   *
   * @return String accessor name of the property.
   */
  String name();

  /**
   * A short description of the property.
   *
   * @return Description of the property.
   */
  String description() default "";

  /**
   * The data type of the property: str, float, or boolean; List[T] or Mapping[T1, T2] of those.
   *
   * @return String data type of the property.
   */
  String dataType() default "";

  /**
   * Whether the property can have a valid value of null.
   *
   * @return True if null is valid, False if null is not valid.
   */
  boolean nullable() default false;
}

package edu.umn.nlpie.mtap.processing;

/**
 * A key-value pair.
 */
public @interface KeyValue {
  /**
   * The key.
   *
   * @return A string key identifier.
   */
  String key();

  /**
   * The value.
   *
   * @return A string value identifier.
   */
  String value();
}

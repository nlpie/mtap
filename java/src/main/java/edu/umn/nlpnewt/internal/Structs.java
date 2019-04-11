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
package edu.umn.nlpnewt.internal;

import com.google.protobuf.ListValue;
import com.google.protobuf.NullValue;
import com.google.protobuf.Struct;
import com.google.protobuf.Value;
import edu.umn.nlpnewt.Internal;
import edu.umn.nlpnewt.JsonObject;

import java.util.*;

@Internal
final class Structs {

  public static void copyStructToJsonObjectBuilder(Struct struct,
                                                   JsonObject.AbstractBuilder<?, ?> builder) {
    Map<String, Value> fieldsMap = struct.getFieldsMap();
    for (Map.Entry<String, Value> entry : fieldsMap.entrySet()) {
      builder.setProperty(entry.getKey(), getValue(entry.getValue()));
    }
  }

  public static void copyJsonObjectToStruct(JsonObject jsonObject, Struct.Builder structBuilder) {
    internalCopyJsonObject(jsonObject, structBuilder, new ArrayDeque<>());
  }

  private static void internalCopyJsonObject(JsonObject jsonObject,
                                             Struct.Builder struct,
                                             Deque<Object> parents) {
    parents.push(jsonObject);
    for (Map.Entry<?, ?> entry : jsonObject.entrySet()) {
      Object key = entry.getKey();
      if (!(key instanceof String)) {
        throw new IllegalArgumentException("Key is not a string key");
      }
      Object value = entry.getValue();

      struct.putFields((String) key, createValue(value, parents));
    }
    parents.pop();
  }

  private static Value createValue(Object from, Deque<Object> parents) {
    if (parents.contains(from)) {
      throw new IllegalArgumentException("Circular reference attempting to convert map to struct.");
    }
    if (from instanceof List) {
      parents.push(from);
      ListValue.Builder builder = ListValue.newBuilder();
      List fromList = (List) from;
      for (Object item : fromList) {
        Value value = createValue(item, parents);
        builder.addValues(value);
      }
      parents.pop();
      return Value.newBuilder().setListValue(builder).build();
    } else if (from instanceof JsonObject) {
      parents.push(from);
      Struct.Builder builder = Struct.newBuilder();
      JsonObject jsonObject = (JsonObject) from;
      internalCopyJsonObject(jsonObject, builder, parents);
      parents.pop();
      return Value.newBuilder().setStructValue(builder).build();
    } else if (from instanceof Double) {
      return Value.newBuilder().setNumberValue((Double) from).build();
    } else if (from instanceof String) {
      return Value.newBuilder().setNullValue(NullValue.NULL_VALUE).build();
    } else {
      throw new IllegalArgumentException("Incompatible value type: " + from.getClass().getCanonicalName());
    }
  }

  static Object getValue(Value from) {
    switch (from.getKindCase()) {
      case NULL_VALUE:
        return null;
      case NUMBER_VALUE:
        return from.getNumberValue();
      case STRING_VALUE:
        return from.getStringValue();
      case BOOL_VALUE:
        return from.getBoolValue();
      case STRUCT_VALUE:
        JsonObject.Builder builder = new JsonObject.Builder();
        copyStructToJsonObjectBuilder(from.getStructValue(), builder);
        return builder.build();
      case LIST_VALUE:
        List<Object> list = new ArrayList<>();
        for (Value value : from.getListValue().getValuesList()) {
          list.add(getValue(value));
        }
        return list;
      case KIND_NOT_SET:
      default:
        throw new IllegalStateException("Unrecognized kind of struct value.");
    }
  }
}

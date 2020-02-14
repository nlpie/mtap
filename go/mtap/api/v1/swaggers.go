package mtap_api_v1 

const (
Events = "{\n  \"swagger\": \"2.0\",\n  \"info\": {\n    \"title\": \"mtap/api/v1/events.proto\",\n    \"version\": \"version not set\"\n  },\n  \"schemes\": [\n    \"http\",\n    \"https\"\n  ],\n  \"consumes\": [\n    \"application/json\"\n  ],\n  \"produces\": [\n    \"application/json\"\n  ],\n  \"paths\": {\n    \"/v1/events/{event_id}\": {\n      \"delete\": {\n        \"summary\": \"Cedes a lease for an event, allowing this service to delete the\\nevent if no active leases remain.\",\n        \"operationId\": \"CloseEvent\",\n        \"responses\": {\n          \"200\": {\n            \"description\": \"A successful response.\",\n            \"schema\": {\n              \"$ref\": \"#/definitions/v1CloseEventResponse\"\n            }\n          }\n        },\n        \"parameters\": [\n          {\n            \"name\": \"event_id\",\n            \"description\": \"The event_id to release.\",\n            \"in\": \"path\",\n            \"required\": true,\n            \"type\": \"string\"\n          },\n          {\n            \"name\": \"lease_id\",\n            \"description\": \"Optional, if the lease has a timed expiration, this is required to prevent\\nreleasing the lease twice.\",\n            \"in\": \"query\",\n            \"required\": false,\n            \"type\": \"integer\",\n            \"format\": \"int32\"\n          }\n        ],\n        \"tags\": [\n          \"Events\"\n        ]\n      },\n      \"post\": {\n        \"summary\": \"Acquires a lease for an event, which will prevent this service\\nfrom deleting the event while the lease is still valid. Can be used to\\neither create new events or return existing events.\",\n        \"operationId\": \"OpenEvent\",\n        \"responses\": {\n          \"200\": {\n            \"description\": \"A successful response.\",\n            \"schema\": {\n              \"$ref\": \"#/definitions/v1OpenEventResponse\"\n            }\n          }\n        },\n        \"parameters\": [\n          {\n            \"name\": \"event_id\",\n            \"description\": \"The globally unique event identifier.\",\n            \"in\": \"path\",\n            \"required\": true,\n            \"type\": \"string\"\n          },\n          {\n            \"name\": \"body\",\n            \"in\": \"body\",\n            \"required\": true,\n            \"schema\": {\n              \"$ref\": \"#/definitions/v1OpenEventRequest\"\n            }\n          }\n        ],\n        \"tags\": [\n          \"Events\"\n        ]\n      }\n    },\n    \"/v1/events/{event_id}/binaries\": {\n      \"get\": {\n        \"operationId\": \"GetAllBinaryDataNames\",\n        \"responses\": {\n          \"200\": {\n            \"description\": \"A successful response.\",\n            \"schema\": {\n              \"$ref\": \"#/definitions/v1GetAllBinaryDataNamesResponse\"\n            }\n          }\n        },\n        \"parameters\": [\n          {\n            \"name\": \"event_id\",\n            \"description\": \"The unique event identifier.\",\n            \"in\": \"path\",\n            \"required\": true,\n            \"type\": \"string\"\n          }\n        ],\n        \"tags\": [\n          \"Events\"\n        ]\n      }\n    },\n    \"/v1/events/{event_id}/binaries/{binary_data_name}\": {\n      \"get\": {\n        \"operationId\": \"GetBinaryData\",\n        \"responses\": {\n          \"200\": {\n            \"description\": \"A successful response.\",\n            \"schema\": {\n              \"$ref\": \"#/definitions/v1GetBinaryDataResponse\"\n            }\n          }\n        },\n        \"parameters\": [\n          {\n            \"name\": \"event_id\",\n            \"description\": \"The unique event identifier.\",\n            \"in\": \"path\",\n            \"required\": true,\n            \"type\": \"string\"\n          },\n          {\n            \"name\": \"binary_data_name\",\n            \"description\": \"The binary data key.\",\n            \"in\": \"path\",\n            \"required\": true,\n            \"type\": \"string\"\n          }\n        ],\n        \"tags\": [\n          \"Events\"\n        ]\n      },\n      \"post\": {\n        \"operationId\": \"AddBinaryData\",\n        \"responses\": {\n          \"200\": {\n            \"description\": \"A successful response.\",\n            \"schema\": {\n              \"$ref\": \"#/definitions/v1AddBinaryDataResponse\"\n            }\n          }\n        },\n        \"parameters\": [\n          {\n            \"name\": \"event_id\",\n            \"description\": \"The unique event identifier.\",\n            \"in\": \"path\",\n            \"required\": true,\n            \"type\": \"string\"\n          },\n          {\n            \"name\": \"binary_data_name\",\n            \"description\": \"The binary data key.\",\n            \"in\": \"path\",\n            \"required\": true,\n            \"type\": \"string\"\n          },\n          {\n            \"name\": \"body\",\n            \"in\": \"body\",\n            \"required\": true,\n            \"schema\": {\n              \"$ref\": \"#/definitions/v1AddBinaryDataRequest\"\n            }\n          }\n        ],\n        \"tags\": [\n          \"Events\"\n        ]\n      }\n    },\n    \"/v1/events/{event_id}/documents\": {\n      \"get\": {\n        \"summary\": \"Returns the names keys of all documents that are stored on an event.\",\n        \"operationId\": \"GetAllDocumentNames\",\n        \"responses\": {\n          \"200\": {\n            \"description\": \"A successful response.\",\n            \"schema\": {\n              \"$ref\": \"#/definitions/v1GetAllDocumentNamesResponse\"\n            }\n          }\n        },\n        \"parameters\": [\n          {\n            \"name\": \"event_id\",\n            \"description\": \"The unique event identifier.\",\n            \"in\": \"path\",\n            \"required\": true,\n            \"type\": \"string\"\n          }\n        ],\n        \"tags\": [\n          \"Events\"\n        ]\n      }\n    },\n    \"/v1/events/{event_id}/documents/{document_name}\": {\n      \"get\": {\n        \"summary\": \"Returns the text of a document.\",\n        \"operationId\": \"GetDocumentText\",\n        \"responses\": {\n          \"200\": {\n            \"description\": \"A successful response.\",\n            \"schema\": {\n              \"$ref\": \"#/definitions/v1GetDocumentTextResponse\"\n            }\n          }\n        },\n        \"parameters\": [\n          {\n            \"name\": \"event_id\",\n            \"description\": \"Unique event identifier that the document occurs on.\",\n            \"in\": \"path\",\n            \"required\": true,\n            \"type\": \"string\"\n          },\n          {\n            \"name\": \"document_name\",\n            \"description\": \"Retrieves the text of the document with this name.\",\n            \"in\": \"path\",\n            \"required\": true,\n            \"type\": \"string\"\n          }\n        ],\n        \"tags\": [\n          \"Events\"\n        ]\n      },\n      \"post\": {\n        \"summary\": \"Adds a new document to an event.\",\n        \"operationId\": \"AddDocument\",\n        \"responses\": {\n          \"200\": {\n            \"description\": \"A successful response.\",\n            \"schema\": {\n              \"$ref\": \"#/definitions/v1AddDocumentResponse\"\n            }\n          }\n        },\n        \"parameters\": [\n          {\n            \"name\": \"event_id\",\n            \"description\": \"The unique event identifier.\",\n            \"in\": \"path\",\n            \"required\": true,\n            \"type\": \"string\"\n          },\n          {\n            \"name\": \"document_name\",\n            \"description\": \"The event-unique document name.\",\n            \"in\": \"path\",\n            \"required\": true,\n            \"type\": \"string\"\n          },\n          {\n            \"name\": \"body\",\n            \"in\": \"body\",\n            \"required\": true,\n            \"schema\": {\n              \"$ref\": \"#/definitions/v1AddDocumentRequest\"\n            }\n          }\n        ],\n        \"tags\": [\n          \"Events\"\n        ]\n      }\n    },\n    \"/v1/events/{event_id}/documents/{document_name}/labels\": {\n      \"get\": {\n        \"summary\": \"Returns the names keys of all label indices that are stored on a document.\",\n        \"operationId\": \"GetLabelIndicesInfo\",\n        \"responses\": {\n          \"200\": {\n            \"description\": \"A successful response.\",\n            \"schema\": {\n              \"$ref\": \"#/definitions/v1GetLabelIndicesInfoResponse\"\n            }\n          }\n        },\n        \"parameters\": [\n          {\n            \"name\": \"event_id\",\n            \"description\": \"The unique event identifier.\",\n            \"in\": \"path\",\n            \"required\": true,\n            \"type\": \"string\"\n          },\n          {\n            \"name\": \"document_name\",\n            \"description\": \"The document name on the event.\",\n            \"in\": \"path\",\n            \"required\": true,\n            \"type\": \"string\"\n          }\n        ],\n        \"tags\": [\n          \"Events\"\n        ]\n      }\n    },\n    \"/v1/events/{event_id}/documents/{document_name}/labels/{index_name}\": {\n      \"get\": {\n        \"summary\": \"Gets all of the labels for a single label index.\",\n        \"operationId\": \"GetLabels\",\n        \"responses\": {\n          \"200\": {\n            \"description\": \"A successful response.\",\n            \"schema\": {\n              \"$ref\": \"#/definitions/v1GetLabelsResponse\"\n            }\n          }\n        },\n        \"parameters\": [\n          {\n            \"name\": \"event_id\",\n            \"description\": \"The event that contains the document and labels.\",\n            \"in\": \"path\",\n            \"required\": true,\n            \"type\": \"string\"\n          },\n          {\n            \"name\": \"document_name\",\n            \"description\": \"The document that contains the labels.\",\n            \"in\": \"path\",\n            \"required\": true,\n            \"type\": \"string\"\n          },\n          {\n            \"name\": \"index_name\",\n            \"description\": \"The index name of the labels on the document.\",\n            \"in\": \"path\",\n            \"required\": true,\n            \"type\": \"string\"\n          }\n        ],\n        \"tags\": [\n          \"Events\"\n        ]\n      },\n      \"post\": {\n        \"summary\": \"Adds a single label index to the document.\",\n        \"operationId\": \"AddLabels\",\n        \"responses\": {\n          \"200\": {\n            \"description\": \"A successful response.\",\n            \"schema\": {\n              \"$ref\": \"#/definitions/v1AddLabelsResponse\"\n            }\n          }\n        },\n        \"parameters\": [\n          {\n            \"name\": \"event_id\",\n            \"description\": \"The unique event identifier.\",\n            \"in\": \"path\",\n            \"required\": true,\n            \"type\": \"string\"\n          },\n          {\n            \"name\": \"document_name\",\n            \"description\": \"The document name on the event.\",\n            \"in\": \"path\",\n            \"required\": true,\n            \"type\": \"string\"\n          },\n          {\n            \"name\": \"index_name\",\n            \"description\": \"A document-unique identifier for the index to create on the document.\",\n            \"in\": \"path\",\n            \"required\": true,\n            \"type\": \"string\"\n          },\n          {\n            \"name\": \"body\",\n            \"in\": \"body\",\n            \"required\": true,\n            \"schema\": {\n              \"$ref\": \"#/definitions/v1AddLabelsRequest\"\n            }\n          }\n        ],\n        \"tags\": [\n          \"Events\"\n        ]\n      }\n    },\n    \"/v1/events/{event_id}/metadata\": {\n      \"get\": {\n        \"summary\": \"Endpoint to get all metadata associated with an event.\",\n        \"operationId\": \"GetAllMetadata\",\n        \"responses\": {\n          \"200\": {\n            \"description\": \"A successful response.\",\n            \"schema\": {\n              \"$ref\": \"#/definitions/v1GetAllMetadataResponse\"\n            }\n          }\n        },\n        \"parameters\": [\n          {\n            \"name\": \"event_id\",\n            \"description\": \"Event unique identifier string.\",\n            \"in\": \"path\",\n            \"required\": true,\n            \"type\": \"string\"\n          }\n        ],\n        \"tags\": [\n          \"Events\"\n        ]\n      }\n    },\n    \"/v1/events/{event_id}/metadata/{key}\": {\n      \"post\": {\n        \"summary\": \"Adds a new metadata entry to an event.\",\n        \"operationId\": \"AddMetadata\",\n        \"responses\": {\n          \"200\": {\n            \"description\": \"A successful response.\",\n            \"schema\": {\n              \"$ref\": \"#/definitions/v1AddMetadataResponse\"\n            }\n          }\n        },\n        \"parameters\": [\n          {\n            \"name\": \"event_id\",\n            \"description\": \"The unique event identifier.\",\n            \"in\": \"path\",\n            \"required\": true,\n            \"type\": \"string\"\n          },\n          {\n            \"name\": \"key\",\n            \"description\": \"The key for the metadata entry\",\n            \"in\": \"path\",\n            \"required\": true,\n            \"type\": \"string\"\n          },\n          {\n            \"name\": \"body\",\n            \"in\": \"body\",\n            \"required\": true,\n            \"schema\": {\n              \"$ref\": \"#/definitions/v1AddMetadataRequest\"\n            }\n          }\n        ],\n        \"tags\": [\n          \"Events\"\n        ]\n      }\n    }\n  },\n  \"definitions\": {\n    \"GetLabelIndicesInfoResponseLabelIndexInfo\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"index_name\": {\n          \"type\": \"string\",\n          \"description\": \"A document-unique identifier for the index on the document.\"\n        },\n        \"type\": {\n          \"$ref\": \"#/definitions/LabelIndexInfoLabelIndexType\"\n        }\n      }\n    },\n    \"LabelIndexInfoLabelIndexType\": {\n      \"type\": \"string\",\n      \"enum\": [\n        \"UNKNOWN\",\n        \"JSON\",\n        \"OTHER\"\n      ],\n      \"default\": \"UNKNOWN\",\n      \"description\": \" - UNKNOWN: Default, no labels field set or not known.\\n - JSON: Has the \\\"json_labels\\\" field set.\\n - OTHER: Has the \\\"other_labels\\\" field set.\"\n    },\n    \"protobufAny\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"type_url\": {\n          \"type\": \"string\",\n          \"description\": \"A URL/resource name that uniquely identifies the type of the serialized\\nprotocol buffer message. This string must contain at least\\none \\\"/\\\" character. The last segment of the URL's path must represent\\nthe fully qualified name of the type (as in\\n`path/google.protobuf.Duration`). The name should be in a canonical form\\n(e.g., leading \\\".\\\" is not accepted).\\n\\nIn practice, teams usually precompile into the binary all types that they\\nexpect it to use in the context of Any. However, for URLs which use the\\nscheme `http`, `https`, or no scheme, one can optionally set up a type\\nserver that maps type URLs to message definitions as follows:\\n\\n* If no scheme is provided, `https` is assumed.\\n* An HTTP GET on the URL must yield a [google.protobuf.Type][]\\n  value in binary format, or produce an error.\\n* Applications are allowed to cache lookup results based on the\\n  URL, or have them precompiled into a binary to avoid any\\n  lookup. Therefore, binary compatibility needs to be preserved\\n  on changes to types. (Use versioned type names to manage\\n  breaking changes.)\\n\\nNote: this functionality is not currently available in the official\\nprotobuf release, and it is not used for type URLs beginning with\\ntype.googleapis.com.\\n\\nSchemes other than `http`, `https` (or the empty scheme) might be\\nused with implementation specific semantics.\"\n        },\n        \"value\": {\n          \"type\": \"string\",\n          \"format\": \"byte\",\n          \"description\": \"Must be a valid serialized protocol buffer of the above specified type.\"\n        }\n      },\n      \"description\": \"`Any` contains an arbitrary serialized protocol buffer message along with a\\nURL that describes the type of the serialized message.\\n\\nProtobuf library provides support to pack/unpack Any values in the form\\nof utility functions or additional generated methods of the Any type.\\n\\nExample 1: Pack and unpack a message in C++.\\n\\n    Foo foo = ...;\\n    Any any;\\n    any.PackFrom(foo);\\n    ...\\n    if (any.UnpackTo(\\u0026foo)) {\\n      ...\\n    }\\n\\nExample 2: Pack and unpack a message in Java.\\n\\n    Foo foo = ...;\\n    Any any = Any.pack(foo);\\n    ...\\n    if (any.is(Foo.class)) {\\n      foo = any.unpack(Foo.class);\\n    }\\n\\n Example 3: Pack and unpack a message in Python.\\n\\n    foo = Foo(...)\\n    any = Any()\\n    any.Pack(foo)\\n    ...\\n    if any.Is(Foo.DESCRIPTOR):\\n      any.Unpack(foo)\\n      ...\\n\\n Example 4: Pack and unpack a message in Go\\n\\n     foo := \\u0026pb.Foo{...}\\n     any, err := ptypes.MarshalAny(foo)\\n     ...\\n     foo := \\u0026pb.Foo{}\\n     if err := ptypes.UnmarshalAny(any, foo); err != nil {\\n       ...\\n     }\\n\\nThe pack methods provided by protobuf library will by default use\\n'type.googleapis.com/full.type.name' as the type URL and the unpack\\nmethods only use the fully qualified type name after the last '/'\\nin the type URL, for example \\\"foo.bar.com/x/y.z\\\" will yield type\\nname \\\"y.z\\\".\\n\\n\\nJSON\\n====\\nThe JSON representation of an `Any` value uses the regular\\nrepresentation of the deserialized, embedded message, with an\\nadditional field `@type` which contains the type URL. Example:\\n\\n    package google.profile;\\n    message Person {\\n      string first_name = 1;\\n      string last_name = 2;\\n    }\\n\\n    {\\n      \\\"@type\\\": \\\"type.googleapis.com/google.profile.Person\\\",\\n      \\\"firstName\\\": \\u003cstring\\u003e,\\n      \\\"lastName\\\": \\u003cstring\\u003e\\n    }\\n\\nIf the embedded message type is well-known and has a custom JSON\\nrepresentation, that representation will be embedded adding a field\\n`value` which holds the custom JSON in addition to the `@type`\\nfield. Example (for message [google.protobuf.Duration][]):\\n\\n    {\\n      \\\"@type\\\": \\\"type.googleapis.com/google.protobuf.Duration\\\",\\n      \\\"value\\\": \\\"1.212s\\\"\\n    }\"\n    },\n    \"protobufNullValue\": {\n      \"type\": \"string\",\n      \"enum\": [\n        \"NULL_VALUE\"\n      ],\n      \"default\": \"NULL_VALUE\",\n      \"description\": \"`NullValue` is a singleton enumeration to represent the null value for the\\n`Value` type union.\\n\\n The JSON representation for `NullValue` is JSON `null`.\\n\\n - NULL_VALUE: Null value.\"\n    },\n    \"v1AddBinaryDataRequest\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"event_id\": {\n          \"type\": \"string\",\n          \"description\": \"The unique event identifier.\"\n        },\n        \"binary_data_name\": {\n          \"type\": \"string\",\n          \"description\": \"The binary data key.\"\n        },\n        \"binary_data\": {\n          \"type\": \"string\",\n          \"format\": \"byte\",\n          \"description\": \"The binary data.\"\n        }\n      },\n      \"description\": \"Request to attach binary data to the event.\"\n    },\n    \"v1AddBinaryDataResponse\": {\n      \"type\": \"object\",\n      \"description\": \"Response after attaching binary data to the event.\"\n    },\n    \"v1AddDocumentRequest\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"event_id\": {\n          \"type\": \"string\",\n          \"description\": \"The unique event identifier.\"\n        },\n        \"document_name\": {\n          \"type\": \"string\",\n          \"description\": \"The event-unique document name.\"\n        },\n        \"text\": {\n          \"type\": \"string\",\n          \"description\": \"The document text.\"\n        }\n      },\n      \"description\": \"Request to add a document to an event.\"\n    },\n    \"v1AddDocumentResponse\": {\n      \"type\": \"object\",\n      \"description\": \"Response from the service when adding a document.\"\n    },\n    \"v1AddLabelsRequest\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"event_id\": {\n          \"type\": \"string\",\n          \"description\": \"The unique event identifier.\"\n        },\n        \"document_name\": {\n          \"type\": \"string\",\n          \"description\": \"The document name on the event.\"\n        },\n        \"index_name\": {\n          \"type\": \"string\",\n          \"description\": \"A document-unique identifier for the index to create on the document.\"\n        },\n        \"json_labels\": {\n          \"$ref\": \"#/definitions/v1JsonLabels\",\n          \"description\": \"JsonLabels, which are a generic JSON object that should have the\\nstart_index and end_index fields as well as any other fields that\\nthe application requires.\"\n        },\n        \"other_labels\": {\n          \"$ref\": \"#/definitions/protobufAny\",\n          \"description\": \"Experimental, a different type of serialized message, which the Events\\nservice will store and return directly to clients.\"\n        },\n        \"no_key_validation\": {\n          \"type\": \"boolean\",\n          \"format\": \"boolean\",\n          \"description\": \"Set to \\\"true\\\" if the client validates label field keys so to ensure that no reserved key names\\noccur. The key names that are reserved are \\\"text\\\", \\\"document\\\", and \\\"location\\\".\"\n        }\n      },\n      \"description\": \"Request to add labels to a document.\"\n    },\n    \"v1AddLabelsResponse\": {\n      \"type\": \"object\",\n      \"description\": \"Response for adding labels to the events service.\"\n    },\n    \"v1AddMetadataRequest\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"event_id\": {\n          \"type\": \"string\",\n          \"description\": \"The unique event identifier.\"\n        },\n        \"key\": {\n          \"type\": \"string\",\n          \"title\": \"The key for the metadata entry\"\n        },\n        \"value\": {\n          \"type\": \"string\",\n          \"description\": \"The value for the metadata entry.\"\n        }\n      },\n      \"title\": \"Request to add a metadata entry to the events service\"\n    },\n    \"v1AddMetadataResponse\": {\n      \"type\": \"object\",\n      \"description\": \"Response from the server for adding a metadata entry.\"\n    },\n    \"v1CloseEventResponse\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"deleted\": {\n          \"type\": \"boolean\",\n          \"format\": \"boolean\",\n          \"description\": \"If the event was deleted after a close.\"\n        }\n      },\n      \"description\": \"Response from the service for closing events.\"\n    },\n    \"v1GetAllBinaryDataNamesResponse\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"binary_data_names\": {\n          \"type\": \"array\",\n          \"items\": {\n            \"type\": \"string\"\n          }\n        }\n      },\n      \"description\": \"Response of all the binary names on the event.\"\n    },\n    \"v1GetAllDocumentNamesResponse\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"document_names\": {\n          \"type\": \"array\",\n          \"items\": {\n            \"type\": \"string\"\n          },\n          \"description\": \"Repeated field containing all documents for the event.\"\n        }\n      },\n      \"description\": \"Response of all the document names on an event.\"\n    },\n    \"v1GetAllMetadataResponse\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"metadata\": {\n          \"type\": \"object\",\n          \"additionalProperties\": {\n            \"type\": \"string\"\n          },\n          \"title\": \"The metadata map for the event\"\n        }\n      },\n      \"description\": \"Response from the server for all metadata associated with an event.\"\n    },\n    \"v1GetBinaryDataResponse\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"binary_data\": {\n          \"type\": \"string\",\n          \"format\": \"byte\",\n          \"description\": \"The binary data.\"\n        }\n      }\n    },\n    \"v1GetDocumentTextResponse\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"text\": {\n          \"type\": \"string\",\n          \"description\": \"The text of the document.\"\n        }\n      },\n      \"description\": \"Response for getting the document text.\"\n    },\n    \"v1GetLabelIndicesInfoResponse\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"label_index_infos\": {\n          \"type\": \"array\",\n          \"items\": {\n            \"$ref\": \"#/definitions/GetLabelIndicesInfoResponseLabelIndexInfo\"\n          },\n          \"description\": \"Info about each label index on the document.\"\n        }\n      },\n      \"description\": \"Response of information about the label indices on a document.\"\n    },\n    \"v1GetLabelsResponse\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"json_labels\": {\n          \"$ref\": \"#/definitions/v1JsonLabels\",\n          \"description\": \"If the original were JsonLabels.\"\n        },\n        \"other_labels\": {\n          \"$ref\": \"#/definitions/protobufAny\",\n          \"description\": \"If the original were other_labels.\"\n        }\n      },\n      \"description\": \"The response for retrieving labels from an event and document.\"\n    },\n    \"v1JsonLabels\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"is_distinct\": {\n          \"type\": \"boolean\",\n          \"format\": \"boolean\",\n          \"description\": \"Whether the label index is distinct, i.e. only consists of non-overlapping,\\nnon-empty spans of text.\"\n        },\n        \"labels\": {\n          \"type\": \"array\",\n          \"items\": {\n            \"type\": \"object\"\n          },\n          \"description\": \"The labels, which are dynamic JSON objects and must contain the number\\nfields \\\"start_index\\\" and \\\"end_index\\\". Any other fields are application-\\nspecific and dynamic.\"\n        }\n      },\n      \"description\": \"A Label Index of dynamic Labels, which are client/processor specified data\\nobjects containing information about an area of text.\"\n    },\n    \"v1OpenEventRequest\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"event_id\": {\n          \"type\": \"string\",\n          \"description\": \"The globally unique event identifier.\"\n        },\n        \"only_create_new\": {\n          \"type\": \"boolean\",\n          \"format\": \"boolean\",\n          \"description\": \"Only create a new event, failing if the event already exists.\"\n        },\n        \"lease_duration\": {\n          \"type\": \"string\",\n          \"description\": \"Optional, how long the lease is valid for.\"\n        }\n      },\n      \"description\": \"A request to open an event, retrieves a lease that prevents the service from\\nde-allocating the event.\"\n    },\n    \"v1OpenEventResponse\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"created\": {\n          \"type\": \"boolean\",\n          \"format\": \"boolean\",\n          \"description\": \"Whether the service created a new event.\"\n        },\n        \"lease_id\": {\n          \"type\": \"integer\",\n          \"format\": \"int32\",\n          \"description\": \"Optional, if the lease has a duration, an identifier which can be used to\\ncede the lease, which will prevent the lease from being ceded twice.\"\n        }\n      },\n      \"description\": \"The response from the service for the open event endpoint.\"\n    }\n  }\n}\n" 
Processing = "{\n  \"swagger\": \"2.0\",\n  \"info\": {\n    \"title\": \"mtap/api/v1/processing.proto\",\n    \"version\": \"version not set\"\n  },\n  \"schemes\": [\n    \"http\",\n    \"https\"\n  ],\n  \"consumes\": [\n    \"application/json\"\n  ],\n  \"produces\": [\n    \"application/json\"\n  ],\n  \"paths\": {\n    \"/v1/processors/{processor_id}/info\": {\n      \"get\": {\n        \"summary\": \"Gets information about the processor.\",\n        \"operationId\": \"GetInfo\",\n        \"responses\": {\n          \"200\": {\n            \"description\": \"A successful response.\",\n            \"schema\": {\n              \"$ref\": \"#/definitions/v1GetInfoResponse\"\n            }\n          }\n        },\n        \"parameters\": [\n          {\n            \"name\": \"processor_id\",\n            \"description\": \"The identifier of the processor, currently is unused but may be eventually used for routing\\nif multiple processors are hosted on the same port / endpoint.\",\n            \"in\": \"path\",\n            \"required\": true,\n            \"type\": \"string\"\n          }\n        ],\n        \"tags\": [\n          \"Processor\"\n        ]\n      }\n    },\n    \"/v1/processors/{processor_id}/process/{event_id}\": {\n      \"post\": {\n        \"summary\": \"Processes an event.\",\n        \"operationId\": \"Process\",\n        \"responses\": {\n          \"200\": {\n            \"description\": \"A successful response.\",\n            \"schema\": {\n              \"$ref\": \"#/definitions/v1ProcessResponse\"\n            }\n          }\n        },\n        \"parameters\": [\n          {\n            \"name\": \"processor_id\",\n            \"description\": \"The identifier of the processor that is being called, currently is unused\\nbut may be eventually used for routing if multiple processors are hosted\\non the same port / endpoint.\",\n            \"in\": \"path\",\n            \"required\": true,\n            \"type\": \"string\"\n          },\n          {\n            \"name\": \"event_id\",\n            \"description\": \"The identifier of the event to process.\",\n            \"in\": \"path\",\n            \"required\": true,\n            \"type\": \"string\"\n          },\n          {\n            \"name\": \"body\",\n            \"in\": \"body\",\n            \"required\": true,\n            \"schema\": {\n              \"$ref\": \"#/definitions/v1ProcessRequest\"\n            }\n          }\n        ],\n        \"tags\": [\n          \"Processor\"\n        ]\n      }\n    },\n    \"/v1/processors/{processor_id}/stats\": {\n      \"get\": {\n        \"summary\": \"Gets globally-aggregated statistics about the processor.\",\n        \"operationId\": \"GetStats\",\n        \"responses\": {\n          \"200\": {\n            \"description\": \"A successful response.\",\n            \"schema\": {\n              \"$ref\": \"#/definitions/v1GetStatsResponse\"\n            }\n          }\n        },\n        \"parameters\": [\n          {\n            \"name\": \"processor_id\",\n            \"description\": \"The deployment identifier of the processor.\",\n            \"in\": \"path\",\n            \"required\": true,\n            \"type\": \"string\"\n          }\n        ],\n        \"tags\": [\n          \"Processor\"\n        ]\n      }\n    }\n  },\n  \"definitions\": {\n    \"protobufNullValue\": {\n      \"type\": \"string\",\n      \"enum\": [\n        \"NULL_VALUE\"\n      ],\n      \"default\": \"NULL_VALUE\",\n      \"description\": \"`NullValue` is a singleton enumeration to represent the null value for the\\n`Value` type union.\\n\\n The JSON representation for `NullValue` is JSON `null`.\\n\\n - NULL_VALUE: Null value.\"\n    },\n    \"v1CreatedIndex\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"document_name\": {\n          \"type\": \"string\",\n          \"description\": \"The document's name where the index was created.\"\n        },\n        \"index_name\": {\n          \"type\": \"string\",\n          \"description\": \"The name of the label index that was created.\"\n        }\n      },\n      \"description\": \"The name of a newly created label index during a process call.\"\n    },\n    \"v1GetInfoResponse\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"metadata\": {\n          \"type\": \"object\"\n        }\n      },\n      \"description\": \"Processor information response, currently does not include anything besides\\nthe processor name. May eventually be extended to reflect more processor\\ninformation like documentation, required inputs (label indices and\\nparameters), and outputs (label indices and parameters), etc.\"\n    },\n    \"v1GetStatsResponse\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"processed\": {\n          \"type\": \"integer\",\n          \"format\": \"int32\",\n          \"description\": \"The number of documents processed.\"\n        },\n        \"failures\": {\n          \"type\": \"integer\",\n          \"format\": \"int32\",\n          \"description\": \"The number of documents that have failed to process.\"\n        },\n        \"timing_stats\": {\n          \"type\": \"object\",\n          \"additionalProperties\": {\n            \"$ref\": \"#/definitions/v1TimerStats\"\n          },\n          \"description\": \"Statistics for each timer.\"\n        }\n      },\n      \"description\": \"Processor statistics response.\"\n    },\n    \"v1ProcessRequest\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"processor_id\": {\n          \"type\": \"string\",\n          \"description\": \"The identifier of the processor that is being called, currently is unused\\nbut may be eventually used for routing if multiple processors are hosted\\non the same port / endpoint.\"\n        },\n        \"event_id\": {\n          \"type\": \"string\",\n          \"description\": \"The identifier of the event to process.\"\n        },\n        \"params\": {\n          \"type\": \"object\",\n          \"description\": \"A dynamic JSON object of runtime parameters that the processor will use.\"\n        }\n      },\n      \"description\": \"A request for a processor to run on a specific event.\"\n    },\n    \"v1ProcessResponse\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"timing_info\": {\n          \"type\": \"object\",\n          \"additionalProperties\": {\n            \"type\": \"string\"\n          },\n          \"description\": \"Processor-specific timings of different operations. Includes a \\\"process\\\"\\ntime for total time taken.\"\n        },\n        \"result\": {\n          \"type\": \"object\",\n          \"description\": \"The dynamic JSON object result returned by the processor.\"\n        },\n        \"created_indices\": {\n          \"type\": \"array\",\n          \"items\": {\n            \"$ref\": \"#/definitions/v1CreatedIndex\"\n          },\n          \"description\": \"All label indices that were created on the event during processing.\"\n        }\n      },\n      \"description\": \"The response after a processor completes processing of an event.\"\n    },\n    \"v1TimerStats\": {\n      \"type\": \"object\",\n      \"properties\": {\n        \"mean\": {\n          \"type\": \"string\",\n          \"description\": \"The mean duration.\"\n        },\n        \"std\": {\n          \"type\": \"string\",\n          \"description\": \"The standard deviation of the duration.\"\n        },\n        \"max\": {\n          \"type\": \"string\",\n          \"description\": \"The maximum duration.\"\n        },\n        \"min\": {\n          \"type\": \"string\",\n          \"description\": \"The minimum duration.\"\n        },\n        \"sum\": {\n          \"type\": \"string\",\n          \"description\": \"The sum of durations.\"\n        }\n      },\n      \"description\": \"A set of globally-aggregated measurements for a specific processor timer\\nacross all requests.\"\n    }\n  }\n}\n" 
)

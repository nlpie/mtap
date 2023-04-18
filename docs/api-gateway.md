---
layout: default
title: RESTful API Gateway
nav_index: 3
---
# RESTful API Gateway

Running and using the MTAP API Gateway.

## Configuring the API Gateway

The API Gateway supports either specifying the addresses that it re-hosts in
configuration, or using service discovery to find services to re-host.

To configure the API Gateway we will create a ``mtapConfig.yaml`` file in the
working directory of the API Gateway binary.


#### Specified addresses:

```yaml
discovery: consul
consul:
  host: localhost
  port: 8500
  scheme: http
  # Python uses {python_naming_scheme}:address[:port][,address[:port],...] as grpc targets
  python_naming_scheme: ipv4

gateway:
  port: 8080
  refresh_interval: 10
  events: localhost:9090
  processors:
    - Identifier: mtap-example-processor-python
      Endpoint: localhost:9091
```


#### Using service discovery:

```yaml
discovery: consul
consul:
  host: localhost
  port: 8500
  scheme: http
  # Python uses {python_naming_scheme}:address[:port][,address[:port],...] as grpc targets
  python_naming_scheme: ipv4

gateway:
  port: 8080
  refresh_interval: 10
  events: null
  processors: []
```


## Running the API Gateway

To launch the API Gateway, use one of the provided executables:

```bash
./mtap-gateway-v{{ site.version }}-linux-amd64
```

## Using the Events API Gateway

### Creating an event

```bash
curl -X POST localhost:8080/v1/events/1
```

### Setting and retrieving metadata

```bash
curl -d '{"value":"Value"}' -H "Content-Type: application/json" -X POST localhost:8080/v1/events/1/metadata/key
```

Getting all metadata:

```bash
curl -X GET localhost:8080/v1/events/1/metadata
```

### Adding a document

```bash
curl -d '{"text":"This is some document text."}' -H "Content-Type: application/json" -X POST localhost:8080/v1/events/1/documents/plaintext
```

### Retrieving document text

```bash
curl -X GET localhost:8080/v1/events/1/documents/plaintext
```

### Adding labels

Create a file, labels.json:

```json
{
  "json_labels": {
    "is_distinct": true,
    "labels": [
      { "start_index": 0, "end_index": 5, "x": "value"},
      { "start_index": 6, "end_index": 20, "x": "value2"}
    ]
  }
}
```

Uploading the labels:

```bash
curl -d @labels.json -H "Content-Type: application/json" \
-X POST localhost:8080/v1/events/1/documents/plaintext/labels/new_index
```

### Retrieving Labels

```bash
curl -X GET localhost:8080/v1/events/1/documents/plaintext/labels/new_index
```

## Using the processing API Gateway

### Listing all available processors

```bash
curl -X GET localhost:8080/v1/processors/
```

### Calling an event processor

```bash
curl -X POST localhost:8080/v1/processors/{processor_id}/process/{event_id}
```

### Calling a document processor

```bash
curl -d '{"params": {"document_name": "plaintext"}}' -H "Content-Type: application/json" \
-X POST localhost:8080/v1/processors/{processor_id}/process/{event_id}
```

## APIs

<script>
window.onload = function() {
  window.ui = SwaggerUIBundle({
    urls: [
        {url: "/assets/json/events.swagger.json", name: "Events"},
        {url: "/assets/json/processing.swagger.json", name: "Processing"}
    ],
    dom_id: '#swagger-ui',
    deepLinking: true,
    presets: [
      SwaggerUIBundle.presets.apis,
      SwaggerUIStandalonePreset
    ],
    plugins: [
      SwaggerUIBundle.plugins.DownloadUrl,
      SwaggerUIBundle.plugins.Topbar
    ],
    layout: "StandaloneLayout",
    tryItOutEnabled: false
  });
};
</script>
<div id="swagger-ui"></div>
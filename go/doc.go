/*
 * Copyright (c) Regents of the University of Minnesota.
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

//go:generate protoc -I/usr/local/include -I../proto -Ithird_party/googleapis --go_out . --go_opt paths=source_relative --go-grpc_out . --go-grpc_opt paths=source_relative ../proto/mtap/api/v1/events.proto
//go:generate protoc -I/usr/local/include -I../proto -Ithird_party/googleapis --grpc-gateway_out . --grpc-gateway_opt logtostderr=true --grpc-gateway_opt paths=source_relative ../proto/mtap/api/v1/events.proto
//go:generate protoc -I/usr/local/include -I../proto -Ithird_party/googleapis --openapiv2_out . --openapiv2_opt logtostderr=true ../proto/mtap/api/v1/events.proto
//go:generate protoc -I/usr/local/include -I../proto -Ithird_party/googleapis --go_out . --go_opt paths=source_relative --go-grpc_out . --go-grpc_opt paths=source_relative ../proto/mtap/api/v1/processing.proto
//go:generate protoc -I/usr/local/include -I../proto -Ithird_party/googleapis --grpc-gateway_out . --grpc-gateway_opt logtostderr=true --grpc-gateway_opt paths=source_relative ../proto/mtap/api/v1/processing.proto
//go:generate protoc -I/usr/local/include -I../proto -Ithird_party/googleapis --openapiv2_out . --openapiv2_opt logtostderr=true ../proto/mtap/api/v1/processing.proto
//go:generate protoc -I/usr/local/include -I../proto -Ithird_party/googleapis --go_out . --go_opt paths=source_relative --go-grpc_out . --go-grpc_opt paths=source_relative ../proto/mtap/api/v1/pipeline.proto
//go:generate protoc -I/usr/local/include -I../proto -Ithird_party/googleapis --grpc-gateway_out . --grpc-gateway_opt logtostderr=true --grpc-gateway_opt paths=source_relative ../proto/mtap/api/v1/pipeline.proto
//go:generate protoc -I/usr/local/include -I../proto -Ithird_party/googleapis --openapiv2_out . --openapiv2_opt logtostderr=true ../proto/mtap/api/v1/pipeline.proto
package mtap

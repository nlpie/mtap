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

//go:generate protoc -I/usr/local/include -I$GOPATH/src -I../proto -I$GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis --go_out=plugins=grpc,paths=source_relative:. ../proto/nlpnewt/api/v1/labels.proto
//go:generate protoc -I/usr/local/include -I$GOPATH/src -I../proto -I$GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis --go_out=plugins=grpc,paths=source_relative:. ../proto/nlpnewt/api/v1/events.proto
//go:generate protoc -I/usr/local/include -I$GOPATH/src -I../proto -I$GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis --grpc-gateway_out=logtostderr=true,grpc_api_configuration=../proto/nlpnewt/api/v1/events.yaml:. ../proto/nlpnewt/api/v1/events.proto
//go:generate protoc -I/usr/local/include -I$GOPATH/src -I../proto -I$GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis --go_out=plugins=grpc,paths=source_relative:. ../proto/nlpnewt/api/v1/processing.proto
//go:generate protoc -I/usr/local/include -I$GOPATH/src -I../proto -I$GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis --grpc-gateway_out=logtostderr=true,grpc_api_configuration=../proto/nlpnewt/api/v1/processing.yaml:. ../proto/nlpnewt/api/v1/processing.proto
package nlpnewt

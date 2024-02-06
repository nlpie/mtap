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

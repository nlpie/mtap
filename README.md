# nlpnewt

## natural language processing new environment (working title)

Repository for storing the prototypes and work-in-progress files for the nlp processing re-architecting.

# building _pb2\[_grpc\] files for python

```bash
cd python
python setup.py build_py
```


# building proto files for grpc-gateway-go

First install go, then follow installation instructions on https://github.com/grpc-ecosystem/grpc-gateway

First time setup:
```bash
go get -u github.com/grpc-ecosystem/grpc-gateway/protoc-gen-grpc-gateway
go get -u github.com/grpc-ecosystem/grpc-gateway/protoc-gen-swagger
go get -u github.com/golang/protobuf/protoc-gen-go
```

```bash
cd go
go generate ./...
```

# building python documentation

```bash
pip3 install sphinx sphinx_rtd_theme
cd python/docs
make html 
```

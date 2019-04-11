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

```bash
cd go
go generate ./...
```

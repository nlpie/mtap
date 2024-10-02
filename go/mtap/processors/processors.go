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

package processors

import (
	"context"
	"encoding/json"
	"net/http"

	"github.com/golang/glog"
	"github.com/gorilla/mux"
	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	ApiV1 "github.com/nlpie/mtap/go/mtap/api/v1"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/protobuf/encoding/protojson"
)

type Gateway struct {
	mux      *runtime.ServeMux
	ctx      context.Context
	cancel   context.CancelFunc
	isManual bool
}

type Server struct {
	Dispatcher          *mux.Router
	processors          map[string]*Gateway
	pipelines           map[string]*Gateway
	ctx                 context.Context
	grpcEnableHttpProxy bool
}

type processorInfo struct {
	Identifier string
}

type processorsResponse struct {
	Processors []processorInfo
}

type Config struct {
	Processors          []ServiceEndpoint
	Pipelines           []ServiceEndpoint
	GrpcEnableHttpProxy bool
}

type ServiceEndpoint struct {
	Identifier string
	Endpoint   string
}

func NewProcessorsServer(ctx context.Context, config *Config) (*Server, error) {
	ps := &Server{
		Dispatcher: mux.NewRouter(),
		processors: make(map[string]*Gateway),
		pipelines:  make(map[string]*Gateway),
		ctx:        ctx,
	}
	ps.Dispatcher.HandleFunc("/v1/processors", ps.handleProcessors).Methods("GET")
	ps.Dispatcher.PathPrefix("/v1/processors/{Identifier}").HandlerFunc(ps.dispatchToProcessor)
	ps.Dispatcher.PathPrefix("/v1/pipeline/{Identifier}").HandlerFunc(ps.dispatchToPipeline)

	for _, processor := range config.Processors {
		pg, err := ps.newProcessorGateway(processor)
		if err != nil {
			return nil, err
		}
		ps.processors[processor.Identifier] = pg
	}

	for _, pipeline := range config.Pipelines {
		pg, err := ps.newPipelineGateway(pipeline)
		if err != nil {
			return nil, err
		}
		ps.pipelines[pipeline.Identifier] = pg
	}

	return ps, nil
}

func (ps *Server) handleProcessors(w http.ResponseWriter, r *http.Request) {
	glog.V(3).Info("\"processors\" endpoint request")
	processors := make([]processorInfo, 0, len(ps.processors))
	for k := range ps.processors {
		processors = append(processors, processorInfo{Identifier: k})
	}
	response := processorsResponse{Processors: processors}
	js, err := json.Marshal(response)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	_, err = w.Write(js)
	if err != nil {
		glog.Errorf("Error writing processors response: %v", err)
	}
}

func (ps *Server) dispatchToProcessor(w http.ResponseWriter, r *http.Request) {
	glog.V(3).Info("Dispatching a processor gateway request")
	vars := mux.Vars(r)
	identifier := vars["Identifier"]
	p, prs := ps.processors[identifier]
	if prs {
		p.mux.ServeHTTP(w, r)
	} else {
		http.NotFound(w, r)
	}
}

func (ps *Server) dispatchToPipeline(w http.ResponseWriter, r *http.Request) {
	glog.V(3).Info("Dispatching a pipeline gateway request")
	vars := mux.Vars(r)
	identifier := vars["Identifier"]
	p, prs := ps.pipelines[identifier]
	if prs {
		p.mux.ServeHTTP(w, r)
	} else {
		http.NotFound(w, r)
	}
}

func (ps *Server) newProcessorGateway(manualProcessor ServiceEndpoint) (*Gateway, error) {
	glog.V(2).Infof("Starting new processor gateway for service: %v with address: %v", manualProcessor.Identifier, manualProcessor.Endpoint)
	gwmux := runtime.NewServeMux(runtime.WithMarshalerOption(runtime.MIMEWildcard, &runtime.JSONPb{MarshalOptions: protojson.MarshalOptions{EmitUnpopulated: true, UseProtoNames: true}}))
	ctx, cancel := context.WithCancel(ps.ctx)

	err := ApiV1.RegisterProcessorHandlerFromEndpoint(
		ctx,
		gwmux,
		manualProcessor.Endpoint,
		ps.createDialOptions())

	if err != nil {
		cancel()
		return nil, err
	}
	gateway := Gateway{mux: gwmux, ctx: ctx, cancel: cancel, isManual: true}
	return &gateway, nil
}

func (ps *Server) createDialOptions() []grpc.DialOption {
	dialOptions := []grpc.DialOption{grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithDefaultServiceConfig(`{"loadBalancingPolicy":"round_robin"}`)}
	if !ps.grpcEnableHttpProxy {
		dialOptions = append(dialOptions, grpc.WithNoProxy())
	}
	return dialOptions
}

func (ps *Server) newPipelineGateway(ep ServiceEndpoint) (*Gateway, error) {
	glog.V(2).Infof("Starting new pipeline gateway for service: %v with address: %v", ep.Identifier, ep.Endpoint)
	gwmux := runtime.NewServeMux(runtime.WithMarshalerOption(runtime.MIMEWildcard, &runtime.JSONPb{MarshalOptions: protojson.MarshalOptions{EmitUnpopulated: true, UseProtoNames: true}}))
	ctx, cancel := context.WithCancel(ps.ctx)

	err := ApiV1.RegisterPipelineHandlerFromEndpoint(
		ctx,
		gwmux,
		ep.Endpoint,
		ps.createDialOptions())

	if err != nil {
		cancel()
		return nil, err
	}
	gateway := Gateway{mux: gwmux, ctx: ctx, cancel: cancel, isManual: true}
	return &gateway, nil
}

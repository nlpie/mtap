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

package processors

import (
	"context"
	"encoding/json"
	"github.com/golang/glog"
	"github.com/gorilla/mux"
	"github.com/grpc-ecosystem/grpc-gateway/runtime"
	"github.com/hashicorp/consul/api"
	"github.com/nlpie/mtap/go/mtap/api/v1"
	"golang.org/x/sync/semaphore"
	"google.golang.org/grpc"
	"net/http"
	"strconv"
	"time"
)

type processorGateway struct {
	mux      *runtime.ServeMux
	ctx      context.Context
	cancel   context.CancelFunc
	isManual bool
}

// listens for new processors from the consul server.
type ProcessorsServer struct {
	Dispatcher          *mux.Router
	processors          map[string]*processorGateway
	t                   *time.Ticker
	ctx                 context.Context
	client              *api.Client
	authority           string
	updating            bool
	semaphore           *semaphore.Weighted
	grpcEnableHttpProxy bool
}

type processorInfo struct {
	Identifier string
}

type processorsResponse struct {
	Processors []processorInfo
}

type Config struct {
	ConsulAddress       string
	ConsulPort          int
	RefreshInterval     time.Duration
	ManualProcessors    []ManualProcessor
	GrpcEnableHttpProxy bool
}

type ManualProcessor struct {
	Identifier string
	Endpoint   string
}

func NewProcessorsServer(ctx context.Context, config *Config) (*ProcessorsServer, error) {
	ps := &ProcessorsServer{
		Dispatcher: mux.NewRouter(),
		processors: make(map[string]*processorGateway),
		t:          time.NewTicker(time.Second * config.RefreshInterval),
		authority:  config.ConsulAddress + ":" + strconv.Itoa(config.ConsulPort),
		ctx:        ctx,
		semaphore:  semaphore.NewWeighted(int64(1)),
	}
	ps.Dispatcher.HandleFunc("/v1/processors", ps.handleProcessors).Methods("GET")
	ps.Dispatcher.PathPrefix("/v1/processors/{Identifier}").HandlerFunc(ps.dispatchToProcessor)

	consulConfig := api.DefaultConfig()
	consulConfig.Address = config.ConsulAddress + ":" + strconv.Itoa(config.ConsulPort)

	client, err := api.NewClient(consulConfig)
	if err != nil {
		return nil, err
	}
	ps.client = client

	for _, manualProcessor := range config.ManualProcessors {
		pg, err := ps.newManualProcessorGateway(manualProcessor)
		if err != nil {
			return nil, err
		}
		ps.processors[manualProcessor.Identifier] = pg
	}

	ps.doUpdate()

	go ps.watcher()

	return ps, nil
}

func (ps *ProcessorsServer) handleProcessors(w http.ResponseWriter, r *http.Request) {
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

func (ps *ProcessorsServer) dispatchToProcessor(w http.ResponseWriter, r *http.Request) {
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

func (ps *ProcessorsServer) watcher() {
	for {
		select {
		case <-ps.ctx.Done():
			return
		case <-ps.t.C:
		}
		// do lookup, deregistering any processors that went away and adding any new ones.
		go ps.doUpdate()
	}
}

func (ps *ProcessorsServer) doUpdate() error {
	if !ps.semaphore.TryAcquire(1) {
		return nil
	}
	defer ps.semaphore.Release(1)

	glog.V(2).Info("Updating processor gateways")

	glog.V(3).Info("Retrieving processors from consul")
	services, _, err := ps.client.Catalog().Services(nil)
	if err != nil {
		glog.Warningf("Error getting processing services from consul %v", err)
		return err
	}
	availableProcessors := make([]string, 0, 10)
	for service, tags := range services {
		found := false
		for _, tag := range tags {
			if tag == "v1-mtap-processor" {
				found = true
			}
		}
		if !found {
			continue
		}
		entries, _, err := ps.client.Health().Service(
			service,
			"v1-mtap-processor",
			true,
			nil)
		if err != nil {
			glog.Errorf("Error getting processing services from consul %v", err)
			return err
		}

		for _, entry := range entries {
			service := entry.Service
			processorName := service.Service
			found := false
			for _, known := range availableProcessors {
				if known == processorName {
					found = true
				}
			}
			if !found {
				availableProcessors = append(availableProcessors, processorName)
			}
		}
	}

	processorsCopy := make(map[string]*processorGateway, len(ps.processors))
	for k, pg := range ps.processors {
		processorsCopy[k] = pg
	}

	glog.V(3).Info("Removing any expired processors")
	for k, pg := range ps.processors {
		if pg.isManual {
			continue
		}
		found := false
		for _, available := range availableProcessors {
			if k == available {
				found = true
				break
			}
		}
		if !found {
			glog.V(2).Infof("Removing processor gateway: %v", k)
			pg.cancel()
			delete(processorsCopy, k)
		}
	}

	glog.V(3).Info("Adding any new processors")
	for _, processor := range availableProcessors {
		found := false
		for existing, _ := range processorsCopy {
			if processor == existing {
				found = true
				break
			}
		}
		if !found {
			pg, err := ps.newProcessorGateway(processor)
			if err != nil {
				glog.Errorf("Unable to create new processor gateway: %v", err)
				continue
			}
			processorsCopy[processor] = pg
		}
	}
	ps.processors = processorsCopy
	glog.V(2).Info("Finished updating processor gateways")

	return nil
}

func (ps *ProcessorsServer) newManualProcessorGateway(manualProcessor ManualProcessor) (*processorGateway, error) {
	glog.V(2).Infof("Starting new processor gateway for service: %v with address: %v", manualProcessor.Identifier, manualProcessor.Endpoint)
	gwmux := runtime.NewServeMux(runtime.WithMarshalerOption(runtime.MIMEWildcard, &runtime.JSONPb{OrigName: true, EmitDefaults: true}))
	ctx, cancel := context.WithCancel(ps.ctx)

	err := mtap_api_v1.RegisterProcessorHandlerFromEndpoint(
		ctx,
		gwmux,
		manualProcessor.Endpoint,
		ps.createDialOptions())

	if err != nil {
		return nil, err
	}
	gateway := processorGateway{mux: gwmux, ctx: ctx, cancel: cancel, isManual: true}
	return &gateway, nil
}

func (ps *ProcessorsServer) createDialOptions() []grpc.DialOption {
	dialOptions := []grpc.DialOption{grpc.WithInsecure(), grpc.WithBalancerName("round_robin")}
	if !ps.grpcEnableHttpProxy {
		dialOptions = append(dialOptions, grpc.WithNoProxy())
	}
	return dialOptions
}

func (ps *ProcessorsServer) newProcessorGateway(pn string) (*processorGateway, error) {
	glog.V(2).Infof("Starting new processor gateway for service: %v", pn)
	gwmux := runtime.NewServeMux(runtime.WithMarshalerOption(runtime.MIMEWildcard, &runtime.JSONPb{OrigName: true, EmitDefaults: true}))
	ctx, cancel := context.WithCancel(ps.ctx)

	err := mtap_api_v1.RegisterProcessorHandlerFromEndpoint(
		ctx,
		gwmux,
		"consul://"+ps.authority+"/"+pn+"/v1-mtap-processor",
		ps.createDialOptions())

	if err != nil {
		return nil, err
	}
	gateway := processorGateway{mux: gwmux, ctx: ctx, cancel: cancel, isManual: false}
	return &gateway, nil
}

package processors

import (
	"context"
	"encoding/json"
	"github.com/golang/glog"
	"github.com/gorilla/mux"
	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	"github.com/hashicorp/consul/api"
	ApiV1 "github.com/nlpie/mtap/go/mtap/api/v1"
	"golang.org/x/sync/semaphore"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/protobuf/encoding/protojson"
	"net/http"
	"strconv"
	"time"
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
	ManualProcessors    []ServiceEndpoint
	ManualPipelines     []ServiceEndpoint
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
		pipelines: make(map[string]*Gateway),
		t:          time.NewTicker(time.Second * config.RefreshInterval),
		authority:  config.ConsulAddress + ":" + strconv.Itoa(config.ConsulPort),
		ctx:        ctx,
		semaphore:  semaphore.NewWeighted(int64(1)),
	}
	ps.Dispatcher.HandleFunc("/v1/processors", ps.handleProcessors).Methods("GET")
	ps.Dispatcher.PathPrefix("/v1/processors/{Identifier}").HandlerFunc(ps.dispatchToProcessor)
	ps.Dispatcher.PathPrefix("/v1/pipeline/{Identifier}").HandlerFunc(ps.dispatchToPipeline)

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

	for _, manualPipeline := range config.ManualPipelines {
		pg, err := ps.newManualPipelineGateway(manualPipeline)
		if err != nil {
			return nil, err
		}
		ps.pipelines[manualPipeline.Identifier] = pg
	}

	ps.doUpdate()

	go ps.watcher()

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

func (ps *Server) watcher() {
	for {
		select {
		case <-ps.ctx.Done():
			return
		case <-ps.t.C:
		}
		// do lookup, deregistering any processors that went away and adding any new ones.
		ps.doUpdate()
	}
}

func (ps *Server) doUpdate() {
	if !ps.semaphore.TryAcquire(1) {
		return
	}
	defer ps.semaphore.Release(1)

	glog.V(2).Info("Updating processor gateways")

	glog.V(3).Info("Retrieving processors from consul")
	services, _, err := ps.client.Catalog().Services(nil)
	if err != nil {
		glog.Warningf("Error getting processing services from consul %v", err)
		return
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
			return
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

	processorsCopy := make(map[string]*Gateway, len(ps.processors))
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
}

func (ps *Server) newManualProcessorGateway(manualProcessor ServiceEndpoint) (*Gateway, error) {
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

func (ps *Server) newProcessorGateway(pn string) (*Gateway, error) {
	glog.V(2).Infof("Starting new processor gateway for service: %v", pn)
	gwmux := runtime.NewServeMux(runtime.WithMarshalerOption(runtime.MIMEWildcard, &runtime.JSONPb{MarshalOptions: protojson.MarshalOptions{EmitUnpopulated: true, UseProtoNames: true}}))
	ctx, cancel := context.WithCancel(ps.ctx)

	err := ApiV1.RegisterProcessorHandlerFromEndpoint(
		ctx,
		gwmux,
		"consul://"+ps.authority+"/"+pn+"/v1-mtap-processor",
		ps.createDialOptions())

	if err != nil {
		cancel()
		return nil, err
	}
	gateway := Gateway{mux: gwmux, ctx: ctx, cancel: cancel, isManual: false}
	return &gateway, nil
}

func (ps *Server) newManualPipelineGateway(ep ServiceEndpoint) (*Gateway, error) {
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

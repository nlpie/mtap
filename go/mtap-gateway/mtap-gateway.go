package main

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"github.com/golang/glog"
	"github.com/gorilla/mux"
	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	ApiV1 "github.com/nlpie/mtap/go/mtap/api/v1"
	_ "github.com/nlpie/mtap/go/mtap/consul"
	"github.com/nlpie/mtap/go/mtap/processors"
	"github.com/spf13/cast"
	"github.com/spf13/viper"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/protobuf/encoding/protojson"
	"gopkg.in/yaml.v3"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"time"
)

type listFlag []string

func (i *listFlag) String() string { return "" }

func (i *listFlag) Set(value string) error {
	*i = append(*i, value)
	return nil
}

type PipelineConfig struct {
	Components []PipelineProcessor
}

type PipelineProcessor struct {
	Name    string
	Address string
}

var processorNames listFlag
var processorHosts listFlag

var pipelineConfigs listFlag

func run() error {
	glog.V(1).Infoln("Starting MTAP API Gateway")

	ctx := context.Background()
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()

	consulPort := viper.GetInt("consul.port")
	consulHost := viper.GetString("consul.host")
	consulAddr := consulHost + ":" + strconv.Itoa(consulPort)

	m := mux.NewRouter()

	config := processors.Config{
		ConsulAddress:       consulHost,
		ConsulPort:          consulPort,
		RefreshInterval:     viper.GetDuration("gateway.refresh_interval"),
		GrpcEnableHttpProxy: viper.GetBool("grpc.enable_proxy"),
	}

	err := viper.UnmarshalKey("gateway.processors", &config.ManualProcessors)
	if err != nil {
		err = nil
	}

	if len(processorNames) != len(processorHosts) {
		return errors.New("unequal number of --name and --host processor flags")
	}

	for i, s := range processorNames {
		config.ManualProcessors = append(config.ManualProcessors, processors.ManualProcessor{
			Identifier: s,
			Endpoint:   processorHosts[i],
		})
	}

	for _, s := range pipelineConfigs {
		data, err := os.ReadFile(s)
		if err != nil {
			glog.Errorf("Error reading pipeline config file %q: %v", s, err)
			panic(1)
		}
		conf := PipelineConfig{}
		err = yaml.Unmarshal(data, &conf)
		if err != nil {
			glog.Errorf("Error unmarshalling pipeline config file %q: %v", s, err)
			panic(1)
		}

		for _, pipelineProcessor := range conf.Components {
			config.ManualProcessors = append(config.ManualProcessors, processors.ManualProcessor{
				Identifier: pipelineProcessor.Name,
				Endpoint:   pipelineProcessor.Address,
			})
		}
	}

	server, err := processors.NewProcessorsServer(ctx, &config)
	if err != nil {
		return err
	}
	m.PathPrefix("/v1/processors").Handler(server.Dispatcher)

	gwmux := runtime.NewServeMux(runtime.WithMarshalerOption(runtime.MIMEWildcard,
		&runtime.JSONPb{MarshalOptions: protojson.MarshalOptions{EmitUnpopulated: true, UseProtoNames: true}}))
	eventsLookup := viper.Get("gateway.events")
	var eventsAddr string
	if eventsLookup != nil {
		eventsAddr = cast.ToString(eventsLookup)
		glog.Infof("Using events address: %s", eventsAddr)
	} else {
		eventsAddr = fmt.Sprintf("consul://%s/mtap-events/v1", consulAddr)
		glog.Info("Using consul service discovery for events: ", eventsAddr)
	}
	err = ApiV1.RegisterEventsHandlerFromEndpoint(
		ctx,
		gwmux,
		eventsAddr,
		[]grpc.DialOption{grpc.WithTransportCredentials(insecure.NewCredentials()),
			grpc.WithDefaultServiceConfig(`{"loadBalancingPolicy":"round_robin"}`)})
	if err != nil {
		return err
	}
	m.PathPrefix("/v1/events").Handler(gwmux)

	port := strconv.Itoa(viper.GetInt("gateway.port"))
	glog.V(1).Infoln("Serving on port " + port)

	srv := &http.Server{
		Addr:         ":" + port,
		WriteTimeout: time.Second * 15,
		ReadTimeout:  time.Second * 15,
		IdleTimeout:  time.Second * 60,
		Handler:      m,
	}

	go func() {
		if err := srv.ListenAndServe(); err != nil {
			glog.Error(err)
		}
	}()

	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt)

	<-c

	ctx2, cancel2 := context.WithTimeout(context.Background(), time.Second*10)
	defer cancel2()
	_ = srv.Shutdown(ctx2)
	_ = fmt.Errorf("shutting down")
	return nil
}

func main() {
	var mtapConfigFlag string
	var port int

	flag.StringVar(&mtapConfigFlag, "mtap-config", "",
		"The path to the mtap configuration file")
	flag.IntVar(&port, "port", -1, "The port to use")

	flag.Var(&processorNames, "name", "The name of a processor to host.")
	flag.Var(&processorHosts, "host", "The endpoint of a processor to host.")

	flag.Var(&pipelineConfigs, "pipeline-config", "A pipeline configuration file to pull processors from.")

	flag.Parse()

	viper.SetDefault("consul.host", "localhost")
	viper.SetDefault("consul.port", 8500)
	viper.SetDefault("gateway.port", 8080)
	viper.SetDefault("gateway.refresh_interval", 10)
	viper.SetDefault("gateway.events", nil)
	viper.SetDefault("gateway.processors", []processors.ManualProcessor{})
	viper.SetDefault("grpc.enable_proxy", false)

	mtapConfig, exists := os.LookupEnv("MTAP_CONFIG")
	if len(mtapConfigFlag) > 0 {
		mtapConfig = mtapConfigFlag
		exists = true
	}
	if exists {
		glog.V(2).Infof("Using config file: %s", mtapConfig)
		viper.SetConfigFile(mtapConfig)
	} else {
		viper.SetConfigName("mtapConfig")
		viper.AddConfigPath(".")
		viper.AddConfigPath("$HOME/.mtap")
		viper.AddConfigPath("/etc/mtap")
	}

	err := viper.ReadInConfig() // Find and read the config file
	if err != nil {             // Handle errors reading the config file
		// will use sensible defaults
		err = nil
	}

	if port != -1 {
		viper.Set("gateway.port", port)
	}

	defer glog.Flush()

	if err := run(); err != nil {
		glog.Fatal(err)
		os.Exit(1)
	}
}

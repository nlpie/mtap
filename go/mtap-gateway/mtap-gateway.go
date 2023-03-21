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

package main

import (
	"context"
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
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"time"
)

func run() error {
	glog.V(1).Infoln("Starting MTAP API Gateway")
	err := viper.ReadInConfig() // Find and read the config file
	if err != nil {             // Handle errors reading the config file
		// will use sensible defaults
		err = nil
	}

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

	var manualProcessors []processors.ManualProcessor
	err = viper.UnmarshalKey("gateway.processors", &manualProcessors)
	if err != nil {
		err = nil
	} else {
		config.ManualProcessors = manualProcessors
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
	flag.StringVar(&mtapConfigFlag, "mtap-config", "",
		"The path to the mtap configuration file")
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

	defer glog.Flush()

	if err := run(); err != nil {
		glog.Fatal(err)
	}
}

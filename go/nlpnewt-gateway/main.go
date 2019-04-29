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
	"github.com/benknoll-umn/nlpnewt/go/nlpnewt/api/v1"
	_ "github.com/benknoll-umn/nlpnewt/go/nlpnewt/consul"
	"github.com/benknoll-umn/nlpnewt/go/nlpnewt/processors"
	"github.com/golang/glog"
	"github.com/gorilla/handlers"
	"github.com/gorilla/mux"
	"github.com/grpc-ecosystem/grpc-gateway/runtime"
	"github.com/spf13/cast"
	"github.com/spf13/viper"
	"google.golang.org/grpc"
	"io"
	"net/http"
	"os"
	"strconv"
	"strings"
)

func serveSwagger(r *mux.Router) {
	m := mux.NewRouter()
	m.HandleFunc("/v1/processors/swagger.json",
		func(w http.ResponseWriter, req *http.Request) {
			_, err := io.Copy(w, strings.NewReader(nlpnewt_api_v1.Processing))
			if err != nil {
				w.WriteHeader(500)
			}
			w.Header().Set("Content-Type", "application/json")
		})

	m.HandleFunc("/v1/events/swagger.json",
		func(w http.ResponseWriter, req *http.Request) {
			_, err := io.Copy(w, strings.NewReader(nlpnewt_api_v1.Events))
			if err != nil {
				w.WriteHeader(500)
			}
			w.Header().Set("Content-Type", "application/json")
		})

	corsHandler := handlers.CORS(
		handlers.AllowedOrigins([]string{"*"}),
		handlers.AllowedMethods([]string{"GET", "POST", "DELETE", "PUT", "PATCH", "OPTIONS"}),
		handlers.AllowedHeaders([]string{"Content-Type", "api-key", "Authorization"}),
	)
	r.Handle("/v1/processors/swagger.json", corsHandler(m))
	r.Handle("/v1/events/swagger.json", corsHandler(m))
}

func run() error {
	glog.V(1).Infoln("Starting NLP-NEWT API gateway")
	err := viper.ReadInConfig() // Find and read the config file
	if err != nil { // Handle errors reading the config file
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

	serveSwagger(m)

	config := processors.Config{
		ConsulAddress:   consulHost,
		ConsulPort:      consulPort,
		RefreshInterval: viper.GetDuration("gateway.refresh_interval"),
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

	gwmux := runtime.NewServeMux()
	eventsLookup := viper.Get("gateway.events")
	var eventsAddr string
	if eventsLookup != nil {
		eventsAddr = cast.ToString(eventsLookup)
	} else {
		eventsAddr = "consul://" + consulAddr + "/nlpnewt-events/v1"
	}
	err = nlpnewt_api_v1.RegisterEventsHandlerFromEndpoint(
		ctx,
		gwmux,
		eventsAddr,
		[]grpc.DialOption{grpc.WithInsecure(), grpc.WithBalancerName("round_robin")})
	if err != nil {
		return err
	}
	m.PathPrefix("/v1/events").Handler(gwmux)

	port := strconv.Itoa(viper.GetInt("gateway.port"))
	glog.V(1).Infoln("Serving on port " + port)

	return http.ListenAndServe(":"+port, handlers.CORS(handlers.AllowedOrigins([]string{"*"}))(m))
}

func main() {
	flag.Parse()
	viper.SetDefault("consul.host", "localhost")
	viper.SetDefault("consul.port", 8500)
	viper.SetDefault("gateway.port", 8080)
	viper.SetDefault("gateway.refresh_interval", 10)
	viper.SetDefault("gateway.events", nil)
	viper.SetDefault("gateway.processors", []processors.ManualProcessor{})

	newtConfig, exists := os.LookupEnv("NEWT_CONFIG")
	if exists {
		viper.SetConfigFile(newtConfig)
	} else {
		viper.SetConfigName("newtConfig")
		viper.AddConfigPath(".")
		viper.AddConfigPath("$HOME/.newt")
		viper.AddConfigPath("/etc/newt")
	}

	defer glog.Flush()

	if err := run(); err != nil {
		glog.Fatal(err)
	}
}

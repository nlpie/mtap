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

package consul

import (
	"context"
	"github.com/golang/glog"
	"github.com/hashicorp/consul/api"
	"google.golang.org/grpc/resolver"
	"strconv"
	"strings"
	"sync"
	"time"
)

func init() {
	resolver.Register(NewBuilder())
}

const (
	defaultFreq = time.Minute * 1
)

type consulBuilder struct {
}

type consulResolver struct {
	freq     time.Duration
	t        *time.Timer
	service  string
	tags     []string
	ctx      context.Context
	cancel   context.CancelFunc
	updating bool
	cc       resolver.ClientConn
	client   *api.Client
	wg       sync.WaitGroup
	rn       chan struct{}
}

func NewBuilder() resolver.Builder {
	return &consulBuilder{}
}

func (*consulBuilder) Build(target resolver.Target, cc resolver.ClientConn, _ resolver.BuildOptions) (resolver.Resolver, error) {
	glog.V(3).Infof("Creating resolver for target %v", target)
	consulConfig := api.DefaultConfig()
	consulConfig.Address = target.URL.Host

	client, e := api.NewClient(consulConfig)
	if e != nil {
		return nil, e
	}

	split := strings.Split(target.URL.Path, "/")
	r := &consulResolver{
		freq:    defaultFreq,
		t:       time.NewTimer(0),
		service: split[0],
		tags:    split[1:],
		cc:      cc,
		client:  client,
		rn:      make(chan struct{}, 1),
	}
	r.ctx, r.cancel = context.WithCancel(context.Background())
	r.wg.Add(1)
	go r.watcher()

	return r, nil
}

func (*consulBuilder) Scheme() string {
	return "consul"
}

func (r *consulResolver) ResolveNow(_ resolver.ResolveNowOptions) {
	glog.V(3).Infof("resolve now called")
	select {
	case r.rn <- struct{}{}:
	default:
	}
}

func (r *consulResolver) lookup() []resolver.Address {
	entries, _, e := r.client.Health().ServiceMultipleTags(r.service, r.tags, true, nil)
	if e != nil {
		return []resolver.Address{}
	}
	addresses := make([]resolver.Address, 0, 10)
	for _, entry := range entries {
		node := entry.Node
		service := entry.Service
		addresses = append(addresses, resolver.Address{Addr: node.Address + ":" + strconv.Itoa(service.Port)})
	}
	return addresses
}

func (r *consulResolver) watcher() {
	defer r.wg.Done()
	for {
		select {
		case <-r.ctx.Done():
			return
		case <-r.t.C:
		case <-r.rn:
		}
		addrs := r.lookup()
		r.t.Reset(r.freq)

		_ = r.cc.UpdateState(resolver.State{
			Addresses:     addrs,
			ServiceConfig: nil,
		})
	}
}

func (r *consulResolver) Close() {
	r.cancel()
	r.wg.Wait()
	r.t.Stop()
}

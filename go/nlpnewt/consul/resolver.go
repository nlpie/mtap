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
	"golang.org/x/sync/semaphore"
	"google.golang.org/grpc/resolver"
	"strconv"
	"strings"
	"time"
)

func init() {
	resolver.Register(NewBuilder())
}

const (
	defaultFreq = time.Second * 30
)

type consulBuilder struct {
}

type consulResolver struct {
	t         *time.Ticker
	service   string
	tags      []string
	ctx       context.Context
	cancel    context.CancelFunc
	updating  bool
	cc        resolver.ClientConn
	client    *api.Client
	semaphore *semaphore.Weighted
}

func NewBuilder() resolver.Builder {
	return &consulBuilder{}
}

func (*consulBuilder) Build(target resolver.Target, cc resolver.ClientConn, opts resolver.BuildOption) (resolver.Resolver, error) {
	glog.V(3).Infof("Creating resolver for target %v", target)
	consulConfig := api.DefaultConfig()
	consulConfig.Address = target.Authority

	client, e := api.NewClient(consulConfig)
	if e != nil {
		return nil, e
	}

	split := strings.Split(target.Endpoint, "/")
	r := &consulResolver{
		t:         time.NewTicker(defaultFreq),
		service:   split[0],
		tags:      split[1:],
		cc:        cc,
		client:    client,
		semaphore: semaphore.NewWeighted(1),
	}
	r.ctx, r.cancel = context.WithCancel(context.Background())

	go r.watcher()

	return r, nil
}

func (*consulBuilder) Scheme() string {
	return "consul"
}

func (r *consulResolver) ResolveNow(opts resolver.ResolveNowOption) {
	glog.V(3).Infof("ResolveNow called for \"%v\" tags %v", r.service, r.tags)
	r.doUpdate()
}

func (r *consulResolver) doUpdate() {
	if !r.semaphore.TryAcquire(1) {
		return
	}
	defer r.semaphore.Release(1)
	glog.V(3).Infof("Updating addresses for service \"%v\" tags %v", r.service, r.tags)
	entries, _, e := r.client.Health().ServiceMultipleTags(r.service, r.tags, true, nil)
	if e != nil {
		glog.Error("Error getting service health from consul")
		return
	}
	addresses := make([]resolver.Address, 0, 10)
	for _, entry := range entries {
		node := entry.Node
		service := entry.Service
		addresses = append(addresses, resolver.Address{Addr: node.Address + ":" + strconv.Itoa(service.Port)})
	}
	if len(addresses) > 0 {
		glog.V(3).Infof("Found addresses for service \"%v\" tags %v", r.service, r.tags)
		r.cc.NewAddress(addresses)
	} else {
		glog.V(3).Infof("Did not find addresses for service \"%v\" tags %v", r.service, r.tags)
	}
}

func (r *consulResolver) watcher() {
	for {
		select {
		case <-r.ctx.Done():
			return
		case <-r.t.C:
		}
		r.doUpdate()
	}
}

func (r *consulResolver) Close() {
	glog.V(3).Infof("Closing resolver for service \"%v\" tags %v", r.service, r.tags)
	r.cancel()
}

# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

from ryu.base import app_manager
from ryu.controller import mac_to_port
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib import mac
from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link
from ryu.app.wsgi import ControllerBase
from collections import defaultdict
from ryu.lib import hub
from operator import attrgetter
from datetime import datetime
from termcolor import colored
import time
import csv
from ryu.lib.packet import arp, ipv6

# switches
myswitches = []

# mymac[srcmac]->(switch, port)
mymac = {}

# adjacency map [sw1][sw2]->port from sw1 to sw2
adjacency = defaultdict(lambda: defaultdict(lambda: None))

datapath_list = {}

byte = defaultdict(lambda: defaultdict(lambda: None))
clock = defaultdict(lambda: defaultdict(lambda: None))
bw_used = defaultdict(lambda: defaultdict(lambda: None))
bw_available = defaultdict(lambda: defaultdict(lambda: None))
bw = defaultdict(lambda: defaultdict(lambda: None))


def max_abw(abw, Q):
    max = float('-Inf')
    node = 0
    for v in Q:
        if abw[v] > max:
            max = abw[v]
            node = v
    return node
    
def get_path2(src, dst, first_port, final_port):
    global bw_available
    print "Dijkstra's widest path algorithm"
    print "src=", src, " dst=", dst, " first_port=", first_port, " final_port=", final_port

    # available bandwidth
    abw = {}
    previous = {}

    for dpid in myswitches:
        abw[dpid] = float('-Inf')
        previous[dpid] = None

    abw[src] = float('Inf')
    Q = set(myswitches)
    print "Q:", Q

    # print time.time()
    while len(Q) > 0:
        u = max_abw(abw, Q)
        Q.remove(u)
        print "Q:", Q, "u:", u

        for p in myswitches:
            if adjacency[u][p] != None:
                link_abw = bw_available[str(u)][str(p)]
                print "link_abw:", str(u), "->", str(p), ":", link_abw, "kbps"
                # alt=max(abw[p], min(width[u], abw_between(u,p)))
                if abw[u] < link_abw:
                    tmp = abw[u]
                else:
                    tmp = link_abw
                if abw[p] > tmp:
                    alt = abw[p]
                else:
                    alt = tmp

                if alt > abw[p]:
                    abw[p] = alt
                    previous[p] = u

    # print "distance=", distance, " previous=", previous
    r = []
    p = dst
    r.append(p)
    q = previous[p]

    while q is not None:
        if q == src:
            r.append(q)
            break
        p = q
        r.append(p)
        q = previous[p]

    r.reverse()
    if src == dst:
        path = [src]
    else:
        path = r

    # Now add the ports
    r = []
    in_port = first_port
    for s1, s2 in zip(path[:-1], path[1:]):
        out_port = adjacency[s1][s2]
        r.append((s1, in_port, out_port))
        in_port = adjacency[s2][s1]
    r.append((dst, in_port, final_port))
    return r
    
def minimum_distance(distance, Q):
    # print "minimum_distance() is called", " distance=", distance, " Q=", Q
    min = float('Inf')
    node = 0
    for v in Q:
        if distance[v] < min:
            min = distance[v]
            node = v
    return node
    
    
def get_path(src, dst, first_port, final_port):
    # Dijkstra's algorithm
    global myswitches, adjacency
    print "Dijkstra's shortest path algorithm"
    print "get_path is called, src=", src, " dst=", dst, " first_port=", first_port, " final_port=", final_port
    distance = {}
    previous = {}

    for dpid in myswitches:
        distance[dpid] = float('Inf')
        previous[dpid] = None

    distance[src] = 0
    Q = set(myswitches)
    # print "Q=", Q

    while len(Q) > 0:
        u = minimum_distance(distance, Q)
        # print "u=", u
        Q.remove(u)
        # print "After removing ", u, " Q=", Q
        for p in myswitches:
            if adjacency[u][p] != None:
                print colored('u e p','green')                 
                print u, "--------",  p
                w = 1
                if distance[u] + w < distance[p]:
                    distance[p] = distance[u] + w
                    previous[p] = u

    # print "distance=", distance, " previous=", previous
    r = []
    p = dst
    r.append(p)
    q = previous[p]

    while q is not None:
        if q == src:
            r.append(q)
            break
        p = q
        r.append(p)
        q = previous[p]

    r.reverse()
    if src == dst:
        path = [src]
    else:
        path = r

    # Now add the ports
    r = []
    in_port = first_port
    for s1, s2 in zip(path[:-1], path[1:]):
        out_port = adjacency[s1][s2]
        r.append((s1, in_port, out_port))
        in_port = adjacency[s2][s1]
    r.append((dst, in_port, final_port))
    return r
    
class ProjectController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    global result, band, tx_ini, tx_fin
    result = band = tx_ini = tx_fin = 0
    def __init__(self, *args, **kwargs):
        super(ProjectController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.topology_api_app = self
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)
        self.arp_table = {}
        self.sw = {}
        global bw
        
@set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])

def _state_change_handler(self, ev):
    datapath = ev.datapath
    if ev.state == MAIN_DISPATCHER:
      if not datapath.id in self.datapaths:
        # self.logger.debug('register datapath: %016x', datapath.id)
        print 'register datapath:', datapath.id
        self.datapaths[datapath.id] = datapath
      elif ev.state == DEAD_DISPATCHER:
        if datapath.id in self.datapaths:
          # self.logger.debug('unregister datapath: %016x', datapath.id)
          print 'unregister datapath:', datapath.id
          del self.datapaths[datapath.id]


def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(1)


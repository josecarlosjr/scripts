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

#Dijkstra for longgest path    
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
    
#Dijkstra for shortest path    
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

def _request_stats(self, datapath):
    # self.logger.debug('send stats request: %016x', datapath.id)
    # print 'send stats request:', datapath.id
    ofproto = datapath.ofproto
    parser = datapath.ofproto_parser

    req = parser.OFPFlowStatsRequest(datapath)
    datapath.send_msg(req)

    req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
    datapath.send_msg(req)
    
    
@set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
def _port_stats_reply_handler(self, ev):
    global byte, clock, bw_used, bw_available, band, result, tx_ini, tx_fin
    # print time.time()," _port_stats_reply_handler"
    body = ev.msg.body
    dpid = ev.msg.datapath.id

    #print "DPID", dpid
    for stat in sorted(body, key=attrgetter('port_no')):
        # print dpid, stat.port_no, stat.tx_packets
        for p in myswitches:
            if adjacency[dpid][p] == stat.port_no:
                # print dpid, p, stat.port_no
                if byte[dpid][p] > 0:
                    bw_used[dpid][p] = (stat.tx_bytes - byte[dpid][p]) * 8.0 / (time.time() - clock[dpid][p]) / 1000
                    bw_available[str(dpid)][str(p)]= 1 * 1024.0 - bw_used[dpid][p]
                    #print colored('int(bw[str(dpid)][str(p)])','green')
                    #print(int(bw[str(dpid)][str(p)]))
                    
                    #print str(dpid), "->", str(p), ":", bw_available[str(dpid)][str(p)], " kbps"
                    # print str(dpid),"->",str(p),":", bw[str(dpid)][str(p)]," kbps"
                byte[dpid][p] = stat.tx_bytes
                clock[dpid][p] = time.time()
    #print "-------------------------------------------------------------------"
    t = time.localtime().tm_sec  # em segundos
    #        print t, 'seg'
    
    if dpid == 2:
        for stat in sorted(body, key=attrgetter('port_no')):
            #                if stat.port_no == 2:
            self.logger.info('switch             '
                             'Port_no         '
                             'Rec_bytes     Trans_bytes       '
                             'banda        '
                            )
            self.logger.info('%016x  %8x         '
                             '%8d     %8d       %8d Mbps',
                             ev.msg.datapath.id, stat.port_no,
                             stat.rx_bytes, stat.tx_bytes, result)
        #if stat.port_no == 2 and tx_ini == 0:  # Se o numero da porta for 3 e os bytes iniciais forem 0
        #    tx_ini = stat.tx_bytes  # valor inicial bytes armazenado
        #if stat.port_no == 2 and t < 59:
        #    tx_fin = stat.tx_bytes
        # perc = band/157,286,400
        #    band = (tx_fin-tx_ini)*8
        #    result = int(band/1048576)
        #    print((int(band/1048576)),  'Mbit/s')
        #    tx_ini = tx_fin
        
        
# Handy function that lists all attributes in the given object
#def ls(self, obj):
#    print("\n".join([x for x in dir(obj) if x[0] != "_"]))

def add_flow(self, datapath, in_port, dst, actions):
    ofproto = datapath.ofproto
    parser = datapath.ofproto_parser
    match = datapath.ofproto_parser.OFPMatch(
        in_port=in_port, eth_dst=dst)
    inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
    mod = datapath.ofproto_parser.OFPFlowMod(
        datapath=datapath, match=match, cookie=0,
        command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
        priority=ofproto.OFP_DEFAULT_PRIORITY, instructions=inst)
    datapath.send_msg(mod)
    
def add_flow_v6(self, datapath, priority, match, actions):
    ofproto = datapath.ofproto
    parser = datapath.ofproto_parser    
    inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                         actions)]
    mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                            idle_timeout=5, hard_timeout=15,
                            match=match, instructions=inst)
    datapath.send_msg(mod)

def install_path(self, p, ev, src_mac, dst_mac):
    print "install_path is called"
    # print "p=", p, " src_mac=", src_mac, " dst_mac=", dst_mac
    msg = ev.msg
    datapath = msg.datapath
    ofproto = datapath.ofproto
    parser = datapath.ofproto_parser
    for sw, in_port, out_port in p:
        print src_mac, "->", dst_mac, "via ", sw, " in_port=", in_port, " out_port=", out_port
        match = parser.OFPMatch(in_port=in_port, eth_src=src_mac, eth_dst=dst_mac)
        actions = [parser.OFPActionOutput(out_port)]
        datapath = datapath_list[sw]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = datapath.ofproto_parser.OFPFlowMod(
            datapath=datapath, match=match, idle_timeout=0, hard_timeout=0,
            priority=1, instructions=inst)
        datapath.send_msg(mod)
        
        
@set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
def switch_features_handler(self, ev):
    print "switch_features_handler is called"
    datapath = ev.msg.datapath
    ofproto = datapath.ofproto
    parser = datapath.ofproto_parser
    match = parser.OFPMatch()
    actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
    inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
    mod = datapath.ofproto_parser.OFPFlowMod(
        datapath=datapath, match=match, cookie=0,
        command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
        priority=0, instructions=inst)
    datapath.send_msg(mod)        
        
        
@set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
def _packet_in_handler(self, ev):
    global target_srcmac, target_dstmac
    # print "packet_in event:", ev.msg.datapath.id, " in_port:", ev.msg.match['in_port']
    msg = ev.msg
    datapath = msg.datapath
    ofproto = datapath.ofproto
    parser = datapath.ofproto_parser
    in_port = msg.match['in_port']
    pkt = packet.Packet(msg.data)
    eth = pkt.get_protocols(ethernet.ethernet)[0]
    # print "eth.ethertype=", eth.ethertype

    # avoid broadcast from LLDP
    if eth.ethertype == 35020:
        return
    
    dst = eth.dst
    src = eth.src
    dpid = datapath.id
    
    #DROP storm bradcast IPv6 evitando Flood(loop)
    if pkt.get_protocol(ipv6.ipv6):
        match = parser.OFPMatch(eth_type=eth.ethertype)
        actions = []
        self.add_flow_v6(datapath, 1, match, actions)
        return None
    
    #ARP LEARNING
    arp_pkt = pkt.get_protocol(arp.arp)
    if arp_pkt:
        self.arp_table[arp_pkt.src_ip] = src  # ARP learning
        
    self.mac_to_port.setdefault(dpid, {})
    
    # Learn a mac address to avoid FLOOD next time.
    self.mac_to_port[dpid][src] = in_port

    # print "src=", src, " dst=", dst, " type=", hex(eth.ethertype)
    # print "adjacency=", adjacency

    #Regra evita broadcast storm arp na rede    
    if dst in self.mac_to_port[dpid]:
        out_port = self.mac_to_port[dpid][dst]
    else:
        if self.arp_handler(msg):  # 1:reply or drop;  0: flood
            return None
        else:
            out_port = ofproto.OFPP_FLOOD        
    
    if dst in mymac.keys():
        if (src == src and dst == dst) or (dst == srcc and src == dst):
            p = get_path2(mymac[src][0], mymac[dst][0], mymac[src][1], mymac[dst][1])
        else:
            p = get_path(mymac[src][0], mymac[dst][0], mymac[src][1], mymac[dst][1])
            print "Path=", p
            self.install_path(p, ev, src, dst)
            out_port = p[0][2]

        else:
            out_port = ofproto.OFPP_FLOOD


        actions = [parser.OFPActionOutput(out_port)]
        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_src=src, eth_dst=dst)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        if out_port == ofproto.OFPP_FLOOD:
            print "FLOOD"
            while len(actions) > 0: actions.pop()
            for i in range(1, 23):
                actions.append(parser.OFPActionOutput(i))
            # print "actions=", actions
            out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                              in_port=in_port, actions=actions, data=data)
            datapath.send_msg(out)
        else:
            # print "unicast"
            out = parser.OFPPacketOut(
                datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port,
                actions=actions, data=data)
            datapath.send_msg(out)

    events = [event.EventSwitchEnter,
          event.EventSwitchLeave, event.EventPortAdd,
          event.EventPortDelete, event.EventPortModify,
          event.EventLinkAdd, event.EventLinkDelete]    
        
    

    
                            
    
        
        
        
        
        
        
            
            
                            
        
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

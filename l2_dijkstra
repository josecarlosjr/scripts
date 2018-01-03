#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
An OpenFlow 1.3 L2 learning switch implementation.
"""
# from ryu.app import simple_monitor_13
from operator import attrgetter
from ryu.base import app_manager
from ryu.controller import ofp_event, event, handler, mac_to_port
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib import dpid as dpid_lib  # adicionado
from ryu.lib import stplib  # adicionado
from ryu.app import simple_switch_13  # adicionado
from ryu.lib.packet import packet, ethernet, ether_types
from termcolor import colored
from ryu.lib import lacplib
from ryu.lib.dpid import str_to_dpid
import py  # adicionado
import os  # adicionado
#import struct
#import math
from ryu.ofproto import ofproto_v1_3_parser
from ryu.lib.packet import ipv4, arp
import threading
from threading import Thread
import time
from datetime import datetime
# import warnings
from ryu.controller import dpset
from ryu.lib.dpid import dpid_to_str
from ryu.lib import hub
#import threading
#import thread
from ryu.app import simple_switch_lacp
from ryu.lib.mac import haddr_to_bin
from ryu.lib import mac
from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link
from ryu.app.wsgi import ControllerBase
from collections import defaultdict
from ryu.lib import hub


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

#bw = defaultdict(lambda: defaultdict(lambda: None))

#target_srcmac = "00:00:00:00:00:03"
#target_dstmac = "00:00:00:00:00:04"

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
    #    print "Q:", Q, "u:", u

        for p in myswitches:
            if adjacency[u][p] != None:
                link_abw = bw_available[str(u)][str(p)]
               # print "link_abw:", str(u), "->", str(p), ":", link_abw, "kbps"
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
        path == [src]
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
                # print u, "--------",  p
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
    
    # CLASSE PAI
#class SimpleSwitch13(simple_switch_13.SimpleSwitch13):
class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
#    _CONTEXTS = {'stplib': stplib.Stp}
    # VARIAVEIS GLOBAIS
    global tx_ini, tx_fin, band, t, result
    tx_ini = tx_fin = t = band = result = 0

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        # super(SimpleMonitor13, self).__init__(*args, *kwargs)
        self.mac_to_port = {}
        #self.stp = kwargs['stplib']
        self.datapaths = {}
        self.topology_api_app = self
        self.monitor_thread = hub.spawn(self._monitor)


    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        dp = datapath.id
        # print colored('Datapath','green')
        # print(dp)
        #if dp == 2:
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                #self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                #self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(1)  # 0.25 exibirÃ¡ 4/seg

    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)
        
        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        body = ev.msg.body




    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        global target_srcmac, target_dstmac
        msg = ev.msg  # Mensagem BASE do Evento armazenada na variavel msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        #avoid broadcast from LLDP
        if eth.ethertype == 35020:
            return

        dst = eth.dst
        src = eth.src
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        #self.mac_to_port[dpid][src] = in_port

        if src not in mymac.keys():
            mymac[src] = (dpid, in_port)
            print "mymac=", mymac

        #if dst in self.mac_to_port[dpid]:  ##
        #    out_port = self.mac_to_port[dpid][dst]
        #else:
        #    out_port = ofproto.OFPP_FLOOD
        if dst in mymac.keys():
            if (src == src and dst == dst) or (dst == src and src == dst):
                p = get_path2(mymac[src][0], mymac[dst][0], mymac[src][1], mymac[dst][1])
            else:
                p = get_path(mymac[src][0], mymac[dst][0], mymac[src][1], mymac[dst][1])
            print "Path = ", p
            self.install_path(p, ev, src, dst)
            out_port = p[0][2] 
        
        #        if dst in mymac.keys():
#            p = get_path(mymac[src][0], mymac[dst][0], mymac[src][1], mymac[dst][1])
#            print p
#            self.install_path(p, ev, src,dst)
#            out_port = p[0][2]

        else:
            out_port = ofproto.OFPP_FLOOD


        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_src=src, eth_dst=dst)
            #self.add_flow(datapath, 1, match, actions)
            # self.add_flow(datapath, msg.in_port, dst, actions)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        if out_port == ofproto.OFPP_FLOOD:
            while len(actions) > 0: actions.pop()

            for i in range(1, 23):
                actions.append(parser.OFPActionOutput(i))
            out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                    in_port=in_port, actions=actions, data=data)
            datapath.send_msg(out)
        else:
            out = parser.OFPPacketOut(
                    datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port,
                    actions=actions, data=data)
            datapath.send_msg(out)

        #out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
        #                          in_port=in_port, actions=actions, data=data)

        #datapath.send_msg(out)

    events = [event.EventSwitchEnter,
            event.EventSwitchLeave, event.EventPortAdd,
            event.EventPortDelete, event.EventPortModify,
            event.EventLinkAdd, event.EventLinkDelete]
        
        
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


    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def port_stats_reply_handler(self, ev):
        global byte, clock, bw_used, bw_available, tx_ini, t, band, tx_fin, result
        body = ev.msg.body
        dp = ev.msg.datapath.id

        #bd = []
        #conteudo = []
        #cont = 0
        #print "DPID", dp

        for stat in sorted(body, key=attrgetter('port_no')):
            for p in myswitches:
                if adjacency[dp][p] == stat.port_no:
                    if byte[dp][p] > 0:
                        bw_used[dp][p] = (stat.tx_bytes - byte[dp][p]) * 8.0 / (time.time() - clock[dp][p]) / 1000
                        bw_available[str(dp)][str(p)]= 1 * 1024.0 - bw_used[dp][p]
                        #print str(dp),"->",str(p),":",bw_available[str(dp)][str(p)]," kbps"

                    byte[dp][p]=stat.tx_bytes
                    clock[dp][p]=time.time()
#        print "-------------------------------------------------------------------"         
        #if banda disponivel get_path2

        #int(bw[str(dp)][str(p)]) 

        #global tx_ini, t, band, tx_fin, result

        # t = datetime.now().strftime("%S.%f") #tempo em microssegundos
        t = time.localtime().tm_sec  # em segundos
#        print t, 'seg'


if dp == 2:
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
                #print((int(band/1048576)),  'Mbit/s')
            #    tx_ini = tx_fin
            #if result > 56:
                #self.send_port_mod(ev.msg.datapath)
                #self.send_flow_mod1(ev.msg.datapath)
            #    print colored('regra aplicada','blue')                 


    #def send_flow_mod1(self, datapath):
#       ofp = datapath.ofproto
#       ofp_parser = datapath.ofproto_parser
#       #print(ofp_parser)      
#       cookie = cookie_mask = 0
#       table_id = 0
#       idle_timeout = hard_timeout = 0
#       #priority = 32768
#       priority = 30000
#        buffer_id = ofp.OFP_NO_BUFFER
#       match = ofp_parser.OFPMatch(in_port=1, eth_dst='00:00:00:00:00:01')
#       actions = [ofp_parser.OFPActionOutput(ofp.OFPP_NORMAL, 0)] 
#       inst = [ofp_parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]
#       
#       req = ofp_parser.OFPFlowMod(datapath, cookie, cookie_mask, table_id, ofp.OFPFC_MODIFY, idle_timeout, hard_timeout, priority, buffer_id, ofp.OFPP_ANY, ofp.OFPG_ANY, ofp.OFPFF_SEND_FLOW_REM, match, inst)
#
#       datapath.send_msg(req)


    def install_path(self, p, ev, src_mac, dst_mac):
        print "install_path is called"
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


#    def delete_flow(self, datapath):
#        ofproto = datapath.ofproto
#        parser = datapath.ofproto_parser
#        #
#        for dst in self.mac_to_port[datapath.id].keys():
#            match = parser.OFPMatch(eth_dst=dst)
#            mod = parser.OFPFlowMod(
#                datapath, command=ofproto.OFPFC_DELETE,
#                out_port=ofproto.OFPP_ANY, out_group=ofproto.OFPG_ANY,
#                priority=1, match=match)
#            datapath.send_msg(mod)


#    @set_ev_cls(stplib.EventTopologyChange, MAIN_DISPATCHER)   
#    def _topology_change_handler(self, ev):
#        dp = ev.dp
#        dpid_str = dpid_lib.dpid_to_str(dp.id)
#        msg = 'Receive topology change event. Flush MAC table.'
        # self.logger.debug("[switch id=%s] %s", dpid_str, msg)
#
#        if dp.id in self.mac_to_port:
#            self.delete_flow(dp)
#            del self.mac_to_port[dp.id]

    #@set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    #def _state_change_handler(self, ev):
    #    datapath = ev.datapath
    #    if ev.state == MAIN_DISPATCHER:
    #        if not datapath.id in self.datapaths:
    #            # self.logger.debug('register datapath: %016x', datapath.id)
    #            print 'register datapath:', datapath.id
    #            self.datapaths[datapath.id] = datapath
    #    elif ev.state == DEAD_DISPATCHER:
    #        if datapath.id in self.datapaths:
    #            # self.logger.debug('unregister datapath: %016x', datapath.id)
    #            print 'unregister datapath:', datapath.id
    #            del self.datapaths[datapath.id]   


    @set_ev_cls(events)
    def get_topology_data(self, ev):
        print "get_topology_data() is called"
        global myswitches, adjacency, datapath_list
        switch_list = get_switch(self.topology_api_app, None)
        myswitches = [switch.dp.id for switch in switch_list]

        for switch in switch_list:
            datapath_list[switch.dp.id] = switch.dp
            # print "datapath_list=", datapath_list
        print "myswitches=", myswitches
        links_list = get_link(self.topology_api_app, None)
        # print "links_list=", links_list

        mylinks = [(link.src.dpid, link.dst.dpid, link.src.port_no, link.dst.port_no) for link in links_list]
        for s1, s2, port1, port2 in mylinks:
            # print "type(s1)=", type(s1), " type(port1)=", type(port1)
            adjacency[s1][s2] = port1
            adjacency[s2][s1] = port2
            print "DP  :   Porta           DP   :   Porta"
            print s1, "  :  ", port1, "<------>", s2, "  :  ", port2
        
        
        
       #    @set_ev_cls(stplib.EventPortStateChange, MAIN_DISPATCHER)
#    def _port_state_change_handler(self, ev):
#        dpid_str = dpid_lib.dpid_to_str(ev.dp.id)
#        of_state = {stplib.PORT_STATE_DISABLE: 'DISABLE',
#                    stplib.PORT_STATE_BLOCK: 'BLOCK',
#                    stplib.PORT_STATE_LISTEN: 'LISTEN',
#                    stplib.PORT_STATE_LEARN: 'LEARN',
#                    stplib.PORT_STATE_FORWARD: 'FORWARD'}
#        self.logger.debug("[dpid=%s][port=%d] state=%s",
#                          dpid_str, ev.port_no, of_state[ev.port_state])


# classe filha para monitoramento
#class SimpleMonitor13(SimpleSwitch13):  # heranÃ§a do simpleswitch13
#    def __init__(self, *args, **kwargs):
#        super(SimpleSwitch13, self).__init__(self)  # conexÃ£o necessaria para herdar a classe anterior
#        self.datapaths = {}
#        self.monitor_thread = hub.spawn(self._monitor)

#    @set_ev_cls(ofp_event.EventOFPStateChange,
#                [MAIN_DISPATCHER, DEAD_DISPATCHER])
#    def _state_change_handler(self, ev):
#        datapath = ev.datapath
#        dp = datapath.id
        # print colored('Datapath','green')
        # print(dp)
#        if dp == 2:
#            if ev.state == MAIN_DISPATCHER:
#                if datapath.id not in self.datapaths:
                    #self.logger.debug('register datapath: %016x', datapath.id)
#                    self.datapaths[datapath.id] = datapath
#            elif ev.state == DEAD_DISPATCHER:
#                if datapath.id in self.datapaths:
                    #self.logger.debug('unregister datapath: %016x', datapath.id)
#                    del self.datapaths[datapath.id]

#    def _monitor(self):
#        while True:
#            for dp in self.datapaths.values():
#                self._request_stats(dp)
#            hub.sleep(1)  # 0.25 exibirÃ¡ 4/seg
#
#    def _request_stats(self, datapath):
#        self.logger.debug('send stats request: %016x', datapath.id)
#        ofproto = datapath.ofproto
#        parser = datapath.ofproto_parser
        # req = parser.OFPFlowStatsRequest(datapath)
        # datapath.send_msg(req)

#        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY) 
        
        
        
        
        
        
        
        
        

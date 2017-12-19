#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
An OpenFlow 1.3 L2 learning switch implementation.
"""
# from ryu.app import simple_monitor_13
from operator import attrgetter
from ryu.base import app_manager
from ryu.controller import ofp_event, event, handler
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
import struct
import math
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
import threading
import thread
from ryu.app import simple_switch_lacp


# CLASSE PAI
class SimpleSwitch13(simple_switch_13.SimpleSwitch13):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'stplib': stplib.Stp}
    # VARIAVEIS GLOBAIS
    global tx_ini, tx_fin, band, t, result
    tx_ini = tx_fin = t = band = result=0

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        # super(SimpleMonitor13, self).__init__(*args, *kwargs)
        self.mac_to_port = {}
        self.stp = kwargs['stplib']
        self.datapath = {}
        # self.monitor_thread = hub.spawn(self._monitor)

        ##amostra do stplib config
        ##referencia stplib.stp.set_config() para detalhes
        config = {dpid_lib.str_to_dpid('0000000000000001'):
                      {'bridge': {'priority': 0x8000}},
                  dpid_lib.str_to_dpid('0000000000000002'):
                      {'bridge': {'priority': 0x9000}},
                  dpid_lib.str_to_dpid('0000000000000003'):
                      {'bridge': {'priority': 0xa000}}}
        self.stp.set_config(config)

    @set_ev_cls(stplib.EventPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg  # Mensagem BASE do Evento armazenada na variavel msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        dst = eth.dst
        src = eth.src
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        #print(parser)
        # self.logger.info("switch %s, Origem %s, Destino %s , porta %s", dpid, src, dst, in_port)

        # se o switch for o numero 2 envia a requisicao
        #if dpid == 2:
        #    port_stat_request = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        #    datapath.send_msg(port_stat_request)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:  ##
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            self.add_flow(datapath, 1, match, actions)
            # self.add_flow(datapath, msg.in_port, dst, actions)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        # out = datapath.ofproto_parser.OFPPacketOut(
        #    datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port,
        #    actions=actions, data=data)
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)

        datapath.send_msg(out)

    # 2
    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def port_stats_reply_handler(self, ev):
        body = ev.msg.body
	dp = ev.msg.datapath.id
	
        global tx_ini, aux, t, band, tx_fin, result
        
        # t = datetime.now().strftime("%S.%f") #tempo em microssegundos
        t = time.localtime().tm_sec  # em segundos
        print t, 'seg'

        # [flow for flow in body if flow.port_no == 3],
        for stat in sorted(body, key=attrgetter('port_no')):
            # if stat.port_no == 3:
            self.logger.info('switch             '
                             'Port_no         '
                             'Rec_bytes     Trans_bytes       '
                             'banda        '
                             )
            self.logger.info('%016x  %8x         '
                             '%8d     %8d       %8d',
                             ev.msg.datapath.id, stat.port_no,
                             stat.rx_bytes, stat.tx_bytes, result)

            if stat.port_no == 3 and tx_ini == 0:  # Se o numero da porta for 3 e os bytes iniciais forem 0
                tx_ini = stat.tx_bytes  # valor inicial bytes armazenado
                #print colored('tx_ini', 'blue')
                #print(tx_ini)

            if stat.port_no == 3 and t == 59:
                tx_fin = stat.tx_bytes
                # band = (tx_fin - tx_ini)*8/60
                # band = (tx_fin - tx_ini)*int(8/1048576)
                # perc = band/157,286,400
                band = (tx_fin - tx_ini) * 8 / 60
                result = int(band/1048576)
		tx_ini = tx_fin
	if result > 56:
	    #self.send_port_mod(ev.msg.datapath)
	    self.send_flow_mod1(ev.msg.datapath)
	    print colored('regra aplicada','blue')	                
	            
	
	

    #def send_port_mod(self, datapath):
#	ofp = datapath.ofproto
#	ofp_parser = datapath.ofproto_parser
##
#	port_no = 3
#	hw_addr = '02:2a:34:4c:8e:8d'
##	config = 0
#	mask = (ofp.OFPPC_NO_FWD)
#	
#	advertise = (ofp.OFPPF_PAUSE)
#
#	req = ofp_parser.OFPPortMod(datapath, port_no, hw_addr, config, mask, advertise)
#	datapath.send_msg(req)

    def send_flow_mod1(self, datapath):
	ofp = datapath.ofproto
	ofp_parser = datapath.ofproto_parser
	#print(ofp_parser)	
	cookie = cookie_mask = 0
	table_id = 0
	idle_timeout = hard_timeout = 0
	priority = 32768
	buffer_id = ofp.OFP_NO_BUFFER
	match = ofp_parser.OFPMatch(in_port=1, eth_dst='00:00:00:00:00:01')
	actions = [ofp_parser.OFPActionOutput(ofp.OFPP_NORMAL, 0)] 
	inst = [ofp_parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]
	
	req = ofp_parser.OFPFlowMod(datapath, cookie, cookie_mask, table_id, ofp.OFPFC_MODIFY, idle_timeout, hard_timeout, priority, buffer_id, ofp.OFPP_ANY, ofp.OFPG_ANY, ofp.OFPFF_SEND_FLOW_REM, match, inst)

	datapath.send_msg(req)


    def send_flow_mod2(self, datapath):
	ofp = datapath.ofproto
	ofp_parser = datapath.ofproto_parser
	#print(ofp_parser)	
	cookie = cookie_mask = 0
	table_id = 0
	idle_timeout = hard_timeout = 0
	priority = 32768
	buffer_id = ofp.OFP_NO_BUFFER
	match = ofp_parser.OFPMatch(in_port=1, eth_dst='00:00:00:00:00:01')
	actions = [ofp_parser.OFPActionOutput(ofp.OFPP_NORMAL, 0)] 
	inst = [ofp_parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)]
	
	req = ofp_parser.OFPFlowMod(datapath, cookie, cookie_mask, table_id, ofp.OFPFC_MODIFY, idle_timeout, hard_timeout, priority, buffer_id, ofp.OFPP_ANY, ofp.OFPG_ANY, ofp.OFPFF_SEND_FLOW_REM, match, inst)

	datapath.send_msg(req)





    # 3

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def flow_stats_reply_handler(self, ev):
        body = ev.msg.body
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        self.logger.info('Switch           '
                         'in-port    eth-dest        out-port          '
                         )
        self.logger.info('---------------- '
                         '--------  -----------------  '
                         '--------  ')
        for stat in sorted([flow for flow in body if flow.priority == 1],
                           key=lambda flow: (flow.match['in_port'], flow.match['eth_dst'])):
            if stat.instructions[0].actions[0].port == 3:
                self.logger.info('%016x %8x  %17s %8x',
                                 ev.msg.datapath.id,
                                 stat.match['in_port'], stat.match['eth_dst'],
                                 stat.instructions[0].actions[0].port)

                # if stat.instructions[0].actions[0].port == 3:
                #    port_stat_request = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
                #    datapath.send_msg(port_stat_request)

    # def send_port_mod(self, datapath):
    #    ofp = datapath.ofproto
    #    ofp_parser = datapath.ofproto_parser

    #    port_no = 4
    #    hw_addr = ''
    #    config = 0
    #    mask = (ofp.OFPC_PORT_DOWN | ofp.OFPPC_NO_RECV |
    #            ofp.OFPPC_NO_FWD | ofp.OFPPC_NO_PACKET_IN)

    #    advertise = (ofp.OFPPF_10MB_HD | ofp.OFPPF_100MB_FD |
    #            ofp.OFPPF_1GB_FD | ofp.OFPPF_COPPER |
    #            fp.OFPPF_AUTONEG | ofp.OFPPF_PAUSE |
    #            ofp.OFPPF_PAUSE_ASYM)

    #    req = ofp_parser.OFPPortMod(datapath, port_no, hw_addr, config,
    #            mask, advertise)
    #    datapath.send_msg(req)


    def delete_flow(self, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        #
        for dst in self.mac_to_port[datapath.id].keys():
            match = parser.OFPMatch(eth_dst=dst)
            mod = parser.OFPFlowMod(
                datapath, command=ofproto.OFPFC_DELETE,
                out_port=ofproto.OFPP_ANY, out_group=ofproto.OFPG_ANY,
                priority=1, match=match)
            datapath.send_msg(mod)

            ###Funcao add_flow mantida###
            # def add_flow(self, datapath, in_port, dst, actions):
            #    ofproto = datapath.ofproto
            #    print colored('add_flow OFPROTO', 'red')
            #    print(type(ofproto))
            #    print(ofproto)
            #    print
            #
            #    match = datapath.ofproto_parser.OFPMatch(
            #        in_port=in_port, dl_dst=haddr_to_bin(dst))
            #    print colored('add_flow MATCH','red')
            #    print(type(match))
            #    print
            #
            #    mod = datapath.ofproto_parser.OFPFlowMod(
            #        datapath=datapath, match=match, cookie=0,
            #        command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
            #        priority=ofproto.OFP_DEFAULT_PRIORITY,
            #        flags=ofproto.OFPFF_SEND_FLOW_REM, actions=actions)
            #    print colored('add_flow MOD','red')
            #    print(type(mod))
            #    print(mod)
            #    print

            #    datapath.send_msg(mod)
            # print colored('', '')
            # print(type(datapath.send_msg(mod)))
            # print(datapath.send_msg(mod))

    @set_ev_cls(stplib.EventTopologyChange, MAIN_DISPATCHER)
    def _topology_change_handler(self, ev):
        dp = ev.dp
        dpid_str = dpid_lib.dpid_to_str(dp.id)
        msg = 'Receive topology change event. Flush MAC table.'
        # self.logger.debug("[switch id=%s] %s", dpid_str, msg)

        if dp.id in self.mac_to_port:
            self.delete_flow(dp)
            del self.mac_to_port[dp.id]

    @set_ev_cls(stplib.EventPortStateChange, MAIN_DISPATCHER)
    def _port_state_change_handler(self, ev):
        dpid_str = dpid_lib.dpid_to_str(ev.dp.id)
        of_state = {stplib.PORT_STATE_DISABLE: 'DISABLE',
                    stplib.PORT_STATE_BLOCK: 'BLOCK',
                    stplib.PORT_STATE_LISTEN: 'LISTEN',
                    stplib.PORT_STATE_LEARN: 'LEARN',
                    stplib.PORT_STATE_FORWARD: 'FORWARD'}
        self.logger.debug("[dpid=%s][port=%d] state=%s",
                          dpid_str, ev.port_no, of_state[ev.port_state])


# classe filha para monitoramento
class SimpleMonitor13(SimpleSwitch13):  # heranÃ§a do simpleswitch13
    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(self)  # conexÃ£o necessaria para herdar a classe anterior
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)

    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        dp = datapath.id
        # print colored('Datapath','green')
        # print(dp)
        if dp == 2:
            if ev.state == MAIN_DISPATCHER:
                if datapath.id not in self.datapaths:
                    self.logger.debug('register datapath: %016x', datapath.id)
                    self.datapaths[datapath.id] = datapath
            elif ev.state == DEAD_DISPATCHER:
                if datapath.id in self.datapaths:
                    self.logger.debug('unregister datapath: %016x', datapath.id)
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
        # req = parser.OFPFlowStatsRequest(datapath)
        # datapath.send_msg(req)

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

        # @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
        # def _flow_stats_reply_handler(self, ev):
        #    body = ev.msg.body

        # self.logger.info('datapath         '
        #        'in-port  eth-dst           '
        #        'out-port packets  bytes')
        # self.logger.info('---------------- '
        #        '-------- ----------------- '
        #        '-------- -------- --------')
        # for stat in sorted([flow for flow in body if flow.priority == 1], key=lambda flow: (flow.match['in_port'], flow.match['eth_dst'])):
        #    self.logger.info('%016x %8x %17s %8x %8d %8d',
        #            ev.msg.datapath.id,
        #            stat.match['in_port'], stat.match['eth_dst'],
        #            stat.instructions[0].actions[0].port,
        #            stat.packet_count, stat.byte_count)

        # @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
        # def _port_stats_reply_handler(self, ev):
        #    body = ev.msg.body
        # self.logger.info('datapath         port     '
        #        'rx-pkts  rx-bytes '
        #        'tx-pkts  tx-bytes')
        # self.logger.info('---------------- -------- '
        #        '-------- -------- -------- '
        #        '-------- -------- --------')

       




   



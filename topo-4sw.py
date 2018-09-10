"""#!/usr/bin/python
"""
# -*- coding: utf-8 -*-

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.util import dumpNodeConnections, custom
from mininet.node import OVSSwitch, Controller, RemoteController, CPULimitedHost
from mininet.link import TCLink, TCIntf, Link
import os, sys


class icone( Topo ):


    def __init__( self ):

        Topo.__init__( self )

        h1 = self.addHost( 'h1', ip='192.168.1.1/24', mac='00:00:00:00:00:01', defaultRoute='via 192.168.1.1', cpu=.1 )
        h2 = self.addHost( 'h2', ip='192.168.2.2/24', mac='00:00:00:00:00:02', defaultRoute='via 192.168.2.2', cpu=.1 )
        #h22 = self.addHost( 'h22', ip='192.168.2.22/24', mac='00:00:00:00:00:22', defaultRoute='via 192.168.2.22', cpu=.1 )
        h3 = self.addHost( 'h3', ip='192.168.3.3/24', mac='00:00:00:00:00:03', defaultRoute='via 192.168.3.3', cpu=.1 )
        h4 = self.addHost( 'h4', ip='192.168.4.4/24', mac='00:00:00:00:00:04', defaultRoute='via 192.168.4.4', cpu=.1 )
        
        s1 = self.addSwitch( 's1_POP' )
        s2 = self.addSwitch( 's2_FUNDAJ' )
        s3 = self.addSwitch( 's3_CPOR' )
        s4 = self.addSwitch( 's4_IFPE' )

        self.addLink( h1, s1, bw=100, delay='1.26ms', loss=0, use_htb=True )
        self.addLink( h2, s2, bw=100, delay='1.05ms', loss=0, use_htb=True )
        #self.addLink( h22, s2, bw=100, delay='1.10ms', loss=0, use_htb=True )
        self.addLink( h3, s3, bw=100, delay='1.20ms', loss=0, use_htb=True )
        self.addLink( h4, s4, bw=100, delay='1.20ms', loss=0, use_htb=True )
        
        self.addLink( s1, s2, bw=1000, delay='1.00ms', loss=0, use_htb=True )
        self.addLink( s2, s3, bw=1000, delay='1ms', loss=0, use_htb=True )
        self.addLink( s1, s4, bw=1000, delay='1.29ms', loss=0, use_htb=True )
        self.addLink( s3, s4, bw=1000, delay='1.15ms', loss=0, use_htb=True )

topos = {'icone': ( lambda: icone() ) }



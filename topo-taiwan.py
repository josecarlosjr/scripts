#!/usr/bin/python
# -*- coding: utf-8 -*-
from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSKernelSwitch, \
    UserSwitch, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.link import Link, TCLink


def topology():
    net = Mininet(controller=RemoteController, link=TCLink,
                  switch=OVSSwitch)

    # Add hosts and switches

    h1 = net.addHost('h1', mac='00:00:00:00:00:01')
    h2 = net.addHost('h2', mac='00:00:00:00:00:02')
    h3 = net.addHost('h3', mac='00:00:00:00:00:03')

    s1 = net.addSwitch('s1')
    s2 = net.addSwitch('s2')
    s3 = net.addSwitch('s3')
    c0 = net.addController('c0', controller=RemoteController,
                           ip='127.0.0.1', port=6633)

    linkopt1 = dict(bw=10, delay='1ms', loss=0)
    linkopt2 = dict(bw=8, delay='1ms', loss=0)
    linkopt3 = dict(bw=100, delay='1ms', loss=0)
    net.addLink(h1, s1, **linkopt3)
    net.addLink(h2, s1, **linkopt3)
    net.addLink(h3, s2, **linkopt3)
    net.addLink(s1, s2, **linkopt1)
    net.addLink(s1, s3, **linkopt1)
    net.addLink(s2, s3, **linkopt2)

    net.build()
    c0.start()
    s1.start([c0])
    s2.start([c0])
    s3.start([c0])

    print '*** Running CLI'
    CLI(net)

    print '*** Stopping network'
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    topology()

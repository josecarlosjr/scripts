#!/usr/bin/python
# -*- coding: utf-8 -*-

from mininet.net import Mininet
#from mininet.topo import Topo
from mininet.node import Controller, RemoteController, OVSSwitch
from mininet.log import setLogLevel, info
from mininet.term import makeTerms, makeTerm, cleanUpScreens
from mininet.link import TCLink, TCIntf, Link, Intf
from mininet.util import custom, pmonitor
from mininet.cli import CLI
from mininet.term import makeTerm, cleanUpScreens
from time import sleep
import time
import os, subprocess
import unittest

#CLASSE PARA ANALISE DE TESTE DO SCRIPT
class test( unittest.TestCase ):

    def test( self ):
        #Funções para inicialização do iperf cliente
        #Cada função representa um host
        #Falta aumentar o tempo de duração do teste do iperf de cada cliente (-t)
        def iperF2():
            print h2.cmd('iperf3 -c %s -p 5201 -u -b 20M -i 1 -t 86400 &' % h1.IP())
            return iperF2

        def iperF22():
            print h22.cmd('iperf3 -c %s -p 5202 -u -b 40M -i 1 -t 86400 &' % h11.IP())
            return iperF22

        def iperF3():
            print h3.cmd('iperf3 -c %s -p 5203 -u -b 5M -i 1 -t 86400 &' % h1.IP())
            return iperF3

        def iperF33():
            print h33.cmd('iperf3 -c %s -p 5204 -u -b 5M -i 1 -t 86400 &' % h11.IP())

        def iperF4():
            print h4.cmd('iperf3 -c %s -p 5205 -u -b 20M -i 1 -t 86400 & ' % h1.IP())
            return iperF4

        #INICIALIZA A REDE COM A FUNÇÃO MININET
        net = Mininet( topo=None, controller=RemoteController, build=False )
        info('\n')
        #Esse print net foi apenas para visualizar o que a variável "net" retorna :P. Não é, de fato, necessário
        print net, '<----- net '
        #ADICIONA O CONTROLADOR
        c0 = net.addController( 'c0', ip='192.168.56.101', port=6633 )
        info('Adding Hosts\n\n')
        #CRIA OS HOSTS E SWITCHES
        #Cada host possue um rede diferente e foi necessário adicionar uma rota padrão em cada um deles
        h1 = net.addHost( 'h1', ip='192.168.1.1/24', defaultRoute='via 192.168.1.1' )
        h2 = net.addHost( 'h2', ip='192.168.2.1/24', defaultRoute='via 192.168.2.1' )
        h3 = net.addHost( 'h3', ip='192.168.3.1/24', defaultRoute='via 192.168.3.1' )
        h4 = net.addHost( 'h4', ip='192.168.4.1/24', defaultRoute='via 192.168.4.1' )
        h11 = net.addHost( 'h11', ip='192.168.1.11/24', defaultRoute='via 192.168.1.11' )
        h22 = net.addHost( 'h22', ip='192.168.2.22/24', defaultRoute='via 192.168.2.22' )
        h33 = net.addHost( 'h33', ip='192.168.3.33/24', defaultRoute='via 192.168.3.33' )
        h44 = net.addHost( 'h44', ip='192.168.4.44/24', defaultRoute='via 192.168.4.44' )
        s1 = net.addSwitch( 's1_POP' )
        s2 = net.addSwitch( 's2_FUNDAJ' )
        s3 = net.addSwitch( 's3_CPOR' )
        s4 = net.addSwitch( 's4_IFPE' )
        #CRIA OS LINKS ENTRE HOSTS E SWITCHES
        info('Link between devices at 100Mb/s\n\n')
        net.addLink( h1, s1, cls=TCLink, bw=40 )
        net.addLink( h11, s1, cls=TCLink, bw=40 )
        net.addLink( h2, s2, cls=TCLink, bw=40 )
        net.addLink( h22, s2, cls=TCLink, bw=40 )
        net.addLink( h3, s3, cls=TCLink, bw=40 )
        net.addLink( h33, s3, cls=TCLink, bw=40 )
        net.addLink( h4, s4, cls=TCLink, bw=40 )
        net.addLink( h44, s4, cls=TCLink, bw=40 )
        net.addLink( s1, s2, cls=TCLink, bw=40 )
        net.addLink( s2, s3, cls=TCLink, bw=40 )
        net.addLink( s1, s4, cls=TCLink, bw=40 )
        net.addLink( s4, s3, cls=TCLink, bw=40 )

        try:
            #INICIA A EMULAÇÃO
            net.start()

            #CONTADOR DE 30 SEGUNDOS PARA O PROTOCOLO STP
            info('\nwaiting 30sec\n' )
            info('*** converging ring topology\n\n')
            c = 0
            for c in range (30):
                c+=1
                print(c)
                time.sleep(1)

            #LISTA TODOS OS HOSTS E SEUS LINKS
            print (net.hosts)

            #INICIA O MODO SERVIDOR NOS HOSTS h1 E h11
            info('\n\n*** Starting Iper3 Server h1 and h11\n\n')
            print h1.cmd('iperf3 -s -p 5201 &') #h2
            time.sleep(1)
            print h1.cmd('iperf3 -s -p 5203 &') #h3
            time.sleep(1)
            print h1.cmd('iperf3 -s -p 5205 &') #h4
            time.sleep(1)
            print h11.cmd('iperf3 -s -p 5202 &') #h22
            time.sleep(1)
            print h11.cmd( 'iperf3 -s -p 5204 &') #h33
            time.sleep(1)
            print h1.cmd('jobs')
            time.sleep(1)
            print h11.cmd ('jobs')


            #A EMULAÇÃO INICIA COM O TRÁFEGO DOS HOSTS h2 E h4
            #info('\n\n***Starting iperf3 clients on Host2 and Host4\n\n')
            #iperF2()
            #time.sleep(1)
            #print h2.cmd('jobs')
            #iperF4()
            #time.sleep(1)
            #print h4.cmd('jobs')

            #PAUSA DE X SEGUNDOS PARA ADICIONAR GRÁFICOS NO CACTI
            #sleep(10)

            #TRATAMENTO DE EXCEÇÕES E MENU DE MANIPULAÇÃO DA TOPOLOGIA

            try:
                info('Choose the action: \n\n')
                info('a: Link s2_FUNDAJ/s1-POP up\n')
                info('b: Link s2_FUNDAJ/s1_POP down\n')
                info('c: Link s2_FUNDAJ/s3_CPOR up\n')
                info('d: Link s2_FUNDAJ/s3_CPOR down\n')
                info('e: Start host3 - s3_CPOR \n')
                info('f: Start host22 - s2_FUNDAJ \n')
                info('g: Shutdown host22 (s2_FUNDAJ) down')
                info('h: Start host2  (s2_FUNDAJ) up\n')
                info('i: Shutdown host2 (s2_FUNDAJ) down\n')
                info('j: Start host33 - s3_CPOR \n')
                info('l: Shutdown host33 (s3_CPOR) down\n')
                info('m: Start host4 (s4_IFPE) up\n')
                info('n: Exit\n\n')
                inputKey = ''
                while inputKey != 'n':
                    inputKey = raw_input('Choose an option (just one letter): ')
                    if inputKey == 'a':
                        time.sleep(1)
                        info('\nlink s2_FUNDAJ / s1_POP UP\n')
                        net.configLinkStatus('s2_FUNDAJ','s1_POP','up')
                        time.sleep(1)
                        inputKey = ''
                    elif inputKey == 'b':
                        time.sleep(1)
                        info('\nlink s2_FUNDAJ / s1_POP DOWN\n')
                        net.configLinkStatus('s2_FUNDAJ','s1_POP','down')
                        time.sleep(1)
                        inputKey = ''
                    elif inputKey == 'c':
                        time.sleep(1)
                        info('\nlink s2_FUNDAJ / s3_CPOR UP\n')
                        net.configLinkStatus('s2_FUNDAJ','s3_CPOR','up')
                        time.sleep(1)
                        inputKey = ''
                    elif inputKey == 'd':
                        time.sleep(1)
                        info('\nlink s2_FUNDAJ \ s3_CPOR DOWN\n')
                        net.configLinkStatus('s2_FUNDAJ','s3_CPOR','down')
                        time.sleep(1)
                        inputKey = ''
                    elif inputKey == 'e':
                        time.sleep(1)
                        iperF3()
                        info('\njobs from h3\n')
                        print h3.cmd('jobs')
                        time.sleep(1)
                        inputKey=''
                    elif inputKey == 'f':
                        time.sleep(1)
                        iperF22()
                        time.sleep(1)
                        info('\n***Starting h22***\n')
                        print h22.cmd('jobs')
                        time.sleep(1)
                        inputKey = ''
                    elif inputKey == 'g':
                        time.sleep(1)
                        info('\nhost-h22 (s2_FUNDAJ) down\n')
                        print h22.cmd('killid="$(ps -eopid,cmd | egrep "*-p 5202 -u*" | cut -f1 -d " " | head -n 1)"')
                        time.sleep(1)
                        print h22.cmd('kill 9 $killid')
                        time.sleep(1)
                        print h22.cmd('unset killid')
                        time.sleep(1)
                        print h22.cmd('jobs')
                        time.sleep(1)
                        inputKey = ''
                    elif inputKey == 'h':
                        time.sleep(1)
                        info('\nhost-h2 (s2_FUNDAJ) UP\n')
                        iperF2()
                        time.sleep(1)
                        print h2.cmd('jobs')
                        time.sleep(1)
                        inputKey = ''
                    elif inputKey == 'i':
                        time.sleep(1)
                        info('\nhost-h2 (s2_FUNDAJ) DOWN\n')
                        print h2.cmd('killid="$(ps -eopid,cmd | egrep "*-p 5201 -u*" | cut -f1 -d " " | head -n 1)"')
                        time.sleep(1)
                        print h2.cmd('kill 9 $killid')
                        time.sleep(1)
                        print h2.cmd('unset killid')
                        time.sleep(1)
                        print h2.cmd('jobs')
                        inputKey = ''
                    elif inputKey == 'j':
                        time.sleep(1)
                        info('\n***Starting h33***\n')
                        iperF33()
                        time.sleep(1)
                        print h33.cmd('jobs')
                        time.sleep(1)
                        inputKey = ''
                    elif inputKey == 'l':
                        time.sleep(1)
                        info('\nhost-h33 (s3_CPOR) down\n')
                        print h33.cmd('killid="$(ps -eopid,cmd | egrep "*-p 5204 -u*" | cut -f1 -d " " | head -n 1)"')
                        time.sleep(1)
                        print h33.cmd('kill 9 $killid')
                        time.sleep(1)
                        print h33.cmd('unset killid')
                        time.sleep(1)
                        print h33.cmd('jobs')
                        inputKey = ''
                    elif inputKey == 'm':
                        time.sleep(1)
                        info('\nhost-h4 (s4_IFPE) UP\n')
                        iperF4()
                        time.sleep(1)
                        print h4.cmd('jobs')
                        time.sleep(1)
                        inputKey = ''
                    elif inputKey == 'n':
                        time.sleep(1)
                        info('\n\n***Exit***\n\n')
                        break
                    else:
                        time.sleep(1)
                        info('\n\n--Option not recognized, Repeat--\n\n')
                        inputKey = ''
            except KeyboardInterrupt:
                print '\n\nDont use Ctrl+C, Use option "m" for exit\n\n'
                #continue
            except EOFError:
                print '\n\nEOF detected: This program doesnt support EOF ending emulation...\n\n'
                print '\n\nEnding Emulation ...\n\n'
            net.stop()
        except KeyboardInterrupt:
            print '\n\n*** Aborting Emulation ***\n\n'
            net.stop()
if __name__=='__main__':
    setLogLevel('info')
    #setLogLevel('debug')
    #setLogLevel('output')
    unittest.main()
    


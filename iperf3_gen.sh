#!/bin/bash

var=0
while [ $var -lt 7 ];
do
  #atravez do ps, grep e awk ele captura a string da port_state
  processo=`ps -auxxx | grep 5202 | awk '{print$15}' | grep -v '^$'`
  if ["$processo" != "5202" ]; then
        echo "$var"º dia
        echo "Executando iperf3 novamente"
        echo `iperf3 -c 10.0.0.1 -p 5202 -u -b 20M -i 1 -t 86400`
        echo "iperf3 executado"
        var=$(($var+1))
        continue
  fi
done

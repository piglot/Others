#!/bin/bash
#This is an SOL for Oberon.

#Begin
if [[ "$1" == *-* ]]; then
    Array_Name=$1
    if [[ "$2" == "spa" || "$2" == "SPA" ]]; then 
        BMC_IP=`swarm $Array_Name --showipinfo | awk 'NR==2{print $3}'`
    elif [[ "$2" == "spb" || "$2" == "SPB" ]]; then 
        BMC_IP=`swarm $Array_Name --showipinfo | awk 'NR==2{print $4}'`
    fi
elif [[ "$1" == *.*.*.* ]]; then
    BMC_IP=$1
fi

ipmitool -I lanplus -H $BMC_IP -U admin -P Password1 sol deactivate
ipmitool -I lanplus -H $BMC_IP -U admin -P Password1 sol activate

exit 0
#End



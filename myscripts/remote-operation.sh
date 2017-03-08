#!/bin/bash
#This is a tool to run array commands remotely from users' VM and get the output on VM screen. 
#Author:    Ming.Yao@emc.com
#Time:      11/4/2016

remote_operation()
{
    IP=$1
    Timeout="timeout 10 "
    echo "IP:         $IP"
    echo "CMD:        $CMD"
    echo "Timeout:    10"
    echo "==========================================================="
    ssh -q -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l root $IP -i /c4shares/Public/ssh/id_rsa.root $Timeout$CMD
    echo "==========================================================="
}

#Begin

if [[ $1 == "*.*.*.*" ]]; then        #Input is ip address
    CMD=$2
    remote_operation $2
else                                  #Input is array name
    Array_Name=$1
    spa_ip=`swarm $Array_Name --showipinfo | awk 'NR==2{print $5}'`
    spb_ip=`swarm $Array_Name --showipinfo | awk 'NR==2{print $6}'`
    
    if [[ $2 == "spa" ]]; then        #specify operation on SPA only
        CMD=$3
        remote_operation  $spa_ip
    elif [[ $2 == "spb" ]]; then      #specify operation on SPB only
        CMD=$3
        remote_operation  $spb_ip
    else                              #Operation both on SPA and SPB
        CMD=$2
        remote_operation  $spa_ip
        remote_operation  $spb_ip
    fi
fi

exit 0

#End

#!/bin/bash
#This is a tool to get system startup states of target array.
#Author:    Ming.Yao@emc.com
#Time:      11/4/2016

CMD="system-state.sh list|grep 'system_complete'|grep -v 'hook'"
array_name=$1

spa_ip=`swarm $array_name --showipinfo | awk 'NR==2{print $5}'`
echo "SPA:  $spa_ip"
spa_state=`ssh -q -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l root $spa_ip -i /c4shares/Public/ssh/id_rsa.root $CMD`
if [[ $spa_state == "system_complete" ]];then
    echo "System complete."
else
    echo "System not complete. Please wait..."
fi

spb_ip=`swarm $array_name --showipinfo | awk 'NR==2{print $6}'`
echo "SPB:  $spb_ip"
spb_state=`ssh -q -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l root $spb_ip -i /c4shares/Public/ssh/id_rsa.root $CMD`
if [[ $spb_state == "system_complete" ]];then
    echo "System complete."
else
    echo "System not complete. Please wait..."
fi

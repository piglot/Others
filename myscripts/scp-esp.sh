#!/bin/bash
#This is a tool to transfer the ouput of ESP components to target array.
#Author:    Ming.Yao@emc.com
#Time:      11/4/2016

until [[ $yn  == "y" || $yn == "n" ]]
do
    read -p "Are you under workspace now ?(y/n)" yn
done

if [[ $yn == "n" ]]; then
    echo "So, do it..."
    exit 0
fi

if [[ -z "$1" && -z "$2" ]]; then 
    read -p "What to scp to ?(1.PhysicalPackage  2.fbecli.exe)" Component
    read -p "Input array name in Swarm:(ex. ob-s2016)" Array_Name
else
    Component=$1
    Array_Name=$2
fi

spa_ip=`swarm $Array_Name --showipinfo | awk 'NR==2{print $5}'`
spb_ip=`swarm $Array_Name --showipinfo | awk 'NR==2{print $6}'`

if [[ "$Component" == "1" || "$Component" == "pp" || "$Component" == "PP" ]]; then
    Path_from="safe/Targets/armada64_checked/kernel/exec/PhysicalPackage.sys"
    Path_to="/opt/safe/safe_binaries/kernel/exec/PhysicalPackage.sys"
elif [[ "$Component" == "2" || "$Component" == "Fbecli" || "$Component" == "fbecli.exe" ]]; then
    Path_from="safe/Targets/armada64_checked/user/exec/fbecli.exe"
    Path_to="/opt/safe/safe_binaries/user/exec/fbecli.exe"
elif [[ "$Component" == "3" || "$Component" == "esp" || "$Component" == "ESP" ]]; then
    Path_from="safe/Targets/armada64_checked/kernel/exec/espkg.sys"
    Path_to="/opt/safe/safe_binaries/kernel/exec/espkg.sys"
fi

CMD1="scp $Path_from root@$spa_ip:$Path_to"
echo $CMD1
eval $CMD1

CMD2="scp $Path_from root@$spb_ip:$Path_to"
echo $CMD2
eval $CMD2

exit 0

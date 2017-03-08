#!/bin/bash

#Begin

if [[ $1 =~ ^(((\d{1,2})|(1\d{2,2})|(2[0-4][0-9])|(25[0-5]))\.){3,3}((\d{1,2})|(1\d{2,2})|(2[0-4][0-9])|(25[0-5]))$ ]]; then        #Input is ip address
    echo $1
    exit 0
    IP=$1
elif [[ $1 == *-* ]]; then                                 #Input is array name
    echo $1
    exit 0
    Array_Name=$1
    if [[ "$2" == "spa" || "$2" == "SPA" ]]; then
        IP=`swarm $Array_Name --showipinfo | awk 'NR==2{print $5}'`
    elif [[ "$2" == "spb" || "$2" == "SPB" ]]; then
        IP=`swarm $Array_Name --showipinfo | awk 'NR==2{print $6}'`
    fi
fi

Image=$3
ssh -q -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l root $IP -i /c4shares/Public/ssh/id_rsa.root  wget ftp://10.244.32.177/image/$3

exit 0

#End


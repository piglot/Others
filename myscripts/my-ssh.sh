#!/bin/bash

my_echo()
{
    type=$1
    Message=$2
    case $type in
        "-I")
            echo -e "\e[32;40;1m$Message\e[0m"
            ;;
        "-W")
            echo -e "\e[33;40;1m$Message\e[0m"
            ;;
        "-E")
            echo -e "\e[31;40;1m$Message\e[0m"
            ;;
        *)
            exit 1
            ;;
    esac
}

Array_Name=$1

if [[ "$2" == "spa" || "$2" == "SPA" ]]; then
    IP=`swarm $Array_Name --showipinfo | awk 'NR==2{print $5}'`
elif [[ "$2" == "spb" || "$2" == "SPB" ]]; then
    IP=`swarm $Array_Name --showipinfo | awk 'NR==2{print $6}'`
fi

my_echo -I "Trying to connect to $IP via ssh..."

ssh -q -o ConnectTimeout=5 -o StrictHostKeyChecking=no -l root $IP -i /c4shares/Public/ssh/id_rsa.root
if [[ $? -ne 0 ]]; then
    my_echo -E "Connect Timeout!" 
else
    my_echo -I "Disconnected from $IP"
fi


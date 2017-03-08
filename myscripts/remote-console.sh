#!/bin/bash

Array_name=$1
SP=$2

User="admin"
Password="Password1"

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

#Begin
if [[ "$SP" == "spa" || "$SP" == "SPA" ]]; then
    BMC_IP=`swarm $Array_name --showipinfo | awk 'NR==2{print $3}'`
elif [[ "$SP" == "spb" || "$SP" == "SPB" ]]; then
    BMC_IP=`swarm $Array_name --showipinfo | awk 'NR==2{print $4}'`
fi

my_echo -I "$SP BMC IP:        $BMC_IP"

Console_deactivate="ipmitool -I lanplus -H $BMC_IP -U $User -P $Password sol deactivate"
Console_activate="ipmitool -I lanplus -H $BMC_IP -U $User -P $Password sol activate"

my_echo -W "$Console_deactivate"
$Console_deactivate

my_echo -W "$Console_activate"
$Console_activate

exit 0

#End

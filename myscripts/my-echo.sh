#!/bin/bash

my_echo()
{
    type=$1
    Message=$2
    case $type in
        "-I")
            echo $Message
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

my_echo $1 $2

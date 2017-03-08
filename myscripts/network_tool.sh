#!/bin/bash
DIR=`dirname $0`
cd $DIR
session_name=network_tool
screen -S $session_name -d -m bash ./goagent
screen -S $session_name -X screen bash ./dnsproxy
screen -S $session_name -X screen bash ./startproxy

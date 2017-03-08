#!/bin/bash

OPENGROK_SRC="/var/opengrok/src/"
ACCUREV="/opt/accurev/bin/accurev"
LOG="/home/c4dev/opengrok/my_scripts/"
DATE=/bin/date
timestamp=`$DATE -d today`

echo "[$timestamp]Removing old log..."
#remove old log
[[ -f $LOG/log ]] && rm $LOG/log

echo "[$timestamp]Purge files..."
for WORKSPACE in $(ls $OPENGROK_SRC|grep og)
do 
    cd $OPENGROK_SRC/$WORKSPACE;$ACCUREV stat -nO |tr -s ' '|cut -d ' ' -f 1 | xargs $ACCUREV purge
    #echo "workspace: $WORKSAPCE" | sudo $MAILTO -s "accurev purge error" Ming.Yao@emc.com
done

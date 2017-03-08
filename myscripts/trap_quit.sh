#!/bin/bash
trap "bash $0 && kill $$" QUIT

i=0
while (( 1 ))
do
    echo "hello $i"
    sleep 1
    (( i++ ))
done


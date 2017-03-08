#!/bin/bash

#for (( i=0;i<10;i++ ))
#do
#    ping 10.62.34.$i &
#    sleep 2
#done
for i in 0 1 2 3 4 5 6 7 8 9 
do
    ping 10.62.34.$i &
    sleep 2
done

wait
exit 0

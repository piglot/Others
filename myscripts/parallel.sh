#!/bin/bash

loop1()
{
    for (( i=0;i<10;i++ ))
    do
        echo `hostname`
        sleep 2
    done
}

loop2()
{
    for (( i=0;i<10;i++ ))
    do
        echo `date`
        sleep 2
    done
}
{ loop1
} &
{ loop2
} &
wait
exit 0

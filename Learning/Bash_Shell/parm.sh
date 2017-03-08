#!/bin/bash

i=0
for parm in "$@"
do
    i=$((i+1))
    echo "You typed $i"th" parm is: $parm"
done


#!/bin/bash

array_name="ob-s2016"

spa_ip="10.32.177.232"
spb_ip="10.32.177.233"

remote_op_spa="ssh -q -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l root $spa_ip -i /c4shares/Public/ssh/id_rsa.root"
remote_op_spb="ssh -q -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l root $spb_ip -i /c4shares/Public/ssh/id_rsa.root"

#eval $remote_op_spa "\"echo yes;echo no\""
#eval $remote_op_spb "\"ls;ping peer\""

screen  -S $array_name-spa-op -d -m $remote_op_spa "ls;ping $spa_ip" 
screen  -S $array_name-spb-op -d -m eval $remote_op_spb "\"ls;ping peer\""

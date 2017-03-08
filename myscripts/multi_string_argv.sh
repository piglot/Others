#!/bin/bash

ssh_remote_op()
{
    ip=$1
    all='('$@')'
    cmd=${all[1]}
    #eval $SSH_COMMAND $ip "$@"
    echo $cmd
    return $?
}

VNXE_SSH_KEY="/c4shares/Public/ssh/id_rsa.root"
SSH_COMMAND="ssh -o ServerAliveInterval=10 -o ServerAliveCountMax=1 -o ConnectTimeout=10 -o User=root-T -i $VNXE_SSH_KEY "

ssh_remote_op 10.32.177.232  "cat ./version"

#!/bin/bash

until [[ "$yn" == "y" || "$yn" == "n" ]]
do
    echo "Would you want to do something?(y/n)"
    read -n 1 -s yn
done
if [[ "$yn" == "y" ]]; then
    echo "Do something..."
fi


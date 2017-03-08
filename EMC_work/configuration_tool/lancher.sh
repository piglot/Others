#!/bin/bash
MAILTO=/usr/bin/mailto

#fab main
if [[ -f "/home/c4dev/work/tool/test.xls" ]]; then
	sudo $MAILTO -s "Array/testbed Configuration Info" Ming.Yao@emc.com
fi

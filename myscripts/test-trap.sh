#!/bin/bash

trap "echo normal exit" EXIT
trap "echo debug exit" DEBUG
trap "echo error exit" ERR

exit 0

#!/bin/bash

set -e

if [ -n $1 ]; then
	NUM=$1
else
	NUM=9
fi

DIRS=$(ls -1 | grep [0-${NUM}])
rc=0

dock() {
	if [ -e /usr/bin/docker ]; then
		docker $@
	else
		docker.io $@
	fi
}

function build-image() {
	if ! dock build -t $1 $1; then
		rc=$?
		echo "non zero exito status from docker build -t $1 $1: $rc"
	fi
}

for x in $DIRS
do
	echo
	echo "starting to create image from $x"
	echo
	build-image $x
done

exit $rc

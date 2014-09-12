#!/bin/bash

set -e

test -x ./build.sh
test -d ./001-ubuntu

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
		rc=1
		echo "non zero exito status from docker build -t $1 $1: $rc"
	fi
}

for stage in [0-9][0-9][0-9]-*
do
	echo
	echo "starting to create image from $stage"
	echo
	build-image $stage
	[ $rc -ne 0 ] && exit $rc
done

exit $rc

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

function run-image() {
	if ! (docker.io run --privileged=true -i --name=$1 $1 -c '/build/build_tplino-core.sh' && dock commit $1 $1) ; then
		rc=1
		echo "non zero exito status from docker run --rm -t -i --name=$1 $1: $rc"
	fi
}

for stage in [0-9][0-9][0-9]-*
do
	if [ -e $stage/privileged ]; then
		echo
		echo "starting to create image from $stage"
		echo
		build-image $stage
		run-image $stage
		[ $rc -ne 0 ] && exit $rc
	else
		echo
		echo "starting to create image from $stage"
		echo
		build-image $stage
		[ $rc -ne 0 ] && exit $rc
	fi
done

exit $rc

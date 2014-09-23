#!/bin/bash

set -e

test -x ./build.sh
test -d ./001-ubuntu

TAG=$(date +%F-%H-%M)
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
	NAME=$TAG-$1
	if ! (docker.io run --privileged=true -i --name=$NAME $1 -c "/build/build_$1.sh" && dock commit $NAME $NAME) ; then
		rc=1
		echo "non zero exito status from docker run --rm -t -i --name=$NAME $NAME: $rc"
	fi
}

for stage in [0-9][0-9][0-9]-*
do
	if [ -e $stage/run ]; then
		echo
		echo "starting to create image from $stage"
		echo
		build-image $stage
		run-image $stage
		[ $rc -ne 0 ] && exit $rc
	elif [ -e $stage/build ]; then
		echo
		echo "starting to create image from $stage"
		echo
		build-image $stage
		[ $rc -ne 0 ] && exit $rc
	else
		echo "run or build not specified"
	fi
done

exit $rc

#!/bin/bash

set -e

test -x ./build.sh
test -d ./001-ubuntu

source ../docker_api.sh

IFS=$'\n'
TAG=$USER
rc=0

for stage in [0-9][0-9][0-9]-*
do
	[ ! -e $stage/Dockerfile ] && exit 1
	DOCKERFILE=$(cat $stage/Dockerfile)
	for LINE in $DOCKERFILE
	do
		$LINE
	done
done

exit $rc

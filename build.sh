#!/bin/bash

set -e

test -x ./build.sh
test -d ./001-ubuntu

. ./docker_api.sh

for stage in [0-9][0-9][0-9]-*
do
	[ ! -x $stage/build.sh ] && exit 1
	cd $stage
	STAGE=$(grep "^\s*STAGE=" ./build.sh | cut -d= -f2-)
	./Dockerfile.sh
	_ENDSTAGE
	LASTSTAGE=${STAGE}

	cd -
done

exit $rc

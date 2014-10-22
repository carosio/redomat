#!/bin/bash

set -e

[ ! -x build.sh ] && echo "build.sh is dose not exist or is not executable" && exit 1
[ ! -x docker_api.sh ] && echo "docker_api.sh is dose not exist or is not executable" && exit 1
mkdir -pv ./build-logs

. ./docker_api.sh

for STAGE in [0-9][0-9][0-9]-*
do
	[ ! -x $STAGE/Dockerfile.sh ] && ERROR "$STAGE/Dockerfile.sh is does not exist or is not executable"
	export STAGE
	export CURRENT_IMAGE=${BUILDID}-${STAGE}-current
	[ -n "$LASTSTAGE" ] && export LASTSTAGE
	(
	cd $STAGE
	export LOCATION=$(pwd)
	[ -n "$LASTSTAGE" ] && export PREVIOUS_STAGE=${BUILDID}-${LASTSTAGE}
	./Dockerfile.sh | tee ../build-logs/${BUILDID}-${STAGE}.log
	SQUASH
	_ENDSTAGE
	)
	LASTSTAGE=${STAGE}
done

#!/bin/bash

set -e

[ ! -x build.sh ] && echo "build.sh is dose not exist or is not executable" && exit 1
[ ! -x docker_api.sh ] && echo "docker_api.sh is dose not exist or is not executable" && exit 1

. ./docker_api.sh

for STAGE in [0-9][0-9][0-9]-*
do
	[ ! -x $STAGE/Dockerfile.sh ] && echo "$STAGE/Dockerfile.sh is dose not exist or is not executable" && exit 1
	cd $STAGE
	export STAGE
	./Dockerfile.sh
	SQUASH
	_ENDSTAGE
	LASTSTAGE=${STAGE}
	cd -
done

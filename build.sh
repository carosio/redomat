#!/bin/bash

set -e

[ ! -x build.sh ] && echo "build.sh is dose not exist or is not executable" && exit 1
[ ! -x docker_api.sh ] && echo "docker_api.sh is dose not exist or is not executable" && exit 1

. ./docker_api.sh

for stage in [0-9][0-9][0-9]-*
do
	[ ! -x $stage/Dockerfile.sh ] && echo "$stage/Dockerfile.sh is dose not exist or is not executable" && exit 1
	cd $stage
	STAGE=$(grep "^\s*STAGE=" ./Dockerfile.sh | cut -d= -f2-)
	[ -z $STAGE ] && echo "STAGE variable not set" && exit 1
	echo "starting stage $STAGE"
	./Dockerfile.sh
	SQUASH
	_ENDSTAGE
	LASTSTAGE=${STAGE}
	cd -
done

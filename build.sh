#!/bin/bash

set -e

[ $1 = "-h" ] && echo "./build.sh <STAGE> <BUILD-ID>" && exit 0

[ ! -x build.sh ] && echo "build.sh is dose not exist or is not executable" && exit 1
[ ! -x docker_api.sh ] && echo "docker_api.sh is dose not exist or is not executable" && exit 1

### setting a stage to jump in to and test if this stage exists ###
STAGES=([0-9][0-9][0-9]-*)
CHECK=0

[ ! -z $1 ] && [ ${1} != "all" ] && for STAGE in ${STAGES[@]}; do echo $STAGE | grep "$1" && CHECK=1; done || CHECK=1
[ $CHECK -eq 0 ] && echo "no such stage" && exit 1;
[ ! -z $1 ] && BEGIN=$1 && CHECK=0 && echo "setting new startingpoint" || CHECK=1

echo $CHECK

###

### creating log directories if they do not exist
mkdir -pv ./build-logs

### reading all docker related functions
. ./docker_api.sh

### overwrite BUILDID if it is passed
[ ! -z "$2" ] && export BUILDID=$2 && export CONTAINER=${BUILDID}-container

#skip everything till stage = begin and then overwrite the Laststaege
### running through the stages specified in STAGES
for STAGE in ${STAGES[@]}
do
	echo "Starting to build stage: $STAGE"
        echo "BuildID: $BUILDID"
	[ ! -d $STAGE ] && ERROR "no such stage"
	[ ! -x $STAGE/Dockerfile.sh ] && ERROR "$STAGE/Dockerfile.sh is does not exist or is not executable"
	export STAGE
	export CURRENT_IMAGE=${BUILDID}-${STAGE}-current
	[ -n "$LASTSTAGE" ] && export LASTSTAGE

### only run the stage if CHECK is 1
	echo $BEGIN $STAGE
	[ ! -z $1 ] && [ ${BEGIN} = ${STAGE} ] && CHECK=1 # || CHECK=0
	[ ! -z $1 ] && [ ${1} = "all" ] && CHECK=1
	(
	echo $CHECK
	cd $STAGE
	export LOCATION=$(pwd)
	[ -n "$LASTSTAGE" ] && export PREVIOUS_STAGE=${BUILDID}-${LASTSTAGE}
	if [ $CHECK -eq 1 ]; then
		./Dockerfile.sh | tee ../build-logs/${BUILDID}-${STAGE}.log
		SQUASH
		_ENDSTAGE
	else
	export PREVIOUS_STAGE=${BUILDID}-${LASTSTAGE}
	fi
	)
	LASTSTAGE=${STAGE}
done

### remove unneeded untagged images
docker rmi -f $(docker images | grep 'none' | awk {'print $3'})

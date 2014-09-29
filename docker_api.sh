#!/bin/bash

set -e

[ -z "$USER" ] && USER=$(id -un)

BUILDID=$(date +%F-%H%M%S)-$$-$USER
CONTAINER=${BUILDID}-container
INTER_IMAGE=${BUILDID}-${STAGE}-lastrun
FINAL_IMAGE=${BUILDID}-${STAGE}-end_of_stage
LAST_IMAGE=${BUILDID}-${LASTSTAGE}-end_of_stage

function FROM() {
	[ -z $1 ] && echo "The RUN command needs at leased one argument" && exit 1
	IMAGE=$1

	[ -z $IMAGE ] && echo "IMAGE variable not set" && exit 1
	[ -z $INTER_IMAGE ] && echo "INTER_IMAGE variable not set" && exit 1

	if [ ${IMAGE}="_PREVIOUS" ]; then
		[ -z $LAST_IMAGE ] && echo "LAST_IMAGE variable not set" && exit 1
		IMAGE=$LAST_IMAGE
	fi
	docker tag $IMAGE $INTER_IMAGE
}

function ADD() {
	FILE=$1
	TARGET=$2

	[ -z $LOCATION ] && echo "LOCATION variable not set" && exit 1
	[ -z $FILE ] && echo "FILE variable not set" && exit 1
	[ -z $TARGET ] && echo "TARGET variable not set" && exit 1

	RUN --volume="$LOCATION:/files" "test -d $TARGET || mkdir -p $TARGET && cp -v -r /files/$FILE $TARGET"
}

function RUNP() {
	RUN --privileged=true "$@"
}

function RUN() {

	[ -z $1 ] && echo "The RUN command needs at leased one argument" && exit 1
	[ -z $CONTAINER ] && echo "CONTAINER variable not set" && exit 1
	[ -z $INTER_IMAGE ] && echo "INTER_IMAGE variable not set" && exit 1

	docker_run_args=""
	#read first char see if it is an -
	while [ "${1:0:1}" = "-" ]
	do
		docker_run_args="$docker_run_args $1"
		shift
	done

	echo "$@" | docker run $docker_run_args -i --name=$CONTAINER $INTER_IMAGE /bin/bash -- /dev/stdin \
			  && docker commit $CONTAINER $INTER_IMAGE \
			  && docker rm $CONTAINER
}

function ENV() {
	echo "NYI"
	exit 1
}

function SQUASH() {
	[ -z $CONTAINER ] && echo "CONTAINER variable not set" && exit 1
	[ -z $INTER_IMAGE ] && echo "INTER_IMAGE variable not set" && exit 1

	docker run --name=$CONTAINER $INTER_IMAGE echo "exporting docker image"
	docker export $CONTAINER | docker import - $INTER_IMAGE
}

function _ENDSTAGE
{
	[ -z $FINAL_IAMGE ] && echo "FINAL_IAMGE variable not set" && exit 1
	[ -z $INTER_IMAGE ] && echo "INTER_IMAGE variable not set" && exit 1

	[ -z $(docker instpect $INTER_IMAGE) ] && echo "no container to finalize the image from" && exit 1
	docker tag $INTER_IMAGE $FINAL_IMAGE
}

export -f  FROM
export -f  ADD
export -f  RUNP
export -f  RUN
export -f  ENV
export -f  SQUASH
export -f  _ENDSTAGE

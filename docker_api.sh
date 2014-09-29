#!/bin/bash

set -e

function ERROR() {
	echo "$@"
	exit 1
}

[ -z "$USER" ] && USER=$(id -un)

export BUILDID=$(date +%F-%H%M%S)-$$-$USER
export CONTAINER=${BUILDID}-container

function STAGE() {
	[ ! "$STAGE" = "$1" ] && ERROR "STAGE directive conflicts with directory name"
}

function FROM() {
	[ -z $1 ] && ERROR "The FROM command needs at leased one argument"
	IMAGE=$1

	[ -z $IMAGE ] && ERROR "IMAGE variable not set"
	[ -z $INTER_IMAGE ] && ERROR "INTER_IMAGE variable not set"

	if [ ${IMAGE} = "_PREVIOUS" ]; then
		[ -z $LAST_IMAGE ] && ERROR "LAST_IMAGE variable not set"
		IMAGE=$LAST_IMAGE
	fi
	docker tag $IMAGE $INTER_IMAGE
}

function ADD() {
	FILE=$1
	TARGET=$2

	[ -z $LOCATION ] && ERROR "LOCATION variable not set"
	[ -z $FILE ] && ERROR "FILE variable not set"
	[ -z $TARGET ] && ERROR "TARGET variable not set"

	RUN --volume="$LOCATION:/files" "test -d $TARGET || mkdir -p $TARGET && cp -v -r /files/$FILE $TARGET"
}

function RUN() {

	[ -z $1 ] && ERROR "The RUN command needs at leased one argument"
	[ -z $CONTAINER ] && ERROR "CONTAINER variable not set"
	[ -z $INTER_IMAGE ] && ERROR "INTER_IMAGE variable not set"

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
	ERROR "NYI"
}

function SQUASH() {
	[ -z $CONTAINER ] && ERROR "CONTAINER variable not set"
	[ -z $INTER_IMAGE ] && ERROR "INTER_IMAGE variable not set"

	docker run --name=$CONTAINER $INTER_IMAGE echo "exporting docker image"
	docker export $CONTAINER | docker import - $INTER_IMAGE
}

function _ENDSTAGE
{
	[ -z $FINAL_IAMGE ] && ERROR "FINAL_IAMGE variable not set"
	[ -z $INTER_IMAGE ] && ERROR "INTER_IMAGE variable not set"

	[ -z $(docker instpect $INTER_IMAGE) ] && ERROR "no container to finalize the image from"
	docker tag $INTER_IMAGE $FINAL_IMAGE
}

export -f ERROR
export -f STAGE
export -f FROM
export -f ADD
export -f RUN
export -f ENV
export -f SQUASH
export -f _ENDSTAGE

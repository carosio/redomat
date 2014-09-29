#!/bin/bash

set -e

function die() {
	echo "$@"
	exit 1
}

[ -z "$USER" ] && USER=$(id -un)

export BUILDID=$(date +%F-%H%M%S)-$$-$USER
export CONTAINER=${BUILDID}-container

function STAGE() {
	[ ! "$STAGE" = "$1" ] && die "STAGE directive conflicts with directory name"
}

function FROM() {
	[ -z $1 ] && die "The FROM command needs at leased one argument"
	IMAGE=$1

	[ -z $IMAGE ] && die "IMAGE variable not set"
	[ -z $INTER_IMAGE ] && die "INTER_IMAGE variable not set"

	if [ ${IMAGE} = "_PREVIOUS" ]; then
		[ -z $LAST_IMAGE ] && die "LAST_IMAGE variable not set"
		IMAGE=$LAST_IMAGE
	fi
	docker tag $IMAGE $INTER_IMAGE
}

function ADD() {
	FILE=$1
	TARGET=$2

	[ -z $LOCATION ] && die "LOCATION variable not set"
	[ -z $FILE ] && die "FILE variable not set"
	[ -z $TARGET ] && die "TARGET variable not set"

	RUN --volume="$LOCATION:/files" "test -d $TARGET || mkdir -p $TARGET && cp -v -r /files/$FILE $TARGET"
}

function RUN() {

	[ -z $1 ] && die "The RUN command needs at leased one argument"
	[ -z $CONTAINER ] && die "CONTAINER variable not set"
	[ -z $INTER_IMAGE ] && die "INTER_IMAGE variable not set"

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
	die "NYI"
}

function SQUASH() {
	[ -z $CONTAINER ] && die "CONTAINER variable not set"
	[ -z $INTER_IMAGE ] && die "INTER_IMAGE variable not set"

	docker run --name=$CONTAINER $INTER_IMAGE echo "exporting docker image"
	docker export $CONTAINER | docker import - $INTER_IMAGE
}

function _ENDSTAGE
{
	[ -z $FINAL_IAMGE ] && die "FINAL_IAMGE variable not set"
	[ -z $INTER_IMAGE ] && die "INTER_IMAGE variable not set"

	[ -z $(docker instpect $INTER_IMAGE) ] && die "no container to finalize the image from"
	docker tag $INTER_IMAGE $FINAL_IMAGE
}

export -f die
export -f STAGE
export -f FROM
export -f ADD
export -f RUN
export -f ENV
export -f SQUASH
export -f _ENDSTAGE

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

# initializes the "current-image-pointer" ( $CURRENT_IMAGE )
# as a docker-commit
function FROM() {
	[ -z $1 ] && ERROR "The FROM command needs at least one argument"
	FROMIMAGE=$1

	[ -z $FROMIMAGE ] && ERROR "FROMIMAGE argument not given"

	if [ ${FROMIMAGE} = "_PREVIOUS" ]; then
		[ -z "$PREVIOUS_STAGE" ] && ERROR "unable to resolve FROM _PREVIOUS."
		FROMIMAGE=$PREVIOUS_STAGE
	fi
	docker tag $FROMIMAGE $CURRENT_IMAGE
}

function ADD() {
	FILE=$1 ; shift
	TARGET=$1 ; shift
	TARGET_dir=${TARGET%/*}

	[ -z $LOCATION ] && ERROR "LOCATION variable not set"
	[ -z $FILE ] && ERROR "FILE argument not given"
	[ -z $TARGET ] && ERROR "TARGET argument not given"
	[ -z $TARGET_dir ] && ERROR "Woopsie TARGET_dir could not be determined"

	RUN --volume="$LOCATION:/files" "mkdir -p $TARGET_dir && cp -rv /files/$FILE $TARGET"
}

function RUN() {
	[ -z $1 ] && ERROR "The RUN command needs at least one argument"

	[ -z $CONTAINER ] && ERROR "CONTAINER variable not set"
	[ -z $CURRENT_IMAGE ] && ERROR "CURRENT_IMAGE argument not given (RUN)"

	docker_run_args=""
	#read first char see if it is an -
	while [ "${1:0:1}" = "-" ]
	do
		docker_run_args="$docker_run_args $1"
		shift
	done

	echo "$@" | docker run $docker_run_args -i --name=$CONTAINER $CURRENT_IMAGE /bin/bash -- /dev/stdin \
			  && docker commit $CONTAINER $CURRENT_IMAGE \
			  && docker rm $CONTAINER
}

function ENV() {
	ERROR "NYI"
}

function ENTRYPOINT() {
	ENTRYPOINT="$1"
	[ -z $ENTRYPOINT ] && ERROR "no ENTRYPOINT set"
	[ -z $CONTAINER ] && ERROR "CONTAINER variable not set"
	[ -z $CURRENT_IMAGE ] && ERROR "CURRENT_IMAGE variable not set (SQUASH)"

	docker run --entrypoint="$ENTRYPOINT" --name=$CONTAINER $CURRENT_IMAGE \
			  && docker commit $CONTAINER $CURRENT_IMAGE \
			  && docker rm $CONTAINER
}

function SQUASH() {
	[ -z $CONTAINER ] && ERROR "CONTAINER variable not set"
	[ -z $CURRENT_IMAGE ] && ERROR "CURRENT_IMAGE variable not set (SQUASH)"

	docker run --name=$CONTAINER $CURRENT_IMAGE echo "exporting docker image"
	docker export $CONTAINER | docker import - $CURRENT_IMAGE
	docker rm $CONTAINER
}

function _ENDSTAGE
{
	[ -z $CURRENT_IMAGE ] && ERROR "CURRENT_IMAGE variable not set"

	docker tag $CURRENT_IMAGE ${BUILDID}-${STAGE}
}

export -f ERROR
export -f STAGE
export -f FROM
export -f ADD
export -f RUN
export -f ENV
export -f ENTRYPOINT
export -f SQUASH
export -f _ENDSTAGE

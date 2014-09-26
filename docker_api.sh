#!/bin/bash

[ -z "$USER" ] && USER=$(id -un)

BUILDID=$(date +%F-%H%M%S)-$$-$USER

function FROM() {
ASSERTs...

	image=$1
	assert -z image
	if image==_PREVIOUS ... -> image=${BUILDID}-${LASTSTAGE}-end_of_stage
	docker tag $image ${BUILDID}-${STAGE}-pre
}

function ADD() {
	FILE=$1
	LOCATION=$2
ASSERTs...
	RUN --volume="$(pwd ein process nur fuer pwd??):/files" "test -d $LOCATION || mkdir -p $LOCATION && cp -v -r /files/$FILE $LOCATION/."
}

function RUNP() {
	RUN --privileged=true "$@"
}

function RUN() {
	[ -z "$1" .... bark
	docker_run_args=""
	#read first char see if it is an -
	while [ "${1:0:1}" = "-" ]
	do
		docker_run_args="$docker_run_args $1"
		shift
	done
	echo "$@" | docker run $docker_run_args -i --name=$NAME $NAME /bin/bash -- /dev/stdin \
			  && docker commit ${BUILDID}-container ${BUILDID}-${STAGE}-lastrun \
			  && docker rm $NAME
}

function ENV() {
	echo "NYI"
	exit 1
}

function SQUASH() {
	docker run --name=$NAME $NAME echo "exporting docker image"
	docker export $NAME | docker import - buildid${STAGE}-last..
}
_ENDSTAGE...
{
	tag..
	${BUILDID}-${STAGE}-end_of_stage
}


export -f ADD
export -f _ENDSTAGE
export -f RUN ..

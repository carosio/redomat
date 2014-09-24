#!/bin/bash

NAME=$STAGE-$USER

function FROM() {
	docker tag $1 $NAME
}

function ADD() {
	FILE=$1
	LOCATION=$2
	RUN --volume="$(pwd):/files" "test -d $LOCATION || mkdir -p $LOCATION && cp -r /files/$FILE $LOCATION/."
}

function RUNP() {
	RUN --privileged=true "$@"
}

function RUN() {
	docker_run_args=""
	#read first char see if it is an -
	while [ "${1:0:1}" = "-" ]
	do
		docker_run_args="$docker_run_args $1"
		shift
	done
	echo "$@" | docker run $docker_run_args --name=$NAME $NAME bash -- /dev/stdin \
			  && docker commit $NAME $NAME \
			  && docker rm $NAME
}

function ENV() {
	echo "NYI"
	exit 1
}

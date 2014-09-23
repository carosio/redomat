#!/bin/bash

NAME=$STAGE-$USER

function FROM() {
	docker tag $1 $NAME
}

function RUNP() {
	RUN --privileged=true "$@"
}

function ADD() {
	FILE=$1
	LOCATION=$2

	if [ -n $3 ]; then
		FILENAME=$3
	else
		FILENAME='.'
	fi

	docker run --name=$NAME -v $(pwd):/files $NAME bash -c "test -d $LOCATION || mkdir -p $LOCATION && cp -r /files/$FILE $LOCATION/$FILENAME" \
			  && docker commit $NAME $NAME \
			  && docker rm $NAME
}

function RUN() {
	docker_run_args=""
	#read first char see if it is an -
	while [ "$1[1]" = "-" ]
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

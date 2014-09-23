#!/bin/bash

NAME=001-ubuntu-$1

function FROM() {
	docker tag $1 $NAME
}

function RUN() {
	CMD=$@
	docker run --name=$NAME $NAME bash -c "$CMD" \
			  && docker commit $NAME $NAME \
			  && docker rm $NAME
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

function RUNP() {
	CMD=$@
	docker run --privileged=true --name=$NAME $NAME bash -c "$CMD" \
			  && docker commit $NAME $NAME \
			  && docker rm $NAME
}

#!/bin/bash

DIRS=$(ls -1 | grep [0-9])

if [ -n ${CI_BUILD_ID} ]; then
	sed -i "s/@@CI_BUILD_ID@@/${CI_BUILD_ID}/g" 002-tposs-4.3.0-alpha/Dockerfile
	sed -i "s/@@CI_BUILD_REF@@/${CI_BUILD_REF}/g" 002-tposs-4.3.0-alpha/Dockerfile
fi

dock() {
	if [ -e /usr/bin/docker ]; then
		docker $@
	else
		docker.io $@
	fi
}

for x in $DIRS
do
	echo
	echo "starting to create image from $x"
	echo
	dock build -t $x $x
done


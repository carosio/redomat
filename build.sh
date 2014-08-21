#!/bin/bash

DIRS=$(ls -1 | grep [0-9])

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
	[ -e $x/setup.sh ] && $x/setup.sh
	dock build -t $x $x
done

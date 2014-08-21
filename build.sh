#!/bin/bash

DIRS=$(ls -1 | grep [0-9])

for x in $DIRS
do
	echo
	echo "starting to create image from $x"
	echo
	docker build -t $x $x
done


#!/bin/bash

DIRS=$(ls -1 | grep [0-9])

for x in $DIRS
do
	docker build -t $x $x
done


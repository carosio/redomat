#!/bin/bash

set -e

test -x ./build.sh
test -d ./001-ubuntu

for stage in [0-9][0-9][0-9]-*
do
	[ ! -x $stage/build.sh ] && exit 1
	cd $stage
	./build.sh
	cd -
done

exit $rc

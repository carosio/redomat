#!/bin/sh
#
# (c) Travelping GmbH - "Tobias Hintze" <thintze+git@travelping.com>
#
# Just a tiny little tool to monitor (as in `docker logs -f`)
# one running container at a time.
#
# Known Issue: If you have more than one container running
# at the same time, `docker logs` command will bark at you...
#
while true
do
	running=$(docker ps -f status=running -q)
	if [ -z "$running" ]
	then
		sleep .5
		echo -n .
		continue
	fi
	echo
	echo "Following log for container [$running]:"
	docker logs -f "${running}"
done


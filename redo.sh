#!/bin/bash

input_file=/dev/stdin

xmlstarlet sel -t -m /manifest/buildstage/bitbake_target \
	-v 'text()' -o " " -v '@command' -o " "  --nl $input_file | while read target command
do
	cmd="bitbake"
	[ -n "$command" ] && cmd="$cmd -c $command"
	cmd="$cmd $target"


	echo "$cmd"

done

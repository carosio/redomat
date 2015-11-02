#!/bin/bash -e
# 
# This script allows deeper inspection of ipk packages
# then usually possible with a single command.
# It extracts the package to a $TMP directory and cleans
# up when it terminates.
# Functions provided by subcommands:
# * control: show control file
# * flist: show list of files (package contents)
# * name: show package name
# * deps: list package dependencies
# * fingerprint: calculate a normalized hash of the package contents
#
# Author: Tobias Hintze - Travelping GmbH
#

TMP=`mktemp -d`

function tmp_cleanup() {
	if [ -z "$NO_CLEANUP" ] ; then
		# just be paranoid:
		echo "$TMP" | grep -q "/tmp/tmp." && rm -rf "$TMP"
	else
		echo "preserved due to \$NO_CLEANUP: $TMP" 1>&2
	fi
}
trap tmp_cleanup EXIT

abs() {
	[ "${1:0:1}" != / ] && printf "`pwd`/"
	printf "$1\n"
}

control() {
	ipk="$(abs $1)"
	(
	cd $TMP
	ar xf $ipk control.tar.gz
	tar xf control.tar.gz ./control
	cat control
	)
}

flist() {
	ipk="$(abs $1)"
	(
	cd $TMP
	ar xf $ipk data.tar.gz
	tar tf data.tar.gz
	)
}

fingerprint() {
	ipk="$(abs $1)"
	(
	cd $TMP
	ar xf $ipk data.tar.gz control.tar.gz
	mkdir data-fp-unpack
	tar xf data.tar.gz -C data-fp-unpack

	mkdir ctrl-fp-unpack
	tar xf control.tar.gz -C ctrl-fp-unpack

	grep ^Package: ctrl-fp-unpack/control
	# cut off build from version for fingerprinting
	grep ^Version: ctrl-fp-unpack/control
	sed --in-place -e 's/\(^Version: .*\)-[^-]*$/\1/' ctrl-fp-unpack/control
	printf "Base-"
	grep ^Version: ctrl-fp-unpack/control

	printf "Package-Fingerprint: "
	(
	find data-fp-unpack ctrl-fp-unpack -type f -printf "%M %U:%G %p " -exec sha1sum {} \;
	find data-fp-unpack ctrl-fp-unpack -not -type f -printf "%M %U:%G %p %l\n"
	) | sort -k3 | sha1sum | cut -d" " -f1
	)
}

pkgname() {
	echo "$c" | grep ^Package:|cut -d" " -f2-
}

deps() {
	echo "$c" | grep ^Depends:|| echo Depends:
}


cmd="$1" ; shift
ipk="$1" ; shift
c=$(control $ipk)

if [ "$cmd" = "control" ] ; then
	echo "$c"
elif [ "$cmd" = "fingerprint" ] ; then
	fingerprint $ipk
elif [ "$cmd" = "flist" ] ; then
	flist $ipk
elif [ "$cmd" = "name" ] ; then
	pkgname
elif [ "$cmd" = "deps" ] ; then
	printf "`pkgname`: "
	deps
else
	echo "unknown command [$cmd]."
	exit 1
fi

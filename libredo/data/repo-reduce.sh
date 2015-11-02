#!/bin/bash
#
# This script challenges packages provided on commandline
# against packages in a dir of candidates for matching
# fingerprints. Then it copies a reduced set of packages
# of those to a target directory. The aim of all this is
# to "deduplicate" packages that have been rebuilt without
# need.
#
# Dependency: ipkg-info.sh (expected in $PATH)
#
# Author: Tobias Hintze - Travelping GmbH
#

set -e

TMP=`mktemp -d`

# this script calls helper `ipkg-info.sh` which
# accepts the same $NO_CLEANUP. so we allow the
# deep and shallow NO_CLEANUP.
[ "$NO_CLEANUP" = deep ] && subcleanup=deep

function tmp_cleanup() {
    if [ -z "$NO_CLEANUP" ] ; then
        # just be paranoid:
        echo "$TMP" | grep -q "/tmp/tmp." && rm -rf "$TMP"
    else
        echo "preserved due to \$NO_CLEANUP: $TMP" 1>&2
    fi
}
trap tmp_cleanup EXIT

function usage() {
	cat << EOF

	$0 
		-o <TARGET_PACKAGE_DIR> 
		-r <CANDIDATES_DIR>
		\`pwd\`/*/*ipk

	Challenge all \`pwd\`/*/*ipk against packages in <CANDIDATES_DIR>
	for matching fingerprints. Then copy a (hopefully) reduced set
	of packages from \`pwd\`/*/*ipk to <TARGET_PACKAGE_DIR>.

EOF
}

# parse dash-options
while [ "${1#-}" != "$1" ]
do
	case "${1}" in
		-o)
			shift
			if [ -n "$1" ] ; then
				target_package_dir="$1"
				shift
			fi
			;;
		-r)
			shift
			if [ -n "$1" ] ; then
				repo="$1"
				shift
			fi
			;;
		*)
			usage
			exit 1
			;;
	esac
done


if [ -z "$repo" ] ; then
	echo "missing: repository with pre-existent packages (candidates)"
	usage
	exit 1
fi

if [ -z "$target_package_dir" ] ; then
	echo "missing: output directory for reduced upgrade increment"
	usage
	exit 1
fi

echo "repo: $repo" 1>&2

declare -i count=0

# loop through all input-packages
while [ -n "$1" ]
do
	ipk="$1" ; shift
	if [ "${ipk#/}" = "$ipk" ] # arguments must be absolute path
	then
		echo "all candidate-package arguments must be absolute paths"
		exit 1
	fi
	count=count+1
	echo "ipk: $ipk" 1>&2

	baseipk="${ipk}"
	baseipk="${baseipk##*/}" # basename
	baseipk="${baseipk%_*}" # cut off machine (core2-64 / vmware / all / ...)
	baseipk="${baseipk%-*}" # cut off build-id

	machine="${ipk}"
	machine="${machine##*_}" # cut off everything before machine
	machine="${machine%.*}" # drop .ipk suffix

	# calculate fingerprint for current package
	env NO_CLEANUP="$subcleanup" ipkg-info.sh fingerprint $ipk > $TMP/${count}-${baseipk}-new.fp

	# determine candidate (same package from last build)
	candidate=$( ls -1r $repo/$machine/${baseipk}*ipk | head -1 )
	[ -z "$candidate" ] && continue

	# calculate fingerprint for candidate package
	env NO_CLEANUP="$subcleanup" ipkg-info.sh fingerprint $candidate > $TMP/${count}-${baseipk}-candidate.fp

	fp_candidate=$(grep ^Package-Fingerprint: $TMP/${count}-${baseipk}-candidate.fp)
	fp_new=$(grep ^Package-Fingerprint: $TMP/${count}-${baseipk}-new.fp)

	if [ "${fp_candidate}" = "${fp_new}" ]
	then
		fullversion_candidate=$(grep ^Version: $TMP/${count}-${baseipk}-candidate.fp | cut -d" " -f2-)
		fullversion_new=$(grep ^Version: $TMP/${count}-${baseipk}-new.fp | cut -d" " -f2-)
		echo "${ipk##*/} matches ${candidate}"
		pkgname="${baseipk%_*}" # cut off machine
		pkgname="${pkgname%_*}" # cut off version
		echo "SKIP ${ipk} ${pkgname} $fullversion_new $fullversion_candidate" >> $TMP/manifest.txt
	else
		echo "TAKE ${ipk}" >> $TMP/manifest.txt
	fi
done

# create sed-filter for dependency modification for all SKIP-packages
# (SKIP packages are those we do not use from current build but use
#  a pre-existing package with same fingerprint)
grep ^SKIP $TMP/manifest.txt | while read action ipkg_fname pkg_name new_version replacement_version
do
	echo "/^Depend/s/\(^.* $pkg_name ([^ ]* \)$new_version)/\1$replacement_version)/" >> $TMP/deps-filter.sed
done

[ -n "$target_package_dir" ]

# now iterate over TAKE-packages, apply abovementioned sed-filter
# and write dependency-modified versions to results-dir ($target_package_dir)
(
cd $TMP
grep ^TAKE ./manifest.txt | while read action ipkg_fname
do
	rm -f ./control.tar.gz
	rm -rf ./control_untar
	ar oxf $ipkg_fname control.tar.gz
	mkdir ./control_untar
	tar xf control.tar.gz -C ./control_untar
	before=$(sha1sum ./control_untar/control)
	sed --in-place -f ./deps-filter.sed ./control_untar/control
	after=$(sha1sum ./control_untar/control)


	# determine double-base (basename and basename of dirname; includes machine)
	# assuming /foo/bar/spam.ipk for the comments
	ipkg_basename=${ipkg_fname##*/}                  # spam.ipk
	ipkg_dirname=${ipkg_fname%/*}                    # /foo/bar
	ipkg_dirbasename=${ipkg_dirname##*/}             # bar
	ipkg_basename=$ipkg_dirbasename/$ipkg_basename   # bar/spam.ipk

	mkdir -p $target_package_dir/$ipkg_dirbasename
	target_ipkg_fname="$target_package_dir/$ipkg_basename"
	cp -v $ipkg_fname $target_ipkg_fname
	if [ "$before" != "$after" ]  # check if control has been modified
	then
		echo "modified deps: $ipkg_fname"
		control_list=`tar ft control.tar.gz | grep -v '^./$'`
		rm -f ./control.tar.gz
		tar cf ./control.tar.gz -C ./control_untar $control_list
		ar Drf $target_ipkg_fname ./control.tar.gz
	else
		echo "unmodified: $ipkg_fname"
	fi
done
)

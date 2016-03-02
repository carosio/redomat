#!/usr/bin/python
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# (c) Travelping GmbH - "Tobias Hintze" <thintze+git@travelping.com>
#

import sys
import os
import getopt
from libredo import Redomat, Repotool
from libredo import Declaration

def usage():
    return """
redomat.py [OPTIONS] <redomat.xml> [<redomat2.xml> ...]

OPTIONS
    -h, --help
        print this help

    -c, --checkout
        standalone checkout mode

    -n, --dry-run
        do not build anything, just show what would be done

    -F, --skip-failure-commit
        do not commit a failed build stage

    -B, --new-build-id=BID
        set BID as build id (use with caution: id should be unique)

    -b, --match-build-id=BID
        use BID for matching/selecting images

    -U, --upgrade=IMGSPEC
        Use specified image IMGSPEC as base image for upgrade.
        repo:tag notation and image-id notation is accepted.
        On default, only build last stage. Use -e if required.

    -f, --foreign
        use stage images from other users

    -e, --entry=STAGE
        start building from STAGE

    -t, --target=STAGE
        build up to STAGE

    -l, --list=BID
        list all images that match a given BUILD-ID

    -L, --list-bids
        list all BUILD-IDs

"""

def main(argv):
    # evaluate passed flags
    try:
        opts, args = getopt.getopt(argv,"hcniFLl:e:t:b:B:U:",
                ["help", "checkout", "dry-run", "images", "skip-failure-commit",
                    "list=", "list-bids", "entry=", "target=", "match-build-id",
                    "new-build-id=", "upgrade="])
    except getopt.GetoptError, e:
        print(e)
        print(usage())
        sys.exit(1)

    declarations=args
    checkout_mode = False

    target_stage = None

    # spawn new redomat instance (docker client interface)
    redo = Redomat('unix://var/run/docker.sock')

    for opt, arg in opts:
        # print help when -h is passed
        if opt in ['-h', '--help']:
            print(usage())
            sys.exit(0)
        elif opt in ['-c', '--checkout']:
            checkout_mode = True
        elif opt in ['-F', '--skip-failure-commit']:
            redo.set_commitfailures(False)
        elif opt in ['-n', '--dry-run']:
            redo.set_dryrun(True)
        elif opt in ['-B', '--new-build-id']:
            redo.set_build_id(arg)
        elif opt in ['-b', '--match-build-id']:
            redo.set_match_build_id(arg)
        elif opt in ['-U', '--upgrade']:
            redo.set_upgrade_repo_tag(arg)
        elif opt in ['-f', '--foreign']:
            # this will allow redomat to select matching stage-images
            # from other users too
            redo.set_enable_foreign_images(True)
        elif opt in ['-e', '--entry']:
            print("starting at entry stage [%s]."%arg)
            redo.set_entry_stage(arg)
        elif opt in ['-t', '--target']:
            print("trying to reach target stage [%s]."%arg)
            target_stage = arg
        elif opt in ['-l', '--list']:
            # print all images that match a given build id
            redo.list_images(args)
            sys.exit(0)
        elif opt in ['-L', '--list-bids']:
            # print all build IDs
            redo.list_all_buildID()
            sys.exit(0)

    # parse declaration(s)
    decl = Declaration()
    for declaration in declarations:
        # check if the xml-file exists
        if not os.path.exists(declaration):
            raise Exception("declaration [%s] not found."%declaration)
            sys.exit(1)
        decl.parse(declaration)

    stages = decl.stages()

    # pass declaration to redomat
    redo.set_decl(decl)

    if checkout_mode:
        repotool = Repotool(decl, "standalone-%s"%os.getpid())
        for cmd in repotool.checkout_all("."):
            os.system(cmd)
        sys.exit(0)

    if not target_stage:
        target_stage = decl.guess_targetstage()
        if target_stage:
            print("determined target stage: %s"%target_stage)
        else:
            print("unable to guess a target stage. stage must be specified:")
            if len(decl.stages()) == 0:
                print("no stages known. did you specify a declaration file?")
            else:
                print(decl.stages())
            sys.exit(1)
    res = redo.build(target_stage)
    print "build completed (%s)."%{True:"successfully", False:"and failed"}[res]
    sys.exit(0)



if __name__ == "__main__":
    main(sys.argv[1:])

# vim:expandtab:ts=4

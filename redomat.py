#!/usr/bin/python
import docker
import sys
import os
import getopt
from libredo import Redomat, Repotool
from libredo import Declaration

def usage():
    return """
redomat <option> <redomat.xml>
    -h, --help
        print this help

    -c, --checkout
        standalone checkout

    -s, --stage=STAGE
        start building from STAGE

    -l, --list=BUILD ID
        list all images that match a given BUILD ID

    -L, --list-bids
        list all build IDs

"""

def main(argv):
    # evaluate passed flags
    try:
        opts, args = getopt.getopt(argv,"hcniLl:e:t:b:B:",
                ["help", "checkout", "dry-run", "images", "list=", "list-bids", "entry=", "target=", "match-build-id", "new-build-id="])
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
        elif opt in ['-n', '--dry-run']:
            redo.set_dryrun(True)
        elif opt in ['-B', '--new-build-id']:
            redo.set_build_id(arg)
        elif opt in ['-b', '--match-build-id']:
            redo.set_match_build_id(arg)
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
        repotool = Repotool(decl)
        for cmd in repotool.checkout_all("."):
            print cmd
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
    redo.build(target_stage)
    print "build completed."
    sys.exit(0)



if __name__ == "__main__":
    main(sys.argv[1:])

# vim:expandtab:ts=4

#!/usr/bin/python
import docker
import sys
import os
import getopt
from libredo import Redomat
from libredo.XML_creator import XML_creator
from libredo import Declaration

def usage():
    return """
redomat <option> <redomat.xml>
    -h, --help
        print this help

    -s, --stage=STAGE
        start building from STAGE

"""

def main(argv):
    # evaluate passed flags
    try:
        opts, args = getopt.getopt(argv,"hniLl:e:t:b:B:",
                ["help", "dry-run", "images", "list=", "list-all", "entry=", "target=", "match-build-id", "new-build-id="])
    except getopt.GetoptError, e:
        print(e)
        print(usage())
        sys.exit(1)

    declarations=args

    target_stage = None
    # spawn new redomat instance (docker client interface)
    redo = Redomat('unix://var/run/docker.sock')

    for opt, arg in opts:
        # print help when -h is passed
        if opt in ['-h', '--help']:
            print(usage())
            sys.exit(0)
        elif opt in ['-n', '--dry-run']:
            redo.set_dryrun(True)
        elif opt in ['-B', '--new-build-id']:
            redo.set_build_id(arg)
        elif opt in ['-b', '--match-build-id']:
            redo.set_match_build_id(arg)
        elif opt in ['-f', '--foreign']:
            # this will allow redomat to select matching stage-images
            # from other users too
            redo.allow_foreign_images(True)
        elif opt in ['-e', '--entry']:
            print("starting at entry stage [%s]."%arg)
            redo.set_entry_stage(arg)
        elif opt in ['-t', '--target']:
            print("trying to reach target stage [%s]."%arg)
            target_stage = arg
        elif opt in ['-l', '--list']:
            # print all images that match a given stage name
            for image in redo.find_images_by_stage(stage=arg):
                print(image['Repository'])
            sys.exit(0)
        elif opt in ['-L', '--list-all']:
            # print all images that (any stage)
            for image in redo.find_images():
                print(image['Repository'])
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
    redo.add(decl)

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


    # iterate over the list of stages and pass the relevant lines to the redomat
    for stage in stages:
        # print the good to knows
        print(stage)
        print("build this stage: " + str(stage['build']))
        redo.current_stage = stage['id']
        redo.prestage = stage['prestage']

        # create the bblayers.conf according to the layers specefied in the  redomat.xml
        XML_creator(declaration).create_bblayers(stage['id'] + "/bblayers.conf")
        XML_creator(declaration).create_local(stage['id'] + "/local.conf")

        # iterate over all the elements in the list dockerlines of the dictionary stage
        for line in stage['dockerlines']:
            # pass the line to the redomat data_parser if the stage is marked as to build
            if stage['build']:
                print(line)
                redo.data_parser(line)
            # if the stage is not marked as to build check if the line includes a FROM statement
            elif 'FROM' in line:
                # overwrite the current image variable to use a custom build id
                redo.current_image=build_id + "-" + stage['id']
                # tag the image with the custom build id so it can be used as a base for the new image
                redo.client.tag(image=redo.current_image, repository=redo.build_id + "-" + stage['id'])
        redo.laststage = redo.current_image
        print("laststage: " + redo.laststage)
        print("done building: " + stage['id'])

if __name__ == "__main__":
    main(sys.argv[1:])

# vim:expandtab:ts=4

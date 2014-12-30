#!/usr/bin/python
# function for parsing the data
import docker
import sys
import os
import getopt
import xml.etree.ElementTree as XML
from redomatfunctions import Redomat
from redomatfunctions import XML_creator
from redomatfunctions import XML_parser

def main(argv):
    #evaluate passed flags
    try:
        opts, args = getopt.getopt(argv,"hs:",["images"])
    except getopt.GetoptError:
        print("redomat <option> <redomat.xml>\n\t-h\t\tprint this help\n\t-s <STAGE>\tstart building from STAGE")
        sys.exit(1)

    start_point=None
    build=True
    dockerfiles=args

    for opt, arg in opts:
        #print help when -h is passed
        if opt == '-h':
            print("redomat <option> <redomat.xml>\n\t-h\t\tprint this help\n\t-s <STAGE> <BUILD_ID> <redomat.xml>\tstart building from STAGE")
            sys.exit()
        #use the -s flag to Start from a different stage
        elif opt == '-s':
            print("using -s")
            dockerfiles=args[1:]
            start_point=arg
            build_id=args[0]
            build=False
        #use the --images flag to print all images that have your username in the build id
        elif opt == '--images':
            for image in docker.Client(base_url='unix://var/run/docker.sock',version='0.6.0').images(name=str('*'+os.getenv('LOGNAME')+'*')):
                print(image['Repository'])
            sys.exit()

    for dockerfile in dockerfiles:
        #check if the xml-file exists
        if os.path.exists(dockerfile) is False:
            raise Exception("No Dockerfile found")
            sys.exit(1)

        #spawn new redomat instance and call it redo
        redo = Redomat(docker.Client(base_url='unix://var/run/docker.sock',version='0.6.0',timeout=2400))

        #parse the xml-file pased as a parameter and write the resolving list in the stages variable
        stages=XML_parser(dockerfile).parse(redo)
        #create a xml-file for the repo tool
        XML_creator(dockerfile).create_repoxml("init-repo/repo-" + dockerfile)

        #iterate over the list of stages and set the once that will be build to true
        for stage in stages:
            if stage['id'] == start_point:
                build = True
            if build==True:
                stage['build']=True

        #iterate over the list of stages and pass the relevant lines to the redomat
        for stage in stages:
            #print the good to knows
            print(stage['id'])
            print("build this stage: " + str(stage['build']))
            redo.current_stage = stage['id']
            redo.prestage = stage['prestage']

            #create the bblayers.conf according to the layers specefied in the  redomat.xml
            XML_creator(dockerfile).create_bblayers(stage['id'] + "/bblayers.conf")

            #iterate over all the elements in the list dockerlines of the dictionary stage
            for line in stage['dockerlines']:
                #pass the line to the redomat data_parser if the stage is marked as to build
                if stage['build']:
                    print(line)
                    redo.data_parser(line)
                #if the stage is not marked as to build check if the line includes a FROM statement
                elif 'FROM' in line:
                    #overwrite the current image variable to use a custom build id
                    redo.current_image=build_id + "-" + stage['id']
                    #tag the image with the custom build id so it can be used as a base for the new image
                    redo.client.tag(image=redo.current_image, repository=redo.build_id + "-" + stage['id'])
            redo.laststage = redo.current_image
            print("laststage: " + redo.laststage)
            print("done building: " + stage['id'])

if __name__ == "__main__":
    main(sys.argv[1:])

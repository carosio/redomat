import xml.etree.ElementTree as XML
import os

class XML_parser:
    def __init__(self):
        """
            parse the redo.xml
        """

        self.stagelist = []
        self.stagedict = {}

    def parse(self, xml_file):
        """
            function that converts the xml file to a list of commands for the redomat
        """
        # read the redomat.xml xml root
        manifest_root=XML.parse(xml_file).getroot()

        # parse the xml root to dictionary in the stages list by iterating over all build stages
        for buildstage in manifest_root.iter('buildstage'):
            # create template dictionary
            stage = {'id': buildstage.get('id'),
                'prestage' : '',
                'dockerlines' : []}

            # store in list and dict
            self.stagelist.append(stage['id'])
            self.stagedict[stage['id']] = stage

            # iterate over items in the build stages knot 
            for stage_command in buildstage.iter():
                # evaluate all different tags:
                # * prestage
                # * bitbake_target
                # * dockerline
                if stage_command.tag == 'prestage':
                    stage['prestage'] = stage_command.text.strip()

                # evaluate bitbake_target
                elif stage_command.tag == 'bitbake_target':
                    # add some needed lines before running the bitbake command
                    ## touch sanity-conf so bitbake will build as root 
                    stage['dockerlines'].append('RUN touch /REDO/build/conf/sanity.conf')
                    ## source oe-init-build-env to setup the environment for bitbake
                    stage['dockerlines'].append('RUN /bin/bash -c "source /REDO/source/poky/oe-init-build-env /REDO/build && bitbake')
                    ## check if the bitbake_target knot has a command specified
                    if stage_command.get('command'):
                        # add the command with the -c flag to the bitbake command
                        stage['dockerlines'].append(stage['dockerlines'].pop() + ' -c ' + stage_command.get('command'))
                    ## add the bitbake target and the closing apostrophe 
                    stage['dockerlines'].append(stage['dockerlines'].pop() + " " + stage_command.text + '"')

                # evaluate a dockerline by passing it 1:1
                elif stage_command.tag == 'dockerline':
                    stage['dockerlines'].append(stage_command.text)

    def stagelist(self):
        return self.stagelist

    def stage(self, stageid):
        return self.stagedict.get(stageid)

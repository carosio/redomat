import xml.etree.ElementTree as XML
import os

class XML_parser:
    def __init__(self, xml_file=None):
        """
            parse the redo.xml
        """
        # check if the parameters are passed correctly
        if xml_file is None:
            raise Exception("no xml file name given")

        # if the file dose not exist raise an exception
        if os.path.exists(xml_file) is False:
            raise Exception(xml_file + "no such file or directory")

        # read the redomat.xml xml root
        self.manifest_root=XML.parse(xml_file).getroot()
        self.stages = []

    def parse(self, redomat=None):
        """
            function that converts the xml file to a list of commands for the redomat
        """
        # check if the parameters are passed correctly
        if redomat is None:
            raise Exception("no redomat name given")

        # parse the xml root to dictionary in the stages list by iterating over all build stages
        for buildstage in self.manifest_root.iter('buildstage'):
            # create template dictionary
            stage = {'id': buildstage.get('id'),
                'build' : False,
                'prestage' : '',
                'dockerlines' : []}

            # append to stages list
            self.stages.append(stage)

            # iterate over items in the build stages knot 
            for stage_command in buildstage.iter():
                # evaluate all different tags:
                # * prestage
                # * bitbake_target
                # * dockerline
                if stage_command.tag == 'prestage':
                    # if prestage has not text build from laststage
                    if stage_command.text == None:
                        stage['dockerlines'].append("FROM laststage")
                    # if prestage has text in it set this stage as previous stage
                    else:
                        stage['prestage'] = stage_command.text
                        stage['dockerlines'].append("FROM prestage")

                # evaluate bitbake_target
                elif stage_command.tag == 'bitbake_target':
                    # add some needed lines before running the bitbake command
                    ## touch sanity-conf so bitbake will build as root 
                    stage['dockerlines'].append('RUN touch /TP/build/conf/sanity.conf')
                    ## source oe-init-build-env to setup the environment for bitbake
                    stage['dockerlines'].append('RUN /bin/bash -c "source /TP/source/poky/oe-init-build-env /TP/build && bitbake')
                    ## check if the bitbake_target knot has a command specified
                    if stage_command.get('command'):
                        # add the command with the -c flag to the bitbake command
                        stage['dockerlines'].append(stage['dockerlines'].pop() + ' -c ' + stage_command.get('command'))
                    ## add the bitbake target and the closing apostrophe 
                    stage['dockerlines'].append(stage['dockerlines'].pop() + " " + stage_command.text + '"')

                # evaluate a dockerline by passing it 1:1
                elif stage_command.tag == 'dockerline':
                    stage['dockerlines'].append(stage_command.text)

        # return the stages list
        return self.stages
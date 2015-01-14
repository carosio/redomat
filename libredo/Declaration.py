import xml.etree.ElementTree as XML
import os, uuid

class Declaration:
    def __init__(self):
        """
            parse the redo.xml
        """

        self.stagedict = {}

    def generate_stage_id(self):
        return "auto_stagename_%s"%uuid.uuid4()

    def parse(self, xml_file):
        """
            parse redomat declaration (xml) and add layers and stages to this instance

            returns the list of parsed stage ids
        """
        # read the redomat.xml xml root
        manifest_root=XML.parse(xml_file).getroot()
        stages = []

        # parse the xml root to dictionary in the stages list by iterating over all build stages
        for buildstage in manifest_root.iter('buildstage'):

            # create template dictionary
            stage = {}
            stage['actions'] = []
            stage['basepath'] = os.path.abspath(xml_file)

            if buildstage.get('id'):
                stage['id'] = buildstage.get('id')
            else:
                stage['id'] = self.generate_stage_id()

            # store in list and dict
            stages.append(stage['id'])
            self.stagedict[stage['id']] = stage

            # iterate over items in the build stages knot 
            for stage_command in buildstage.iter():
                # evaluate all different tags:
                # * prestage
                # * bitbake_target
                # * action (with @type being one of bitbake, command)
                if stage_command.tag == 'prestage':
                    stage['prestage'] = stage_command.text.strip()

                # evaluate bitbake_target
                elif stage_command.tag == 'bitbake_target':
                    # add some needed lines before running the bitbake command
                    ## touch sanity-conf so bitbake will build as root 
                    stage['actions'].append('RUN touch /REDO/build/conf/sanity.conf')
                    ## source oe-init-build-env to setup the environment for bitbake
                    stage['actions'].append('RUN /bin/bash -c "source /REDO/source/poky/oe-init-build-env /REDO/build && bitbake')
                    ## check if the bitbake_target knot has a command specified
                    if stage_command.get('command'):
                        # add the command with the -c flag to the bitbake command
                        stage['actions'].append(stage['actions'].pop() + ' -c ' + stage_command.get('command'))
                    ## add the bitbake target and the closing apostrophe 
                    stage['actions'].append(stage['actions'].pop() + " " + stage_command.text + '"')

                # evaluate a dockerline by passing it 1:1
                elif stage_command.tag == 'action':
                    stage['actions'].append(stage_command.text)
            return stages

    def stages(self):
        return self.stages

    def stage(self, stageid):
        return self.stagedict.get(stageid)

    def guess_startstage(self):
        # look for stages marked as startstage
        for stage in self.stages:
            if self.stagedict[stage].has_key("startstage"):
                return stage
        # fallback to any stage without a prestage
        for stage in self.stages:
            if not self.stagedict[stage].has_key("prestage"):
                return stage
        # no clue...
        return None

# vim:expandtab:ts=4

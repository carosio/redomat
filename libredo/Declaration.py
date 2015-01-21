import xml.etree.ElementTree as XML
import os, uuid

class DeclarationError(Exception):
    pass

class Declaration:
    def __init__(self):
        """
            parse the redo.xml
        """

        self.stagedict = {}
        self.layers = {}
        self.baselayer = None
        self.layer_remotes = {}

    def generate_stage_id(self):
        return "auto_stagename_%s"%uuid.uuid4()

    def log(self, severity, message):
        # FIXME use logging framework
        print message

    def parse(self, xml_file):
        """
            parse redomat declaration (xml) and add layers and stages to this instance

            returns the list of parsed stage ids
        """
        # read the redomat.xml xml root
        manifest_root=XML.parse(xml_file).getroot()

        # parse layer declaration
        new_layers = {}
        for layer_declaration in manifest_root.iter('layer_declaration'):
            # read all deceleration lines
            for repo_line in layer_declaration.iter():
                if repo_line.tag == 'layer_declaration': continue

                # if the tag reads layer
                if repo_line.tag == 'layer':
                    layer = {}
                    for attribute in ['name', 'remote', 'revision', 'repo']:
                        if not repo_line.attrib.has_key(attribute):
                            raise DeclarationError("attribute [%s] missing in layer declaration"%attribute)
                        layer[attribute] = repo_line.attrib[attribute]
                    new_layers[layer['name']] = layer
                    self.log(6, "added layer [%s]."%layer)

                elif repo_line.tag == 'baselayer':
                    self.baselayer = {}
                    for attribute in ['remote', 'revision', 'repo']:
                        if not repo_line.attrib.has_key(attribute):
                            raise DeclarationError("attribute [%s] missing in baselayer declaration"%attribute)
                        self.baselayer[attribute] = repo_line.attrib[attribute]
                    self.log(6, "baselayer: [%s]."%self.baselayer)

                # if the tag reads remote
                elif repo_line.tag == 'remote':
                    remote = {}
                    for attribute in ['name', 'baseurl']:
                        if not repo_line.attrib.has_key(attribute):
                            raise DeclarationError("attribute [%s] missing in remote declaration"%attribute)
                        remote[attribute] = repo_line.attrib[attribute]
                    self.layer_remotes[remote['name']] = remote
                    self.log(6, "added layer-remote [%s]."%remote['name'])
        self.layers.update(new_layers)

        new_stages = []
        # parse the xml root to dictionary in the stages list by iterating over all build stages
        for buildstage in manifest_root.iter('buildstage'):
            #{{{
            # create template dictionary
            stage = {}
            stage['actions'] = []
            stage['basepath'] = os.path.realpath(os.path.dirname(xml_file))

            if buildstage.get('id'):
                stage['id'] = buildstage.get('id')
            else:
                stage['id'] = self.generate_stage_id()

            # store in list and dict
            new_stages.append(stage['id'])
            self.stagedict[stage['id']] = stage
            self.log(6, "added stage [%s]."%stage['id'])

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
                    new_actions = []
                    # add some needed lines before running the bitbake command
                    ## touch sanity-conf so bitbake will build as root 
                    new_actions.append('RUN touch /REDO/build/conf/sanity.conf')
                    ## source oe-init-build-env to setup the environment for bitbake
                    new_actions.append('RUN /bin/bash -c "source /REDO/source/poky/oe-init-build-env /REDO/build && bitbake')
                    ## check if the bitbake_target knot has a command specified
                    if stage_command.get('command'):
                        # add the command with the -c flag to the bitbake command
                        new_actions.append(new_actions.pop() + ' -c ' + stage_command.get('command'))
                    ## add the bitbake target and the closing apostrophe 
                    new_actions.append(new_actions.pop() + " " + stage_command.text + '"')
                    stage['actions'].extend(new_actions)
                    self.log(6, "added bitbake actions: [%s]."%new_actions)

                # evaluate a dockerline by passing it 1:1
                elif stage_command.tag == 'action':
                    stage['actions'].append(stage_command.text)
                    self.log(6, "added action: [%s]."%stage_command.text)
            #}}}
        return new_layers, new_stages



    def stages(self):
        return self.stagedict.keys()

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

    def guess_targetstage(self):
        stages = set(self.stagedict)
        for stage in self.stagedict.keys():
            if self.stagedict[stage].has_key("prestage"):
                stages.remove(self.stagedict[stage]["prestage"])
        if len(stages) == 1:
            return stages.pop()
        return None

    def __str__(self):
        s = []
        s.append("stages:")
        s.append(self.stagedict.__str__())
        s.append("layer remotes:")
        s.append(self.layer_remotes.__str__())
        s.append("layers:")
        s.append(self.layers.__str__())
        return "\n".join(s)

# vim:expandtab:ts=4

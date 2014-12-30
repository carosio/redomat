from docker import Client
import sys, time, os
import xml.etree.ElementTree as XML

class Redomat:

    def __init__(self,client=None):
        """
            a builder for yocto using docker to support builds on top of other builds
        """
        #check if client is passed
        if client is None:
            raise Exception("client is not set")

        #set some default values
        #set the client
        self.client = client
        #stage that is build
        self.current_stage = "undefined"
        #current image name that is processed
        self.current_image = "undefined"
        #last stage that was build
        self.laststage = "undefined"
        #prestage specified in the redomat.xml
        self.prestage = "undefined"
        #unique build id
        self.build_id = "%s-%s"%(time.strftime("%F-%H%M%S"), os.getenv('LOGNAME'))
        #counter for container so the id's don't collide
        self.run_sequence = 0

    def data_parser(self, docker_line):
        """
            map redomat lines to the functions of the redomat
        """
        #split the callback function from the parameters
        docker_command = docker_line.split(" ")

        #raise exception if there is no function in the redomat with that name
        if not hasattr(self, docker_command[0]):
            raise Exception("unknown command <%s>"%docker_command[0])
        callback = getattr(self, docker_command[0])

        #pass the commands to the redomat
        callback(" ".join(docker_command[1:]).strip())

    def _nextseq(self):
        """
            counter for RUN command
        """
        self.run_sequence = self.run_sequence + 1
        return "%03i"%self.run_sequence

    def FROM(self, image=None):
        """
            tag an image to begin from
        """
        #check if all the parameters are passed
        if image is None:
            raise Exception("no image given to work with")
        #check if the image contains laststage
        elif 'laststage' in image:
            #pick up from the previous stage
            print("picking up build from lasstage: " + self.laststage)
            image = self.laststage
        #check if the image contains prestage
        elif 'prestage' in image:
            #pickup build from a prestage set in the default xml
            print('picking up build from ' + self.prestage)
            #check if prestage is set correctly
            if self.prestage is 'undefined':
                raise Exception("no prestage set")
            image = self.build_id + "-" + self.prestage


        #set the current image vatiable
        self.current_image="%s-%s"%(self.build_id, self.current_stage)

        try:
            #tag the current image
            self.client.tag(image,self.current_image)
        except:
            try:
                #if the tag cannot be created try to pull the image
                print("pulling: " + image + ":" + image_tag)
                image, image_tag = image.split(":")
                self.client.pull(repository=image,tag=image_tag)
                self.client.tag(image + ":" + image_tag,self.current_image)
            except:
                raise Exception("The base image could not be found local or remote")

    def RUN(self, cmd=None):
        """
            RUN command within a docker container
        """
        #check if parameters are passed correctly
        if self.client is None:
            raise Exception("No client given to work with")
        if cmd is None:
            raise Exception("RUN needs atleast one comman")

        #set the name of the container being processed
        name = "%s-%s-%s"%(self.build_id, self.current_stage, self._nextseq())
        #create a container withe the command that should be executed
        self.client.create_container(image=self.current_image, name=name, command=cmd)
        #start the crated container
        self.client.start(container=name, privileged=True)

        #wait till the command is executed
        if self.client.wait(container=name) is not 0:
            #raise Exception if the command exited with a non zero code
            raise Exception("Container " + name + " exited with a non zero exit status")
        #commit the currently processed container
        self.client.commit(container=name, repository=self.current_image)

    def ADD(self, parameter=None):
        """
            ADD a file to an image
        """
        #check if parameters are passed correctly
        if parameter is None:
            raise Exception("No parameter given")
        if file_name is None:
            raise Exception("No filename given")
        if target is None:
            raise Exception("No target directory given")

        #split filename and target
        file_name, target =parameter.split()
        #add the directory of the current stage to the filename
        file_name=self.current_stage + "/" + file_name

        #check if the file exists
        if os.path.exists(file_name) is False:
            raise Exception("No such file: " + file_name)

        #split of the name of the file
        file_name=os.path.basename(file_name)
        #read the absolute path of the file dir of the stage
        volume_path=os.path.abspath(self.current_stage)
        #set the name of the container being processed
        name = "%s-%s-%s-%s"%(self.build_id, self.current_stage, self._nextseq(), "create-target_dir")

        #create a container to create the target dir
        self.client.create_container(image=self.current_image, name=name, command="/bin/mkdir -pv " + os.path.dirname(target))
        #run the container
        self.client.start(container=name)

        #commit when the container exited with a non zero exit code
        if self.client.wait(container=name) is not 0:
                         raise Exception("Container " + name + " could not create a dir to use for th ADD command")
        self.client.commit(container=name, repository=self.current_image)

        #set the name of the container being processed
        name = "%s-%s-%s-%s"%(self.build_id, self.current_stage, self._nextseq(), "copy-data")

        #create a container to copy the file to the target image
        self.client.create_container(image=self.current_image, name=name, volumes=volume_path, command="cp -rv /files/" + file_name + " " + target)
        #start the container with the files dir of the stage connected as a volume
        self.client.start(container=name, binds={
                volume_path:
                    {
                        'bind': '/files/',
                        'ro': True
                    }})

        #commit when the container exited with a non zero exit code
        if self.client.wait(container=name) is not 0:
            raise Exception("Container " + name + " exited with a non zero exit status")
        self.client.commit(container=name, repository=self.current_image)

    def WORKDIR(self, directory=None):
        """
            set a WORKDIR for an image
        """
        #check if parameters are passed correctly
        if directory is None:
            raise Exception("No directory given")

        #set name for the current container being processed
        name = "%s-%s-%s"%(self.build_id, self.current_stage, self._nextseq())

        #create the container and set a working dir
        self.client.create_container(image=self.current_image, name=name, working_dir=directory)

        #commit the container
        self.client.commit(container=name, repository=self.current_image)

    def ENTRYPOINT(self, cmd=None):
        """
            set entry point of image
        """
        #check if parameters are passed correctly
        if self.client is None:
            raise Exception("No client given to work with")
        if cmd is None:
            raise Exception("RUN needs atleast one comman")

        #set the name of the container being processed
        name = "%s-%s-%s"%(self.build_id, self.current_stage, self._nextseq())

        #create a container with a different entry point set
        self.client.create_container(image=self.current_image, name=name, command=cmd)
        #commit the container with the new entry point set
        self.client.commit(container=name, repository=self.current_image)

class XML_creator:
    def __init__(self, xml_file=None):
        """
            create xml files that can be used by a variety of tools needed for the redomat
            * repo tool
            * bitbakes bblayer.conf
            * bitbakes local.conf
        """
        if xml_file is None:
            raise Exception("no xml file name given")

        if os.path.exists(xml_file) is False:
            raise Exception(xml_file + "no such file or directory")

        self.manifest_root=XML.parse(xml_file).getroot()

    def create_repoxml(self,out_name=None):
        """
            function used to crate a xml file used by the repo tool
            the out put file name must be passed
        """
        if out_name is None:
            raise Exception("no output file name given")

#       if os.path.exists(out_name):
#           raise Exception(out_name + "file already exists")

        repo_xml_root = XML.Element("manifest")

        for layer_declaration in self.manifest_root.iter('layer_declaration'):
            for repo_line in layer_declaration.iter().next():
                if repo_line.tag == 'layer':
                    repo_xml = XML.SubElement(repo_xml_root, 'project')
                    for attribute, value in repo_line.attrib.iteritems():
                        if 'path' in attribute:
                            repo_xml.set('path', value)
                        if 'reponame' in attribute:
                            repo_xml.set('name', value)
                        else:
                            repo_xml.set(attribute, value)

                else:
                    repo_xml = XML.SubElement(repo_xml_root, repo_line.tag)
                    for attribute, value in repo_line.attrib.iteritems():
                        repo_xml.set(attribute, value)

        tree = XML.ElementTree(repo_xml_root)
        tree.write(out_name, xml_declaration=True)

    def create_bblayers(self, out_name=None):
        """
            function used to crate the bblayers.conf for bitbake
            the out put file name must be passed
        """
        if out_name is None:
            raise Exception("no output file name given")

        if os.path.exists(out_name):
            os.remove(out_name)

        bblayers = open(out_name, 'a')
        bb_tamplate = open('default_bblayers', 'r')

        for line in bb_tamplate:
            bblayers.write(line)
        bb_tamplate.close()

        for layer_declaration in self.manifest_root.iter('layer_declaration'):
            for repo_line in layer_declaration.iter().next():
                if repo_line.tag == 'layer':
                    for attribute, value in repo_line.attrib.iteritems():
                        if 'path' in attribute:
                            if value!='poky':
                                bblayers.write("/TP/source/" + value + ' \ \n')

        bblayers.write('"')
        bblayers.close()
        if bblayers.closed is False:
            raise Exception("Something went wrong while closing the bblayers file")

    def create_local(self, out_name=None):
        """
            function used to crate the bblayers.conf for bitbake
            the out put file name must be passed
        """
        if out_name is None:
            raise Exception("no output file name given")

        if os.path.exists(out_name):
            os.remove(out_name)

        local_conf = open(out_name, 'a')
        local_tamplate = open('default_local', 'r')

        for line in local_tamplate:
            local_conf.write(line)
        local_tamplate.close()

        for local_declaration in self.manifest_root.iter('local_conf'):
            for local_line in local_declaration.iter().next():
                local_conf.write(local_line.tag + '"' + local_line.value + '"\n')

        local_conf.close()
        if local_conf.closed is False:
            raise Exception("Something went wrong while closing the local.conf")

class XML_parser:
    def __init__(self, xml_file=None):
        """
            parse the redo.xml
        """
        if xml_file is None:
            raise Exception("no xml file name given")

        if os.path.exists(xml_file) is False:
            raise Exception(xml_file + "no such file or directory")

        self.manifest_root=XML.parse(xml_file).getroot()
        self.stages = []

    def parse(self, redomat=None):
        """
            function that converts the xml file to a list of commands for the redomat
        """
        if redomat is None:
            raise Exception("no redomat name given")

        for buildstage in self.manifest_root.iter('buildstage'):
            stage = {'id': buildstage.get('id'),
                'build' : False,
                'prestage' : '',
                'dockerlines' : []}
            self.stages.append(stage)

            for stage_command in buildstage.iter():
                if stage_command.tag == 'prestage':
                    if stage_command.text == None:
                        stage['dockerlines'].append("FROM laststage")
                    else:
                        stage['prestage'] = stage_command.text
                        stage['dockerlines'].append("FROM prestage")

                elif stage_command.tag == 'bitbake_target':
                    stage['dockerlines'].append('RUN touch /TP/build/conf/sanity.conf')
                    stage['dockerlines'].append('RUN /bin/bash -c "source /TP/source/poky/oe-init-build-env /TP/build')
                    stage['dockerlines'].append(stage['dockerlines'].pop() + ' && bitbake ')
                    if stage_command.get('command'):
                        stage['dockerlines'].append(stage['dockerlines'].pop() + '-c ' + stage_command.get('command'))
                        stage['dockerlines'].append(stage['dockerlines'].pop() + " " + stage_command.text + '"')
                    else:
                        stage['dockerlines'].append(stage['dockerlines'].pop() + stage_command.text + '"')

                elif stage_command.tag == 'dockerline':
                    stage['dockerlines'].append(stage_command.text)

        return self.stages

import docker
import getpass
import time, os
import xml.etree.ElementTree as XML

class BuildException(Exception):
    pass

class Redomat:

    def __init__(self,service_url):
        """
            a builder for yocto using docker to support builds on top of other builds
        """
        self.service_url = service_url
        self.service_version = "0.6.0"
        self.dclient = docker.Client(base_url=self.service_url,version=self.service_version,timeout=2400)

        # stage that is build
        self.current_stage = None
        # current image name that is processed
        self.current_image = "undefined"

        # last stage that was build
        self.laststage = "undefined"
        # prestage specified in the redomat.xml
        self.prestage = "undefined"


        # counter for container so the id's don't collide
        self.run_sequence = 0

        # flag for image search-operation and selection
        # (allow other user's images as candidates)
        self.include_foreigns = False

        # some options, see accessor function for details
        self.build_id = None
        self.match_build_id = None
        self.dry_run = False

        self.username = getpass.getuser()

        self.exposed_docker_commands = set(['FROM', 'RUN', 'ADD', 'WORKDIR', 'ENTRYPOINT'])

    def log(self, severity, message):
        # FIXME use logging framework
        print message

    def add(self, _decl):
        """
            set the build declaration to be used for the next build
        """
        self.decl = _decl

    def set_dryrun(self, dry):
        """
            set_dryrun(True) - do not actually build anything, but output what would be done
            set_dryrun(False) - well... do it.
        """
        self.dry_run = dry

    def setuser(self, _user):
        """
            set specific username.
            the username is one component of the name of containers,
            images and tags. the default is to use the user name of
            the detected system username.
        """
        self.username = _user

    def set_match_build_id(self, _buildid):
        """
            set the build-id used for matching/selecting images
            as prestages for builds
        """
        self.match_build_id = _buildid

    def set_build_id(self, _buildid):
        """
            set the actual build-id of the new build.
            use of this is discouraged. build-ids should
            be unique. Redomat will generate a suitable build-id
            if this function is not used.
        """
        self.build_id = _buildid

    def resolve_stage_to_image(self, stage):
        """
            this function takes a stage-id from the stage-declaration
            as input and tries to find a matching image.
            the matching strategy depends on match_build_id, the username
            and the include_foreigns option.

            if no image is found None is returned. this usually means
            that a rebuild of the stage is necessary.
        """
       
        if self.match_build_id:
            expectation = "%s-%s"%(self.match_build_id, stage)
            if expectation in self.find_images_by_stage(stage=stage):
                return expectation
        else:
            # TODO implement some heuristic to pick any matching stage
            pass
        return None

    def generate_build_chain(self, target):
        """
            generate a list (in reverse build order) of
            (stage_id, stage_image) tuples where stage_image
            specifies the prestage-image to be used for building
            stage_id.
            stage_id of the first tuple is always the target argument
        """
        chain = []
        sid = target

        while True:
            stage = self.decl.stage(sid)
            assert(type(stage) == dict)

            prestage = stage.get("prestage")
            if prestage:
                chain.append((sid, self.resolve_stage_to_image(prestage)))
                if chain[-1][1]:
                    # prestage could be resolved to existing image
                    # the chain ends here. this is the starting point
                    break
                sid = prestage
            else:
                # without a prestage there must be a FROM,
                # which specifies the verbatim starting point
                # from a docker registry/hub.
                fromline = stage['actions'][0]
                chain.append((sid, fromline.split(" ")[1].strip()))
                break
        return chain

    def build(self, stage):
        """
            build the given stage.
            depending on how the stage-dependency-resolution-policy is set,
            dependent stages are either resolved or build.
        """

        if not self.build_id:
            # generate a buildid if non was provided
            self.build_id = "%s-%s"%(time.strftime("%F-%H%M%S"), self.username)
            self.log(6, "build-id generated: [%s]"%self.build_id)

        build_chain = self.generate_build_chain(stage)

        while True:
            stage, pre_image = build_chain.pop()

            stage_decl = self.decl.stage(stage)
            if not stage_decl:
                self.log(3, "unable to access declaration for stage [%s]"%stage)
                raise BuildException("cannot build. stage [%s]. stage undeclared."%stage)

            self.current_stage = stage

            self.log(5, "starting build of stage [%s] with build-id [%s]"%(self.current_stage, self.build_id))

            # set the current image vatiable
            self.current_image = "%s-%s"%(self.build_id, self.current_stage)

            # check pre-image
            try:
                pre_image_details = dclient.inspect_image(pre_image)
            except: # FIXME catch more precisely
                # image not found
                raise BuildException("cannot build. pre_image [%s] not accesible."%pre_image)

            # tag the current image
            self.dclient.tag(pre_image,self.build_id)
            self.log(5, "successfully tagged [%s@%s]"%(pre_image, self.current_image))
            except:
                try:
                    # if the tag cannot be created try to pull the image
                    print("pulling: " + image + ":" + image_tag)
                    image, image_tag = image.split(":")
                    self.dclient.pull(repository=image,tag=image_tag)
                    self.dclient.tag(image + ":" + image_tag,self.current_image)
                except:
                    raise Exception("The base image could not be found local or remote")

            for action in stage_decl['actions']:
                self.log(7, "executing action [%s]"%action)


    def allow_foreign_images(self, flag):
        """
            set flag to True/False to enable/disable images
            from other users as candidates for prestages
        """
        self.include_foreigns = True

    def find_images(self):
        if self.include_foreigns:
            pattern = "*-*-*"
        else:
            pattern = "*-%s-*"%self.username
        return self.find_images_by_pattern(pattern)

    def find_images_by_stage(self, stage):
        if self.include_foreigns:
            pattern = "*-*-%s"%stage
        else:
            pattern = "*-%s-%s"%(self.username, stage)
        return self.find_images_by_pattern(pattern)

    def find_images_by_pattern(self, pattern):
        for image in self.dclient.images(name=pattern):
            yield image

    def data_parser(self, docker_line):
        # FIXME: bad wording: a parser should not execute
        """
            map redomat lines to the functions of the redomat
            (and also execute them)
        """
        # split the callback function from the parameters
        docker_command = docker_line.split(" ")

        # better check if the command is part of what we want to expose
        if not docker_command[0] in self.exposed_docker_commands:
            raise Exception("unsupported command <%s>"%docker_command[0])

        # raise exception if there is no matching function
        if not hasattr(self, docker_command[0]):
            raise Exception("unknown command <%s>"%docker_command[0])
        callback = getattr(self, docker_command[0])

        # pass the commands to the redomat
        callback(" ".join(docker_command[1:]).strip())

    def _nextseq(self):
        """
            counter for RUN command
        """
        self.run_sequence = self.run_sequence + 1
        return "%03i"%self.run_sequence

    def FROM(self, image):
        """
            The FROM line has to be present in entry-stages
            without prestages. This is the verbatim image specifier
            used by docker to start the first stage.
            Unlike all other actions this line is not parsed here
            but during build-chain generation, hence it is a mistake
            if this code is reached.
        """
        assert(False)


    def RUN(self, cmd):
        """
            RUN command within a docker container
        """
        # check if parameters are passed correctly
        assert(self.dclient)

        # set the name of the container being processed
        name = "%s-%s-%s"%(self.build_id, self.current_stage, self._nextseq())
        # create a container withe the command that should be executed
        self.dclient.create_container(image=self.current_image, name=name, command=cmd)
        # start the crated container
        self.dclient.start(container=name, privileged=True)

        # wait till the command is executed
        if self.dclient.wait(container=name) is not 0:
            # raise Exception if the command exited with a non zero code
            raise Exception("Container " + name + " exited with a non zero exit status")
        # commit the currently processed container
        self.dclient.commit(container=name, repository=self.current_image)

    def ADD(self, parameter):
        """
            ADD a file to an image
        """

        # split filename and target
        file_name, target =parameter.split()
        # add the directory of the current stage to the filename
        file_name=self.current_stage + "/" + file_name

        # check if the file exists
        if target is None:
            raise Exception("No target directory given")
        if file_name is None:
            raise Exception("No filename given")
        if os.path.exists(file_name) is False:
            raise Exception("No such file: " + file_name)

        # split of the name of the file
        file_name=os.path.basename(file_name)
        # read the absolute path of the file dir of the stage
        volume_path=os.path.abspath(self.current_stage)
        # set the name of the container being processed
        name = "%s-%s-%s-%s"%(self.build_id, self.current_stage, self._nextseq(), "create-target_dir")

        # create a container to create the target dir
        self.dclient.create_container(image=self.current_image, name=name, command="/bin/mkdir -pv " + os.path.dirname(target))
        # run the container
        self.dclient.start(container=name)

        # commit when the container exited with a non zero exit code
        if self.dclient.wait(container=name) is not 0:
                         raise Exception("Container " + name + " could not create a dir to use for th ADD command")
        self.dclient.commit(container=name, repository=self.current_image)

        # set the name of the container being processed
        name = "%s-%s-%s-%s"%(self.build_id, self.current_stage, self._nextseq(), "copy-data")

        # create a container to copy the file to the target image
        self.dclient.create_container(image=self.current_image, name=name, volumes=volume_path, command="cp -rv /files/" + file_name + " " + target)
        # start the container with the files dir of the stage connected as a volume
        self.dclient.start(container=name, binds={
                volume_path:
                    {
                        'bind': '/files/',
                        'ro': True
                    }})

        # commit when the container exited with a non zero exit code
        if self.dclient.wait(container=name) is not 0:
            raise Exception("Container " + name + " exited with a non zero exit status")
        self.dclient.commit(container=name, repository=self.current_image)

    def WORKDIR(self, directory):
        """
            set a WORKDIR for an image
        """
        # set name for the current container being processed
        name = "%s-%s-%s"%(self.build_id, self.current_stage, self._nextseq())

        # create the container and set a working dir
        self.dclient.create_container(image=self.current_image, name=name, working_dir=directory)

        # commit the container
        self.dclient.commit(container=name, repository=self.current_image)

    def ENTRYPOINT(self, cmd):
        """
            set entry point of image
        """
        # check if parameters are passed correctly
        if self.dclient is None:
            raise Exception("No client given to work with")

        # set the name of the container being processed
        name = "%s-%s-%s"%(self.build_id, self.current_stage, self._nextseq())

        # create a container with a different entry point set
        self.client.create_container(image=self.current_image, name=name, command=cmd)
        # commit the container with the new entry point set
        self.client.commit(container=name, repository=self.current_image)

# vim:expandtab:ts=4

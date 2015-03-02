import getpass, time, os, logging, socket, sys
from libredo import Repotool
from libredo.ConfCreator import ConfCreator
import xml.etree.ElementTree as XML

class BuildException(Exception):
    pass

class Redomat:

    def __init__(self,service_url):
        """
            a builder for yocto using docker to support builds on top of other builds
        """
        self.decl = None
        self._dclient = None
        self.service_url = service_url
        self.service_version = "0.6.0"
        self.repotool = Repotool.Repotool(self.decl)
        self.conf_creator = ConfCreator(self.decl)
        # stage that is build
        self.current_stage = None
        # current image name that is processed

        # counter for container so the IDs don't collide
        self.run_sequence = 0

        # flag for image search-operation and selection
        # (allow other user's images as candidates)
        self.include_foreigns = False

        # some options, see accessor function for details
        self.build_id = None
        self.match_build_id = None
        self.dry_run = False
        self._entry_stage = None
        self.loglevel = logging.INFO
        self.logformat = '%(asctime)s %(levelname)s: %(message)s'
        logging.basicConfig(format=self.logformat, level=self.loglevel)

        self.username = getpass.getuser()

        self.exposed_docker_commands = set(['CREATE_BBLAYERS','CREATE_LOCAL_CONF','REPOSYNC', 'FROM', 'RUN', 'ADD', 'WORKDIR', 'ENTRYPOINT'])

    def dc(self):
        "return docker client instance (imports docker module)"
        if None == self._dclient:
            if 'docker' not in dir():
                import docker
            self._dclient = docker.Client(base_url=self.service_url,version=self.service_version,timeout=2400)
        return self._dclient

    def set_entry_stage(self, s):
        self._entry_stage = s

    def log(self, severity, message):
        m = []
        if self.build_id:
            m.append("[%s]"%self.build_id)
        if self.current_stage:
            m.append("(%s)"%self.current_stage)
        m.append(message)

        if severity <= 2:
            logging.critical(" ".join(m))
        elif severity == 3:
            logging.error(" ".join(m))
        elif severity == 4:
            logging.warning(" ".join(m))
        elif ( 4 < severity <= 6):
            logging.info(" ".join(m))
        elif severity >= 7:
            logging.debug(" ".join(m))

    def set_decl(self, _decl):
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
            expectation = "%s:%s"%(self.match_build_id, stage)
            if expectation in self.find_images_by_stage(stage=stage):
                self.log(6, "matched [%s]"%expectation)
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

        self.log(7, "generating build-chain")
        while True:
            stage = self.decl.stage(sid)
            assert(type(stage) == dict)

            prestage = stage.get("prestage")
            if prestage:
                prestage_image = self.resolve_stage_to_image(prestage)
                if prestage_image:
                    # prestage could be resolved to existing image
                    # the chain ends here. this is the starting point
                    chain.append((sid, prestage_image))
                    break
                else:
                    # this image has to be built:
                    chain.append((sid, "%s:%s"%(self.build_id, prestage)))
                sid = prestage
            else:
                # without a prestage there must be a FROM,
                # which specifies the verbatim starting point
                # from a docker registry/hub.
                fromline = stage['actions'].pop(0).strip()
                if not fromline.startswith("FROM "):
                    raise BuildException("a stage without pre-stage lacks FROM")
                tags = []
                for x in self.dc().images(name=fromline.split(" ")[1].split(":")[0]):
                    tags.append(x["Tag"])
                image = fromline.split(" ")[1].split(":")[0]
                tag = fromline.split(" ")[1].split(":")[1]
                if tag not in tags:
                    self.log(7, "could not find %s in local registry trying to locate it on dockerhub"%image)
                    if [] != self.dc().search(image):
                        self.log(7, "%s found on dockerhub"%image)
                        self.log(7, "trying to pull %s:%s"%(image, tag))
                        self.dc().pull(repository=image, tag=tag)
                        tags = []
                        for x in self.dc().images(name=fromline.split(" ")[1].split(":")[0]):
                            tags.append(x["Tag"])
                        if tag not in tags:
                            raise Exception("%s:%s could not be obtained no such tag"%(image, tag))
                        self.log(7, "successfully pulled %s:%s"%(image, tag))
                chain.append((sid, fromline.split(" ")[1].strip()))
                break
            if stage == self._entry_stage:
                self.log(7, "entry stage matched")
                break
        self.log(6, "build-chain: %s"%chain)
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

        self.repotool.set_syncid(self.build_id)
        build_chain = self.generate_build_chain(stage)

        while build_chain:
            stage, pre_image = build_chain.pop()

            stage_decl = self.decl.stage(stage)
            if not stage_decl:
                self.log(3, "unable to access declaration for stage [%s]"%stage)
                raise BuildException("cannot build. stage [%s]. stage undeclared."%stage)

            self.current_stage = stage

            self.log(5, "starting build.")

            # set the current image vatiable
            self._resetseq()

            # check pre-image
            try:
                pre_image_details = self.dc().inspect_image(pre_image)
                # key changed from id to Id between 0.6.0 and following 
                # docker client versions. we try to be compatible
                image_id =  pre_image_details.get('Id') or  pre_image_details.get('id')
                self.log(6, "pre-image [%s] resolved to: %s"%(pre_image, image_id))
            except Exception, e: # FIXME catch more precisely
                # image not found try to pull the image
                self.log(3, e.__str__())
                raise BuildException("cannot build. pre_image [%s] not accesible."%pre_image)

            # tag the current image
            tag = "%s-%s"%(self.current_stage, self._seq())
            if not self.dry_run:
                self.dc().tag(pre_image, self.build_id, tag=tag)
                self.log(5, "successfully tagged %s as [%s@%s]"%(pre_image, self.build_id, tag))
            else:
                self.log(5, "successfully (not) tagged %s as [%s@%s]"%(pre_image, self.build_id, tag))

            if False:
                # just keeping some code which was never called
                # (image_tag is used too early, this would throw)
                try:
                    # if the tag cannot be created try to pull the image
                    print("pulling: " + image + ":" + image_tag)
                    image, image_tag = image.split(":")
                    self.dc().pull(repository=image,tag=image_tag)
                    self.dc().tag(image + ":" + image_tag,self._current_image())
                except:
                    raise BuildException("The base image could not be found local or remote")

            for action in stage_decl['actions']:
                if not self.dry_run:
                    self.log(7, "executing action [%s]"%action)
                    self.handle_action(action)
                else:
                    self.log(5, "(not) executing action [%s]"%action)
            self.log(5, "stage actions completed. tagging: %s:%s"%(self.build_id, self.current_stage))
            if not self.dry_run:
                self.dc().tag(self._current_image(), self.build_id, self.current_stage)

    def _current_image(self):
        return "%s:%s-%s"%(self.build_id, self.current_stage, self._seq())

    def _current_container(self):
        return "%s-%s-%s"%(self.build_id, self.current_stage, self._seq())

    def set_enable_foreign_images(self, flag):
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
            pattern = "*-*"
        else:
            pattern = "*-%s"%self.username
        # filter for requested stage
        for image in self.find_images_by_pattern(pattern):
            if image.get('Tag') == stage:
                yield "%s:%s"%(image.get('Repository'),image.get('Tag'))

    def find_images_by_pattern(self, pattern):
        for image in self.dc().images(name=pattern):
            yield image

    def list_all_buildID(self):
        build_ids = []
        for image in self.dc().images(all=True):
            build_ids.append(image['Repository'])
        build_ids=list(set(build_ids))
        for ID in build_ids:
            if '<none>' != ID:
                print(ID)

    def list_images(self, args):
        for buildID in self.dc().images(name=args):
            print(buildID['Id'])

    def handle_action(self, action):
        """
            execute "action"
        """
        # split the callback function from the parameters
        docker_command = action.split(" ")

        # better check if the command is part of what we want to expose
        if not docker_command[0] in self.exposed_docker_commands:
            raise Exception("unsupported command <%s>"%docker_command[0])

        # raise exception if there is no matching function
        if not hasattr(self, docker_command[0]):
            raise Exception("unknown command <%s>"%docker_command[0])
        callback = getattr(self, docker_command[0])

        # pass the commands to the redomat
        callback(" ".join(docker_command[1:]).strip())

    def _resetseq(self):
        self.run_sequence = 0

    def _seq(self):
        """
            return current seq without incrementing
        """
        return "%03i"%self.run_sequence

    def _nextseq(self):
        """
            counter for RUN command
        """
        self.run_sequence = self.run_sequence + 1
        return "%03i"%self.run_sequence

    def file_socket_send(self, message, filename):
        """
            create a container listening on a tcpsocket
        """

        name = self._current_container()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = 8888

        # create the container
        container = self.dc().create_container(image=self._current_image(), name=name, command="/bin/bash -c \"socat -u tcp4-listen:{port} create:{name}\"".format(port=port, name=filename))
        container_id = container.get('Id') or container.get('id')
        self.log(4, "new container started [%s] from [%s]"%(container_id, self._current_image()))

        # start the container
        self.dc().start(container=name)

        # getting the ip of the container
        IP = self.dc().inspect_container(container=name)['NetworkSettings']['IPAddress']
        server_address = (IP, port)

        print >>sys.stderr, 'connecting to {IP} port {port}'.format(IP=IP,port=port)
        # connecting to socket
        for i in range(0, 9):
            try:
                sock.connect(server_address)
            except socket.error as e:
                self.log(5, "Could not connect to container {container}:".format(container=name))
                self.log(5, "Reconnecting")
                if e.errno == socket.errno.ECONNREFUSED:
                    time.sleep(3)

        # sending file
        try:
            print >>sys.stderr, 'sending"%s"'%message
            sock.sendall(message)
        except socket.error as e:
            raise e
            raise Exception("Error while sending configuration file: {name}".format(name=filename))
        finally:
            print >>sys.stderr, 'closing socket'
            sock.close()

        # stop the container after the file is send
        if self.dc().wait(container=name) is not 0:
            tag = "%s-%s-fail"%(self.current_stage, self._nextseq())
            self.dc().commit(container=name, repository=self.build_id, tag=tag)
            # raise Exception if the command exited with a non zero code
            raise BuildException("""Container {container} exited with non-zero exit-code.
               Committed: [{container}] -> [{image}]
               Log: docker logs -f {container_id}""". \
                    format(container=name, container_id=container_id, image="%s:%s"%(self.build_id,tag)))
        self.dc().stop(container=name)

        # commit the currently processed container
        tag = "%s-%s"%(self.current_stage, self._nextseq())
        self.dc().commit(container=name, repository=self.build_id, tag=tag)
        self.log(4, "container [%s] committed -> [%s]"%(container_id, "%s:%s"%(self.build_id,tag)))

    def CREATE_BBLAYERS(self, args):
        """
            create bblayers.conf
        """

        self.conf_creator.set_decl(self.decl)
        self.conf_creator.create_bblayers()

        self.file_socket_send(self.conf_creator.bblayers, "/REDO/build/conf/bblayers.conf")

        self.log(6, "CREATING_BBLAYERS")

    def CREATE_LOCAL_CONF(self, args):
        """
            create local.conf
        """

        self.conf_creator.set_decl(self.decl)
        self.conf_creator.create_local_conf()

        self.file_socket_send(self.conf_creator.local_conf, "/REDO/build/conf/local.conf")

        self.log(6, "CREATING_LOCAL_CONF")

    def REPOSYNC(self, args):
        """
            sync all repos
        """

        self.repotool.set_declaration(self.decl)
        cmds = self.repotool.checkout_all("/REDO/source")
        for cmd in cmds:
            self.RUN("/bin/bash -c \"%s\""%cmd)
            self.log(6, "RUN /bin/bash -c \"%s\""%cmd)

    def FROM(self, image):
        """
            The FROM line has to be present in entry-stages
            without prestages. This is the verbatim image specifier
            used by docker to start the first stage.
            Unlike other actions this line is not parsed in this place
            but during build-chain generation, hence it is a mistake
            if this code is reached.
        """
        assert(False)


    def RUN(self, cmd):
        """
            RUN command within a docker container
        """
        name = self._current_container()

        # create the container
        container = self.dc().create_container(image=self._current_image(), name=name, command=cmd)
        container_id = container.get('Id') or container.get('id')
        self.log(6, "new container started [%s] from [%s]"%(container_id, self._current_image()))

        # start the container
        self.dc().start(container=name, privileged=True)

        # wait till the command is executed
        if self.dc().wait(container=name) is not 0:
            tag = "%s-%s-fail"%(self.current_stage, self._nextseq())
            self.dc().commit(container=name, repository=self.build_id, tag=tag)
            # raise Exception if the command exited with a non zero code
            raise BuildException("""Container {container} exited with non-zero exit-code.
               Committed: [{container}] -> [{image}]
               Log: docker logs -f {container_id}""". \
                    format(container=name, container_id=container_id, image="%s:%s"%(self.build_id,tag)))

        # commit the currently processed container
        tag = "%s-%s"%(self.current_stage, self._nextseq())
        self.dc().commit(container=name, repository=self.build_id, tag=tag)
        self.log(6, "container [%s] committed -> [%s]"%(container_id, "%s:%s"%(self.build_id,tag)))

    def ADD(self, parameter):
        """
            ADD a file to an image
        """

        # split filename and target
        file_name, target = parameter.split()
        # add the directory of the current stage to the filename
        file_name=self.decl.stage(self.current_stage)["basepath"] + "/" + self.current_stage + "/" + file_name
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
        volume_path=self.decl.stage(self.current_stage)["basepath"] + "/" + self.current_stage
        # set the name of the container being processed
        name = "%s-%s-%s"%(self.build_id, self.current_stage, self._seq())

        # create the container to create target dir
        container = self.dc().create_container(image=self._current_image(), name=name, command="/bin/mkdir -pv " + os.path.dirname(target))
        container_id = container.get('Id') or container.get('id')
        self.log(4, "new container started [%s] from [%s]"%(container_id, self._current_image()))

        # run the container
        self.dc().start(container=name)

        # commit when the container exited with a non zero exit code
        if self.dc().wait(container=name) is not 0:
            raise BuildException("Container " + name + " could not create a dir to use for th ADD command")
        
        tag = "%s-%s"%(self.current_stage, self._seq())
        self.dc().commit(container=name, repository=self.build_id, tag=tag)
        self.log(4, "container [%s] committed -> [%s]"%(container_id, "%s:%s"%(self.build_id,tag)))

        # set the name of the container being processed
        name = "%s-%s-%s-%s"%(self.build_id, self.current_stage, self._seq(), "copy")

        # create the container to copy file
        container = self.dc().create_container(image=self._current_image(), name=name, volumes=volume_path, command="cp -rv \"/files/" + file_name + "\" " + target)
        container_id = container.get('Id') or container.get('id')
        self.log(4, "new container started [%s] from [%s]"%(container_id, self._current_image()))

        # start the container with the files dir of the stage connected as a volume
        self.dc().start(container=name, binds={
                volume_path:
                    {
                        'bind': '/files/',
                        'ro': True
                    }})

        # commit when the container exited with a non zero exit code
        if self.dc().wait(container=name) != 0:
            # raise Exception if the command exited with a non zero code
            raise BuildException("Container " + name + " exited with a non zero exit status")

        tag = "%s-%s"%(self.current_stage, self._nextseq())
        self.dc().commit(container=name, repository=self.build_id, tag=tag)
        self.log(4, "container [%s] committed -> [%s]"%(container_id, "%s:%s"%(self.build_id,tag)))

    def WORKDIR(self, directory):
        """
            set a WORKDIR for an image
        """

        # set name for the current container being processed
        name = "%s-%s-%s"%(self.build_id, self.current_stage, self._seq())

        # create the container
        container = self.dc().create_container(image=self._current_image(), name=name, working_dir=directory)
        container_id = container.get('Id') or container.get('id')
        self.log(4, "new container started [%s] from [%s]"%(container_id, self._current_image()))

        # commit when the container exited with a non zero exit code
        if self.dc().wait(container=name) is not 0:
            # raise Exception if the command exited with a non zero code
            raise BuildException("Container " + name + " exited with a non zero exit status")

        tag = "%s-%s"%(self.current_stage, self._nextseq())
        self.dc().commit(container=name, repository=self.build_id, tag=tag)
        self.log(4, "container [%s] committed -> [%s]"%(container_id, "%s:%s"%(self.build_id,tag)))

    def ENTRYPOINT(self, cmd):
        """
            set entry point of image
        """

        # set the name of the container being processed
        name = "%s-%s-%s"%(self.build_id, self.current_stage, self._seq())

        # create the container
        container = self.dc().create_container(image=self._current_image(), name=name, command=cmd)
        container_id = container.get('Id') or container.get('id')
        self.log(4, "new container started [%s] from [%s]"%(container_id, self._current_image()))

        # commit when the container exited with a non zero exit code
        if self.dc().wait(container=name) is not 0:
            # raise Exception if the command exited with a non zero code
            raise BuildException("Container " + name + " exited with a non zero exit status")

        tag = "%s-%s"%(self.current_stage, self._nextseq())
        self.dc().commit(container=name, repository=self.build_id, tag=tag)
        self.log(4, "container [%s] committed -> [%s]"%(container_id, "%s:%s"%(self.build_id,tag)))

# vim:expandtab:ts=4

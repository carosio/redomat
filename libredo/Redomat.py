import getpass, time, os, logging, socket, sys
from libredo import Repotool
from libredo.ConfCreator import ConfCreator
import xml.etree.ElementTree as XML
from multiprocessing import Process
import re

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
        self.service_version = "1.15"
        self.repotool = Repotool.Repotool(self.decl)
        self.conf_creator = ConfCreator(self.decl)
        # stage that is build
        self.current_stage = None
        # current image name that is processed

        self.container_id = None

        # flag for image search-operation and selection
        # (allow other user's images as candidates)
        self.include_foreigns = False

        self.command_line_extra_local_conf = []
        # some options, see accessor function for details
        self.build_id = None
        self.match_build_id = None
        self.entry_image = None
        self.dry_run = False
        self.commit_failures = True
        self._entry_stage = None
        self.loglevel = logging.INFO
        self.logformat = '%(asctime)s %(levelname)s: %(message)s'
        logging.basicConfig(format=self.logformat, level=self.loglevel)

        self.username = getpass.getuser()

        self.allowed_commands = set(['CREATE_BBLAYERS','CREATE_LOCAL_CONF','REPOSYNC', 'FROM', 'RUN', 'ADD'])

    def dc(self):
        "return docker client instance (imports docker module)"
        if None == self._dclient:
            if 'docker' not in dir():
                import docker
            self._dclient = docker.Client(base_url=self.service_url,version=self.service_version,timeout=2400)
            # monkey patch our client.execute improvement
            from libredo._docker_py import better_docker_execute
            self._dclient.__class__.better_execute = better_docker_execute
        return self._dclient

    def set_entry_stage(self, s):
        self._entry_stage = s

    def append_local_conf(self, local_conf_line):
        """
        append more lines to the local.conf
        this is in addition to local.conf-contents
        declared in the xml files.
        """

        if self.decl:
            self.decl.append_local_conf(local_conf_line)
        else:
            # this will be added to the decl in set_decl()
            self.command_line_extra_local_conf.append(local_conf_line)

    def log(self, severity, message):
        m = ['[']
        if self.build_id:
            m.append("%s"%self.build_id)
        if self.current_stage:
            m.append("%s"%self.current_stage)
        if self.container_id:
            m.append("%s"%(self.container_id[:8]))
        m.append(']')
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

        # command-line-extra-local-conf contents might
        # exist already. (can be added before parsing)
        while len(self.command_line_extra_local_conf) > 0:
            self.decl.append_local_conf(self.command_line_extra_local_conf.pop(0))

    def set_dryrun(self, dry):
        """
            set_dryrun(True) - do not actually build anything, but output what would be done
            set_dryrun(False) - well... do it.
        """
        self.dry_run = dry

    def set_commitfailures(self, cf):
        """
            set_commitfailures(True) - commit (and tag) a docker container after failure
            set_commitfailures(False) - don't.
        """
        self.commit_failures = cf

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

    def set_entry_image(self, _repoTag):
        """
            set image to be used as starting point
            can be specified as repo:tag or image_id
        """
        self.entry_image = _repoTag

    def set_build_id(self, _buildid):
        """
            set the actual build-id of the new build.
            use of this is discouraged. build-ids should
            be unique. Redomat will generate a suitable build-id
            if this function is not used.
        """

        self.build_id = re.sub('[^a-zA-Z0-9_.-]', '', _buildid)

    def get_image(self, repo_tag):
        """
            return the image id for the given repo:tag
        """
        images = self.dc().images()
        matches = []
        for image in images:
            if image['Id'].startswith(repo_tag):
                matches.append(image['Id'])
        for image in images:
            if repo_tag in image['RepoTags']:
                matches.append(image['Id'])
        if len(matches) == 0:
            raise Exception("get_image(\"%s\") did not match any image"%repo_tag)
        elif len(matches) > 1:
            self.log(3, "ambiguous image specification \"%s\". possible matches: %s"%(repo_tag, ",".join(matches)))
            raise Exception("no unique match for get_image(\"%s\")"%repo_tag)
        return matches[0]

    def resolve_stage_to_image(self, stage):
        """
            this function takes a stage-id from the stage-declaration
            as input and tries to find a matching image.
            the matching strategy depends on match_build_id, the username
            and the include_foreigns option.

            if no image is found None is returned. this usually means
            that a rebuild of the stage is necessary.
        """

        if not self.match_build_id:
            return None
        self.log(6, "trying to match [%s - %s]"%(stage, self.match_build_id))
        for image in self.find_images_by_pattern(self.match_build_id):
            if stage in map(lambda x:x.split(":")[-1], image['RepoTags']):
                self.log(6, "MATCH image: {img}".format(img=image['Id']))
                return image['Id']
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

        if self.entry_image and not self._entry_stage:
            # -U without -e --> default to last declared stage
            self._entry_stage = target

        self.log(7, "generating build-chain")
        while True:
            stage = self.decl.stage(sid)
            assert(type(stage) == dict)

            prestage = stage.get("prestage")

            if self.entry_image:
                if stage.get("id") == self._entry_stage:
                    self.log(6, "entry stage matched. the chain ends/starts here.")
                    chain.append((self._entry_stage, self.get_image(self.entry_image)))
                    break

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
                image = fromline.split(" ")[1].split(":")[0]
                tag = fromline.split(" ")[1].split(":")[1]
                print(self.dc().images(name=image))
                for y in self.dc().images(name=image):
                    for x in y["RepoTags"]:
                        tags.append(x.split(":")[1])
                print(tags)
                if tag not in tags:
                    self.log(7, "could not find %s in local registry trying to locate it on dockerhub"%image)
                    if [] != self.dc().search(image):
                        self.log(7, "%s found on dockerhub"%image)
                        self.log(7, "trying to pull %s:%s"%(image, tag))
                        self.dc().pull(repository=image, tag=tag)
                        tags = []
                        for x in self.dc().images(name=fromline.split(" ")[1].split(":")[0]):
                            tags.append(x["RepoTags"])
                        if tag not in tags:
                            raise Exception("%s:%s could not be obtained no such tag"%(image, tag))
                        self.log(7, "successfully pulled %s:%s"%(image, tag))
                chain.append((sid, fromline.split(" ")[1].strip()))
                break
        self.log(6, "build-chain: %s"%chain)

        if self.entry_image and self._entry_stage:
            if not chain[-1][0] == self._entry_stage:
                raise BuildException("entry stage [%s] not matched."%self._entry_stage)
        return chain

    def build_stage(self, stage, pre_image):
        """
            run all actions of a stage
        """

        stage_decl = self.decl.stage(stage)
        if not stage_decl:
            self.log(3, "unable to access declaration for stage [%s]"%stage)
            raise BuildException("cannot build. stage [%s]. stage undeclared."%stage)

        self.current_stage = stage


        # tag the current image
        tag = self.current_stage + "-start"
        if not self.dry_run:
            self.dc().tag(pre_image, self.build_id, tag=tag)
            self.log(5, "successfully tagged %s as [%s@%s]"%(pre_image, self.build_id, tag))
        else:
            self.log(5, "successfully (not) tagged %s as [%s@%s]"%(pre_image, self.build_id, tag))

        name="%s-%s"%(self.build_id,self.current_stage)

        failures = 0
        for action in stage_decl['actions']:
            if not self.dry_run:
                self.log(7, "executing action [%s]"%action)
                if not self.handle_action(action):
                    # failure:
                    failures = failures + 1
                    self.log(6, "action [%s] failed"%action)
                    # if not "-k" ...
                    break
            else:
                self.log(5, "(not) executing action [%s]"%action)


        if failures == 0:
            tag = self.current_stage
        else:
            tag = self.current_stage + "-failure"

        cid = self.container_id
        if not self.dry_run:
            if (failures == 0) or self.commit_failures:
                self.log(5, "end of stage actions. committing (%s): %s:%s"%(cid[:8], self.build_id, tag))
                res = self.dc().commit(container=cid, repository=self.build_id, tag=tag)
        else:
            self.log(5, "end of stage actions. (not) committing (%s): %s:%s"%(cid[:8], self.build_id, tag))

        return failures == 0

    def build(self, stage):
        """
            build the given stage.
            depending on how the stage-dependency-resolution-policy is set,
            dependent stages are either resolved or build.
        """

        self.log(5, "starting build.")

        if not self.build_id:
            # generate a buildid if non was provided
            self.build_id = "%s-%s"%(time.strftime("%F-%H%M%S"), self.username)
            self.log(6, "build-id generated: [%s]"%self.build_id)


        self.repotool.set_syncid(self.build_id)
        build_chain = self.generate_build_chain(stage)

        # check pre-image
        pre_image = build_chain[-1][1] # peek first stage's pre_image
        try:
            pre_image_details = self.dc().inspect_image(pre_image)
            # key changed from id to Id between 0.6.0 and following 
            # docker client versions. we try to be compatible
            image_id =  pre_image_details.get('Id') or  pre_image_details.get('id')
            self.log(6, "pre-image [%s] resolved to: %s"%(pre_image, image_id))
        except Exception, e: # FIXME catch more precisely
            self.log(3, e.__str__())
            raise BuildException("cannot build. pre_image [%s] not accesible."%pre_image)

        # create container with some bogus loop, this will change to some httpd
        res = self.dc().create_container(image=pre_image, name=self.build_id,
                command="/bin/sh -c 'while [ ! -e /REDO/container-terminated ] ; do sleep 1 ;date; done'")
        self.container_id = res['Id']
        self.dc().start(container=self.container_id, privileged=True)

        #stage, pre_image = build_chain.pop()

        #success = self.build_stage(stage, pre_image)

        # prepare for result serving
        self.RUN('mkdir -p /REDO/source')
        self.file_send(self.build_id, "/REDO/source/BUILDID")

        # add serve.sh
        self.RUN("mkdir -p /REDO/results")
        serve_script = open(os.path.join(os.path.split(__file__)[0], "data/serve.sh"))
        self.file_send(serve_script.read(), "/REDO/results/serve.sh", "unlink,mode=0755")
        self.RUN("chmod +x /REDO/results/serve.sh")

        serve_script.close()

        # add result_httpd.py
        self.RUN("mkdir -p /REDO/results")
        serve_script = open(os.path.join(os.path.split(__file__)[0], "data/result_httpd.py"))
        self.file_send(serve_script.read(), "/REDO/results/result_httpd.py", "unlink,mode=0755")
        serve_script.close()

        #
        # start building the stages
        #
        try:
            while build_chain:
                stage, pre_image = build_chain.pop()

                if not self.build_stage(stage, pre_image):
                    return False
        finally:
            self.dc().better_execute(self.container_id, 'touch /REDO/container-terminated')
        return True

    def _current_image(self):
        return "%s:%s"%(self.build_id, self.current_stage)

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

    def find_images_by_pattern(self, pattern):
        for image in self.dc().images(name=pattern):
            yield image

    def list_all_buildID(self):
        build_ids = []
        for image in self.dc().images(all=True):
            for tag in image['RepoTags']:
                build_ids.append(tag.split(":")[0])
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
        if not docker_command[0] in self.allowed_commands:
            raise Exception("unsupported command <%s>"%docker_command[0])

        # raise exception if there is no matching function
        if not hasattr(self, docker_command[0]):
            raise Exception("unknown command <%s>"%docker_command[0])
        callback = getattr(self, docker_command[0])

        # pass the commands to the redomat
        return callback(" ".join(docker_command[1:]).strip())

    def file_send(self, data, filename, _options="unlink"):
        """ send data into a file in the container """
        execres = self.dc().better_execute(self.container_id, 'dd of="%s"'%filename, attach_stdin=True)

        # send file
        insock = execres.input_sock()
        insock.sendall(data)
        execres.close_input()
        self.log(6, "sent data to {filename} in container {cid}".format(filename=filename, cid=self.container_id[:8]))
        return execres.exit_code() == 0

    def CREATE_BBLAYERS(self, args):
        """
            create bblayers.conf
        """

        self.conf_creator.set_decl(self.decl)
        self.conf_creator.create_bblayers()

        self.RUN('mkdir -p /REDO/build/conf')

        self.log(6, "CREATING_BBLAYERS")
        return self.file_send(self.conf_creator.bblayers, "/REDO/build/conf/bblayers.conf")

    def CREATE_LOCAL_CONF(self, args):
        """
            create local.conf
        """

        self.conf_creator.set_decl(self.decl)
        self.conf_creator.create_local_conf()

        self.RUN('mkdir -p /REDO/build/conf')

        self.log(6, "CREATING_LOCAL_CONF")
        return self.file_send(self.conf_creator.local_conf, "/REDO/build/conf/local.conf")

    def REPOSYNC(self, args):
        """
            sync all repos
        """

        self.repotool.set_declaration(self.decl)
        cmds = self.repotool.checkout_all("/REDO/source")
        for cmd in cmds:
            self.log(6, "RUN /bin/sh -c \"%s\""%cmd)
            if not self.RUN("/bin/sh -c \"%s\""%cmd):
                return False
        return True

    def FROM(self, image):
        """
            The FROM line has to be present in entry-stages
            without prestages. This is the verbatim image specifier
            used by docker to start the first stage.
            Unlike other actions this line is not parsed in this place
            but during build-chain generation, hence it is a mistake
            if this code is reached.
            Unless...
            ...the very first stage is selected as the entry-stage (-e)
            on the command line. Then it just needs to be ignored.
        """
        if self._entry_stage:
            self.log(6, "ignoring FROM declaration.")
            return True
        else:
            assert(False)


    def RUN(self, cmd):
        """
            RUN command within a docker container
        """
        name ="%s-%s"%(self.build_id,self.current_stage)

        cid = self.container_id
        if not self.dc().inspect_container(container=cid)['State']['Running']:
            self.log(5, 'Starting container {container} for RUN...'.format(container=cid))
            assert(False) # this is unexpected
            self.dc().start(container=cid, privileged=True)

        self.log(6, "running %s"%(cmd))
        execres = self.dc().better_execute(container=cid, cmd=cmd, linebased=False)

        for chunk in execres.output_gen:
            self.log(6, "output: [%s]"%chunk.strip())

        rc = execres.exit_code()
        self.log(6, 'RUN/EXEC exit-code: %s'%rc)
        return rc == 0

    def ADD(self, parameter):
        """
            ADD a file to an image
        """

        # split filename and target
        source, target = parameter.split()

        if not source:
            raise Exception("ADD: no source filename specified.")

        if not target:
            raise Exception("ADD: no target filename specified")

        # support relative paths
        if source[0] != '/':
            resolved_source = self.decl.stage(self.current_stage)["basepath"] + "/" + self.current_stage + "/" + source

            if not os.path.exists(resolved_source):
                resolved_source = self.decl.stage(self.current_stage)["basepath"] + "/" + source

        # check if the file exists
        if not os.path.exists(resolved_source):
            raise Exception("ADD: specified source file [%s] does not exist: %s"%(source,resolved_source))

        f = open(resolved_source, 'r')
        rc = self.file_send(f.read(), target)
        self.log(6, 'ADD: %s.'%{True: "succeeded", False: "failed"}[rc])
        f.close()
        return rc

# vim:expandtab:ts=4

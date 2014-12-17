from docker import Client
import sys,time, os

class Redomat:

	def __init__(self,client=None):
		"""
			a builder for yocto using docker to support builds on top of other builds
		"""
		if client is None:
			raise Exception("client is not set")
		self.client = client
		self.current_stage = "undefined"
		self.current_image = "undefined"
		self.build_id = "%s-%s"%(time.strftime("%F-%H%M%S"), os.getenv('LOGNAME'))
		self.run_sequence = 0

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
		if image is None:
			raise Exception("no image given to work with")

		self.current_image="%s-%s-%s"%(time.strftime("%F-%H%M%S"), os.getenv('LOGNAME'), self.current_stage)
		self.client.tag(image,self.current_image)

	def RUN(self, cmd=None):
		"""
			RUN command within a docker container
		"""
		if self.client is None:
			raise Exception("No client given to work with")
		if cmd is None:
			raise Exception("RUN needs atleast one comman")

		name = "%s-%s-%s"%(self.build_id, self.current_stage, self._nextseq())
		self.client.create_container(image=self.current_image, name=name, command=cmd)
		self.client.start(container=name, privileged=True)

		if self.client.wait(container=name) is not 0:
			raise Exception("Container " + name + " exited with a non zero exit status")
		self.client.commit(container=name, repository=self.current_image)

	def ADD(self, parameter=None):
		"""
			ADD a file to an image
		"""
		if parameter is None:
			raise Exception("No parameter given")
		file_name, target =parameter.split()
		file_name=self.current_stage + "/" + file_name
		if file_name is None:
			raise Exception("No filename given")
		if target is None:
			raise Exception("No target directory given")
		if os.path.exists(file_name) is False:
			raise Exception("No such file: " + file_name)

		file_name=os.path.basename(file_name)
		volume_path=os.path.abspath(self.current_stage)
		name = "%s-%s-%s-%s"%(self.build_id, self.current_stage, self._nextseq(), "create-target_dir")

		self.client.create_container(image=self.current_image, name=name, command="/bin/mkdir -pv " + os.path.dirname(target))
		self.client.start(container=name)
		if self.client.wait(container=name) is not 0:
                         raise Exception("Container " + name + " could not create a dir to use for th ADD command")
		self.client.commit(container=name, repository=self.current_image)

		name = "%s-%s-%s-%s"%(self.build_id, self.current_stage, self._nextseq(), "copy-data")

		self.client.create_container(image=self.current_image, name=name, volumes=volume_path, command="cp -rv /files/" + file_name + " " + target)
		self.client.start(container=name, binds={
				volume_path:
					{
						'bind': '/files/',
						'ro': True
					}})

		if self.client.wait(container=name) is not 0:
			raise Exception("Container " + name + " exited with a non zero exit status")
		self.client.commit(container=name, repository=self.current_image)

	def WORKDIR(self, directory=None):
		"""
			set a WORKDIR for an image
		"""
		if directory is None:
			raise Exception("No directory given")
		name = "%s-%s-%s"%(self.build_id, self.current_stage, self._nextseq())
		self.client.create_container(image=self.current_image, name=name, working_dir=dircetory)

		if self.client.wait(container=name) is not 0:
			raise Exception("Container " + name + " exited with a non zero exit status")
		self.client.commit(container=name, repository=self.current_image)

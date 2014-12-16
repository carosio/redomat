from docker import Client
import sys,time, os

class Redomat:

	def __init__(self,client=None):
		if client is None:
			raise Exception("client is not set")
		self.client = client
		self.current_stage = "undefined"
		self.current_image = "undefined"
		self.build_id = "%s-%s"%(time.strftime("%F-%H%M%S"), os.getenv('LOGNAME'))
		self.run_sequence = 0

	def _nextseq(self):
		self.run_sequence = self.run_sequence + 1
		return "%03i"%self.run_sequence

	def FROM(self, image=None):
		if image is None:
			raise Exception("no image given to work with")
		self.client.tag(image,self.current_image)

	def STAGE(self, stage=None):
		if stage is None:
			raise Exception("No stage given")
		self.current_stage=stage
		self.current_image="%s-%s-%s"%(time.strftime("%F-%H%M%S"), os.getenv('LOGNAME'), self.current_stage)

	def RUN(self, cmd=None):
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

	def ADD(self, file_name=None, target_dir=None):
		if filename is None:
			raise Exception("No filename given")
		if target_dir is None:
			raise Exception("No target directory given")
		if os.path.exists(file_name) is False:
			raise Exception("No such file")
		file_name=os.path.basename(file_name)
		volume_path=os.path.abspath(self.current_stage)

		self.client.create_container(image=self.current_image, name=name, volumes=volume_path, command="mkdir -p " + target_dir  + " && cp -rv /files/" + file_name + " " + target_dir)
		self.client.start(name=name, bind={
				'/files/':
					{
						'bind': volume,
						'ro':True
					}})
		self.client.commit(container=name, repository=self.current_image)

	def WORKDIR(self, directory=None):
		if directory is None:
			raise Exception("No directory given")
		name = "%s-%s-%s"%(self.build_id, self.current_stage, self._nextseq())
		delf.client.create_container(image=self.current_image, name=name, working_dir=dircetory)
		self.client.commit(container=name, repository=self.current_image)

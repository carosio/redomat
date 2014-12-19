from docker import Client
import sys, time, os
import xml.etree.ElementTree as XML

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
		self.laststage = "undefined"
		self.build_id = "%s-%s"%(time.strftime("%F-%H%M%S"), os.getenv('LOGNAME'))
		self.run_sequence = 0

	def data_parser(self, docker_line):
		docker_command = docker_line.split(" ")

		if not hasattr(self, docker_command[0]):
			raise Exception("unknown command <%s>"%docker_command[0])
		callback = getattr(self, docker_command[0])

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
		if image is None:
			raise Exception("no image given to work with")

		self.current_image="%s-%s-%s"%(time.strftime("%F-%H%M%S"), os.getenv('LOGNAME'), self.current_stage)
		try:
			self.client.tag(image,self.current_image)
		except:
			image, image_tag = image.split(":")
			print("pulling: " + image + ":" + image_tag)
			self.client.pull(repository=image,tag=image_tag)
			self.client.tag(image + ":" + image_tag,self.current_image)

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

class XML_creator:
	def __init__(self, xml_file=None):
		if xml_file is None:
			raise Exception("no xml file name given")

		if os.path.exists(xml_file) is False:
			raise Exception(xml_file + "no such file or directory")

		self.manifest_root=XML.parse(xml_file).getroot()

	def create_repoxml(self,out_name=None):
		if out_name is None:
			raise Exception("no output file name given")

		if os.path.exists(out_name):
			raise Exception(out_name + "file already exists")

		repo_xml_root = XML.Element("manifest")

		for layer_declaration in self.manifest_root.iter('layer_declaration'):
			for repo_line in layer_declaration.iter().next():
				if repo_line.tag == 'layer':
					repo_xml = XML.SubElement(repo_xml_root, 'project')
				else:
					repo_xml = XML.SubElement(repo_xml_root, repo_line.tag)
				for attribute, value in repo_line.attrib.iteritems():
					repo_xml.set(attribute, value)

		tree = XML.ElementTree(repo_xml_root)
		tree.write(out_name)

class XML_parser:
	def __init__(self, xml_file=None):
		if xml_file is None:
			raise Exception("no xml file name given")

		if os.path.exists(xml_file) is False:
			raise Exception(xml_file + "no such file or directory")

		self.manifest_root=XML.parse(xml_file).getroot()
		self.stages = []

	def parse(self, redomat=None):
		if redomat is None:
			raise Exception("no redomat name given")

		for buildstage in self.manifest_root.iter('buildstage'):
			stage = {'id': buildstage.get('id'),
				'build' : False,
				'dockerlines' : []}
			self.stages.append(stage)

			for stage_command in buildstage.iter():
				if stage_command.tag == 'prestage':
					stage['dockerlines'].append("FROM " + redomat.laststage)

				elif stage_command.tag == 'bitbake_target':
					stage['dockerlines'].append('RUN bitbake ')
					if stage_command.get('command'):
						stage['dockerlines'].append(stage['dockerlines'].pop() + '-c ' + stage_command.get('command'))
						stage['dockerlines'].append(stage['dockerlines'].pop() + " " + stage_command.text)
					else:
						stage['dockerlines'].append(stage['dockerlines'].pop() + stage_command.text)

				elif stage_command.tag == 'dockerline':
					stage['dockerlines'].append(stage_command.text)

		return self.stages



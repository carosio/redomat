# function for parsing the data
import docker
import sys
import os
import xml.etree.ElementTree as XML
from redomatfunctions import Redomat

def xml_parser(xml_file):
	manifest_root = XML.parse(xml_file).getroot()
	stages = []

	for buildstage in manifest_root.iter('buildstage'):
		stage = {'id': buildstage.get('id'),
			'dockerlines' : [],
			'bitbake_target' : {'cmd' : [], 'target' : [] }}
		stages.append(stage)

		for stage_command in buildstage.iter():

			if stage_command.tag == 'dockerline':
				stage['dockerlines'].append(stage_command.text)

			if stage_command.tag == 'bitbake_target':
				stage['dockerlines'].append('RUN bitbake ')
				if stage_command.get('command'):
					stage['dockerlines'].append(stage['dockerlines'].pop() + '-c ' + stage_command.get('command'))
					stage['dockerlines'].append(stage['dockerlines'].pop() + " " + stage_command.text)
				else:
					stage['dockerlines'].append(stage['dockerlines'].pop() + stage_command.text)
	return stages

def data_parser(docker_line, redo):
	docker_command = docker_line.split(" ")

	if not hasattr(redo, docker_command[0]):
		raise Exception("unknown command <%s>"%docker_command[0])
	callback = getattr(redo, docker_command[0])

	callback(" ".join(docker_command[1:]).strip())

for dockerfile in sys.argv[1:]:
	if os.path.exists(dockerfile) is False:
		raise Exception("No Dockerfile found")
		sys.exit(1)

	stages=xml_parser(dockerfile)

	redo = Redomat(docker.Client(base_url='unix://var/run/docker.sock',version='0.6.0'))

	for stage in stages:
		print(stage['id'])
		for line in stage['dockerlines']:
			print(line)
			data_parser(line, redo)
		print()

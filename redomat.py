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
			'build' : False,
			'dockerlines' : []}
		stages.append(stage)

		for stage_command in buildstage.iter():
			if stage_command.tag == 'prestage':
				stage['dockerlines'].append("FROM " + redo.laststage)

			elif stage_command.tag == 'bitbake_target':
				stage['dockerlines'].append('RUN bitbake ')
				if stage_command.get('command'):
					stage['dockerlines'].append(stage['dockerlines'].pop() + '-c ' + stage_command.get('command'))
					stage['dockerlines'].append(stage['dockerlines'].pop() + " " + stage_command.text)
				else:
					stage['dockerlines'].append(stage['dockerlines'].pop() + stage_command.text)

			elif stage_command.tag == 'dockerline':
				stage['dockerlines'].append(stage_command.text)

	return stages

def data_parser(docker_line, redo):
	docker_command = docker_line.split(" ")

	if not hasattr(redo, docker_command[0]):
		raise Exception("unknown command <%s>"%docker_command[0])
	callback = getattr(redo, docker_command[0])

	callback(" ".join(docker_command[1:]).strip())

if sys.argv[1] == '-s':
	start_number=3
	start_point=sys.argv[2]
	build=False
else:
	start_point=None
	build=True
	start_number=1

for dockerfile in sys.argv[start_number:]:
	if os.path.exists(dockerfile) is False:
		raise Exception("No Dockerfile found")
		sys.exit(1)

	redo = Redomat(docker.Client(base_url='unix://var/run/docker.sock',version='0.6.0'))

	stages=xml_parser(dockerfile)

	for stage in stages:
		if stage['id'] == start_point:
			build = True
		if build==True:
			stage['build']=True

	for stage in stages:
		print(stage['id'])
		print(stage['build'])
		redo.current_stage = stage['id']
		for line in stage['dockerlines']:
			if stage['build']:
				print(line)
				data_parser(line, redo)
		redo.laststage = redo.current_image
		print("done building: " + stage['id'])

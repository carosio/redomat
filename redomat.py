# function for parsing the data
import docker
import sys
import os
import xml.etree.ElementTree as XML
from redomatfunctions import Redomat
from redomatfunctions import XML_creator
from redomatfunctions import XML_parser

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

	stages=XML_parser(dockerfile).parse(redo)
	XML_creator(dockerfile).create_repoxml("repo-" + dockerfile)

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
				redo.data_parser(line)
		redo.laststage = redo.current_image
		print("done building: " + stage['id'])

# function for parsing the data
import docker
import sys
import os
from redomatfunctions import Redomat


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

	inputfile = open(dockerfile)

	redo = Redomat(docker.Client(base_url='unix://var/run/docker.sock',version='0.6.0'))
	for line in inputfile:
		if line.strip() == "":
			continue
		if line.strip().startswith("#"):
			continue
		data_parser(line.strip(), redo)

	inputfile.close()

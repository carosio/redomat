# function for parsing the data
import docker

import os
from redomatfunctions import Redomat


def data_parser(docker_line, redo):
	docker_command = docker_line.split(" ")

	if not hasattr(redo, docker_command[0]):
		raise Exception("unknown command <%s>"%docker_command[0])
	callback = getattr(redo, docker_command[0])

	callback(" ".join(docker_command[1:]).strip())


#reps[i]("ubuntu:14.04")

inputfile = open('Dockerfile.sh')

#reps = {'STAGE':redomatfunctions.STAGE,'FROM':redomatfunctions.FROM,'RUN':redomatfunctions.RUN}

redo = Redomat(docker.Client(base_url='unix://var/run/docker.sock'))
for line in inputfile:
	if line.strip() == "":
		continue
	if line.strip().startswith("#"):
		continue
	data_parser(line.strip(), redo)

inputfile.close()


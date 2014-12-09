# function for parsing the data
from docker import Client
import os
from redomatfunctions import redomat

client = Client(base_url='unix://var/run/docker.sock')
redo = redomat(client)

def data_parser(text, dic):
	for i, j in dic.items():
		if i in text :
			#print(text.replace(i+" ",""))
			x=str(text.replace(i+" ",""))
			reps[i](x)
#reps[i]("ubuntu:14.04")

inputfile = open('Dockerfile.sh')

#reps = {'STAGE':redomatfunctions.STAGE,'FROM':redomatfunctions.FROM,'RUN':redomatfunctions.RUN}
reps = {'FROM':redo.FROM}

for line in inputfile:
	data_parser(line, reps)

inputfile.close()


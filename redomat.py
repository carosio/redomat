#!/usr/bin/python
# function for parsing the data
import docker
import sys
import os
import getopt
import xml.etree.ElementTree as XML
from redomatfunctions import Redomat
from redomatfunctions import XML_creator
from redomatfunctions import XML_parser

def main(argv):
	try:
		opts, args = getopt.getopt(argv,"hs:",["images"])
	except getopt.GetoptError:
		print("redomat <option> <redomat.xml>\n\t-h\t\tprint this help\n\t-s <STAGE>\tstart building from STAGE")
		sys.exit(1)

	start_point=None
	build=True
	dockerfiles=args

	for opt, arg in opts:
		if opt == '-h':
			print("redomat <option> <redomat.xml>\n\t-h\t\tprint this help\n\t-s <STAGE> <BUILD_ID> <redomat.xml>\tstart building from STAGE")
			sys.exit()
		elif opt == '-s':
			print("using -s")
			dockerfiles=args[1:]
			start_point=arg
			build_id=args[0]
			build=False
		elif opt == '--images':
			for x in docker.Client(base_url='unix://var/run/docker.sock',version='0.6.0').images(name=str('*'+os.getenv('LOGNAME')+'*')):
				print(x['Repository'])
			sys.exit()

	for dockerfile in dockerfiles:
		if os.path.exists(dockerfile) is False:
			raise Exception("No Dockerfile found")
			sys.exit(1)

		redo = Redomat(docker.Client(base_url='unix://var/run/docker.sock',version='0.6.0'))

		stages=XML_parser(dockerfile).parse(redo)
		XML_creator(dockerfile).create_repoxml("init-repo/repo-" + dockerfile)

		for stage in stages:
			if stage['id'] == start_point:
				build = True
			if build==True:
				stage['build']=True

		for stage in stages:
			print(stage['id'])
			print(stage['build'])
			redo.current_stage = stage['id']

			XML_creator(dockerfile).create_bblayers(stage['id'] + "/bblayers.conf")

			for line in stage['dockerlines']:
				if stage['build']:
					print(line)
					redo.data_parser(line)
				elif 'FROM' in line:
					redo.current_image=build_id + "-" + stage['id']
			redo.laststage = redo.current_image
			print("laststage: " + redo.laststage)
			print("done building: " + stage['id'])

if __name__ == "__main__":
	main(sys.argv[1:])

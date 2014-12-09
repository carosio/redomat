from docker import Client
import sys

class redomat:

	def __init__(self,client=None):
		if client is None:
			error("client is not set")
		self.cli = client
		self.current_image = "test3"

	def error(*objs):
		print("ERROR: ", *objs, file=sys.stderr)

	def FROM(self, image=None):
		if image is None:
			error("no image given to work with")
			return 1
		print(str(image))
		self.cli.tag(image,self.current_image)

	def STAGE(text=None,):
		if text is None:
			error("No stage given")
			return 1
		print(text)

	def RUN(cmd=None,):
		if self.cli is None:
			error("No client given to work with")
			return 1
		if cmd is None:
			error("RUN needs atleast one commadn")
			return 1
		self.cli.create_container(image=img, name='run-container', command=cmd)
	#	cli.start(

#FROM('ubuntu:14.04',client)
#client.tag('ubuntu:14.04', 'test')
#print(sys.exc_info())

from docker import Client
import sys,time, os

class Redomat:

	def __init__(self,client=None):
		if client is None:
			raise Exception("client is not set")
		self.client = client
		self.current_stage = 'undefined'
		self.current_image = "test3"
		self.build_id = "%s-%s"%(time.strftime("%F-%H%M%S"), os.getenv('LOGNAME'))
		self.run_sequence = 0

	def _nextseq(self):
		self.run_sequence = self.run_sequence + 1
		return "%03i"%self.run_sequence

	def FROM(self, image=None):
		if image is None:
			raise Exception("no image given to work with")
		print(str(image))
		self.client.tag(image,self.current_image)

	def STAGE(self, text=None):
		if text is None:
			raise Exception("No stage given")
		print(text)

	def RUN(self, cmd=None):
		if self.client is None:
			raise Exception("No client given to work with")
		if cmd is None:
			raise Exception("RUN needs atleast one commadn")
		name = "%s-%s-%s"%(self.build_id, self.current_stage, self._nextseq())
		self.client.create_container(image=self.current_image, name=name, command=cmd)
	#	client.start(

#FROM('ubuntu:14.04',client)
#client.tag('ubuntu:14.04', 'test')
#print(sys.exc_info())

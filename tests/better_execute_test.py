import docker,sys
import socket

import readline,rlcompleter
readline.parse_and_bind("tab: complete")

class BetterTest:
	def __init__(self, cid):
		self.cid = cid
		self.service_url = "unix://var/run/docker.sock"
		self.service_version = "1.17"
		self.dc = docker.Client(base_url=self.service_url,version=self.service_version,timeout=2400)

		from libredo._docker_py import better_docker_execute
		self.dc.__class__.better_execute = better_docker_execute

	def test_input(self):
		"use-case: stdin (create a file)"
		print "test_input"
		self.exres = bt.dc.better_execute(self.cid, 'bash -c "rm /foo2 ; dd of=/foo2;exit 17"')
		i = self.exres.input_sock()
		i.send("Hell")
		i.send("o\n")
		i.send("World\n")
		i.shutdown(socket.SHUT_WR) # to pass EOF
		print "ExitCode:", str(self.exres.exit_code())

	def test_output(self):
		"use-case: output..."
		print "test_output"
		self.exres = bt.dc.better_execute(self.cid, 'bash -c "date ; sleep 2 ; date ; exit 13"')
		#o = self.exres['output']()
                for chunk in self.exres.output_gen: print chunk
		print "exit-code", self.exres.exit_code()

        def test_inout(self):
		"use-case: filter"
		print "test_inout"
		self.exres = bt.dc.better_execute(self.cid, 'bash -c "date ; sleep 1 ; tac ; exit 42"')
		i = self.exres.input_sock()
		i.send("One\n")
		i.send("Two\n")
		i.send("Three\n")
		i.shutdown(socket.SHUT_WR) # to pass EOF
		for chunk in self.exres.output_gen: print chunk
		print "ExitCode:", str(self.exres.exit_code())

bt = BetterTest(sys.argv[1])
bt.test_input()
bt.test_output()
bt.test_inout()


#!/usr/bin/python


import readline,rlcompleter
#!/usr/bin/env python

import os, sys

here = os.path.realpath(os.path.dirname(sys.argv[0]))
print here

print __file__
sys.path.insert(0, here+"/..")

import libredo

d = libredo.Declaration()
d.parse("%s/../example/example.xml"%here)

r = libredo.Redomat('unix://var/run/docker.sock')

r.set_decl(d)
r.set_dryrun(True)
r.build('stage3')


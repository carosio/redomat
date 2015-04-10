#!/usr/bin/python

import os, sys

import libredo

here = os.path.realpath(os.path.dirname(sys.argv[0]))
print here


d = libredo.Declaration()
# FIXME copy example declaration into this repo
d.parse("%s/example/example.xml"%here)

r = libredo.Redomat('unix://var/run/docker.sock')
r.add(d)


print d

r.build('001-ubuntu')


#!/usr/bin/python

import os, sys

from libredo.Declaration import Declaration

here = os.path.realpath(os.path.dirname(sys.argv[0]))
print here


d = Declaration()
# FIXME copy example declaration into this repo
d.parse("%s/example/example.xml"%here)

print d


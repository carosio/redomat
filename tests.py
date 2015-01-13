#!/usr/bin/python

import os

from redomatfunctions.Declaration import Declaration

d = Declaration()
# FIXME copy example declaration into this repo
stages = d.parse("%s/vc/tp/tposs-release/redodecl/default.xml"%os.getenv("HOME"))

print stages


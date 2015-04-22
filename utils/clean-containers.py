#!/usr/bin/python

"""
remove non-running containers which terminated
more than 7 days ago
"""

import time
import docker

dc = docker.Client(
	base_url='unix://var/run/docker.sock',
	version='1.15', timeout=900)

for container in dc.containers(all=True):
        cid = container['Id']
	cdata = dc.inspect_container(cid)
        cstate = cdata['State']
	if cstate['Running'] != False:
		continue
        ct_end = time.mktime(time.strptime(cstate['FinishedAt'].split('T')[0], '%Y-%m-%d'))
        if time.time() - ct_end > 7 * 86400:
            print "old, non-running container:",cid
        dc.remove_container(cid)


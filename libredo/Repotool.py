"""
    libredo/Repotool

    Tool for checking out layers from git.

    (This is not the android repo-tool, but 
    a replacement thereof in the scope of Redomat.)
"""

import time, os

class Repotool:

    def __init__(self, _declaration):
        """
            a builder for yocto using docker to support builds on top of other builds
        """
        self.declaration = _declaration

    def checkout(self, destpath, git_url, revision):
        cmds = []
        cmds.append("( mkdir -pv %s ; cd %s ; [ ! -d .git ] && git init )"%
                (destpath, destpath))
        cmds.append("( cd %s ; git remote add declremote %s ; git fetch )"%
                (destpath, git_url))
        cmds.append("( cd %s ; git checkout -b declrev %s )"%
                (destpath, revision))
        return cmds

    def checkout_all(self, checkout_dir):
        cmds = []
        for layername, layer in self.declaration.layers.iteritems():
            assert(layername == layer['name'])
            remote = self.declaration.layer_remotes.get(layer['remote'])
            repo = layer['repo']
            revision = layer['revision']
            git_url = "/".join([remote, repo])
            cmds.extend(self.checkout(checkout_dir, git_url, revision))
        return cmds

# vim:expandtab:ts=4

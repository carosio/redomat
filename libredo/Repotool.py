"""
    libredo/Repotool

    Tool for checking out layers from git.

    (This is not the android repo-tool, but 
    a replacement thereof in the scope of Redomat.)
"""

import time, os, uuid

class Repotool:

    def __init__(self, _declaration, _branch_id=None):
        """
            a builder for yocto using docker to support builds on top of other builds
        """
        self.declaration = _declaration

        self.branch_id = _branch_id
        if not self.branch_id:
            self.branch_id = "%s-%s"%(time.strftime("%F-%H%M%S"), uuid.uuid1())

    def set_declaration(self, decl):
        """
            set declaration
        """
        self.declaration = decl

    def checkout(self, destpath, git_url, revision):
        cmds = []
        cmds.append("""
        if [ ! -d %s ] ; then
            mkdir -pv %s
            cd %s
            [ ! -d .git ] && git init

            git remote add declremote %s
            git fetch declremote
        else
            cd %s
            git fetch declremote
        fi"""%
                (destpath, destpath, destpath, git_url, destpath))
        cmds.append("( cd %s ; git checkout -b declrev%s %s )"%
                (destpath, self.branch_id, revision))
        return cmds

    def checkout_all(self, checkout_dir):
        cmds = []
        print self.declaration.layers

        baselayer = self.declaration.baselayer
        git_dir = "/".join((checkout_dir, baselayer['repo']))
        remote = self.declaration.layer_remotes.get(baselayer['remote'])
        repo = baselayer['repo']
        revision = baselayer['revision']
        git_url = "/".join([remote['baseurl'], repo])
        cmds.extend(self.checkout(git_dir, git_url, revision))

        for layername, layer in self.declaration.layers.iteritems():
            print layer
            print layername
            assert(layername == layer['name'])
            git_dir = "/".join((checkout_dir, baselayer['repo'], layer["name"]))
            remote = self.declaration.layer_remotes.get(layer['remote'])
            repo = layer['repo']
            revision = layer['revision']
            git_url = "/".join([remote['baseurl'], repo])
            cmds.extend(self.checkout(git_dir, git_url, revision))
        return cmds

# vim:expandtab:ts=4

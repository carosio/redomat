
import time, os, uuid

class Repotool:
    """
        libredo/Repotool

        Tool for checking out yocto-layers from git.

        (This is not the android repo-tool, but 
        a replacement thereof in the scope of Redomat.)
    """

    def __init__(self, declaration, syncid=None):
        """
            construct a Repotool instance.
            
            syncid - identifies one specific state of the git repositories
        """

        self._declaration = declaration

        self._syncid = syncid
        if not self._syncid:
            self._syncid = "%s-%s"%(time.strftime("%F-%H%M%S"), uuid.uuid1())

    def set_declaration(self, decl):
        """
            set declaration
        """
        self._declaration = decl

    def set_syncid(self, syncid):
        self._syncid = syncid

    def checkout(self, destpath, git_url, revision):
        cmds = []
        cmds.append("""
        if [ ! -d {dest}/.git ] ; then
            mkdir -pv {dest}
            cd {dest}
            git init
        else
            cd {dest}
        fi

        if [ ! -e .git/refs/heads/branch-{syncid} ]
        then
            git remote add remote-{syncid} {git_url} || true
            echo fetching remote: remote-{syncid} from {git_url}
            git fetch remote-{syncid}
            git branch branch-{syncid} {rev}
            git checkout branch-{syncid}
        else
            echo branch-{syncid} exists, not checking out
        fi

        """.format
                (dest=destpath, git_url=git_url, syncid=self._syncid, rev=revision))
        return cmds

    def checkout_all(self, checkout_dir):
        cmds = []

        baselayer = self._declaration.baselayer
        git_dir = "/".join((checkout_dir, baselayer['repo']))
        remote = self._declaration.layer_remotes.get(baselayer['remote'])
        repo = baselayer['repo']
        revision = baselayer['revision']
        git_url = "".join([remote['baseurl'], repo])
        cmds.extend(self.checkout(git_dir, git_url, revision))

        for layername, layer in self._declaration.layers.iteritems():
            assert(layername == layer['name'])
            git_dir = "/".join((checkout_dir, baselayer['repo'], layer["name"]))
            remote = self._declaration.layer_remotes.get(layer['remote'])
            repo = layer['repo']
            revision = layer['revision']
            git_url = "".join([remote['baseurl'], repo])
            cmds.extend(self.checkout(git_dir, git_url, revision))
        return cmds

# vim:expandtab:ts=4

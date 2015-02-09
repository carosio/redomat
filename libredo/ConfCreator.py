import xml.etree.ElementTree as XML
import os

class ConfCreator:
    def __init__(self, _declaration):
        """
                this will crate a string with a set of commands
                which can be passed using a run command to a docker container
                these commands will set the local.conf and bblayers.conf
        """

        self.declaration = _declaration
        self.bblayers = None
        self.local_conf = None

    def set_decl(self, _decl):
        """
            set declarations to use
        """
        self.declaration = _decl

    def create_bblayers(self):
        """
            function used to define the bblayers.conf for bitbake
        """

        extra_bblayer = ""

        baselayer = self.declaration.baselayer['repo']

        for layername, layer in self.declaration.layers.iteritems():
            extra_bblayer += " /REDO/source/%s/%s"%(baselayer,layer['name'])

        self.bblayers = """
# LAYER_CONF_VERSION is increased each time build/conf/bblayers.conf
# changes incompatibly
LCONF_VERSION = "6"

BBPATH = "${TOPDIR}"
BBFILES ?= ""

BBLAYERS ?= " \
             /REDO/source/poky/meta \
             /REDO/source/poky/meta-yocto \
             %s "
            """%extra_bblayer

    def create_local_conf(self):
        """
            function used to create the bblayers.conf for bitbake
        """

        self.local_conf ="""
DL_DIR = "/REDO/download"
PACKAGE_CLASSES = "package_ipk"
EXTRA_IMAGE_FEATURES = "debug-tweaks"
USER_CLASSES = "buildstats image-mklibs image-prelink"
PATCHRESOLVE = "noop"
BB_DISKMON_DIRS = "\
    STOPTASKS,${TMPDIR},1G,100K \
    STOPTASKS,${DL_DIR},1G,100K \
    STOPTASKS,${SSTATE_DIR},1G,100K \
    ABORT,${TMPDIR},100M,1K \
    ABORT,${DL_DIR},100M,1K \
    ABORT,${SSTATE_DIR},100M,1K"
CONF_VERSION = "1"
PREFERRED_PROVIDER_virtual/erlang ?= "erlang16"
PREFERRED_PROVIDER_virtual/erlang-native ?= "erlang16-native"
%s
        """%self.declaration.extra_local_conf

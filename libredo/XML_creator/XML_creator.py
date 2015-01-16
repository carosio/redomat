import xml.etree.ElementTree as XML
import os

class XML_creator:
    def __init__(self, xml_file=None):
        """
            create xml files that can be used by a variety of tools needed for the redomat
            * repo tool
            * bitbakes bblayer.conf
            * bitbakes local.conf
        """
        # check if all the parameters are passed correctly
        if xml_file is None:
            raise Exception("no xml file name given")

        # check if the passed file exists
        if os.path.exists(xml_file) is False:
            raise Exception(xml_file + "no such file or directory")

        # get the xml root to read from
        self.manifest_root=XML.parse(xml_file).getroot()

    def create_repoxml(self,out_name=None):
        """
            function used to crate a xml file used by the repo tool
            the out put file name must be passed
        """
        # check if all parameters are passed correctly
        if out_name is None:
            raise Exception("no output file name given")

        # if os.path.exists(out_name):
        #     raise Exception(out_name + "file already exists")

        # create a new xml root for the repo.xml
        repo_xml_root = XML.Element("manifest")

        # reading stage declaration has been moved from here to Declaration.py

        # convert the xml root to a xml tree
        tree = XML.ElementTree(repo_xml_root)
        # see if directory exists if not create
        directory=os.path.dirname(os.path.abspath(out_name))
        if not directory:
            os.makedirs(directory)
        # write the xml tree to a file 
        tree.write(out_name, xml_declaration=True)

    def create_bblayers(self, out_name=None):
        """
            function used to crate the bblayers.conf for bitbake
            the out put file name must be passed
        """
        # check if parameters are passed correctly
        if out_name is None:
            raise Exception("no output file name given")

        # if passed file exists delete it
        if os.path.exists(out_name):
            os.remove(out_name)

        # create a file bblayers
        bblayers = open(out_name, 'a')

        # read the default bblayer file and write them in the bblayers.conf
        try:
            bb_tamplate = open('default-configs/default_bblayers', 'r')
        except:
            raise Exception('Could not create bblayers.conf, no default bblayers.conf found.')

        for line in bb_tamplate:
            bblayers.write(line)
        bb_tamplate.close()

        for layer_declaration in self.manifest_root.iter('layer_declaration'):
            for repo_line in layer_declaration.iter().next():
                if repo_line.tag == 'layer':
                    for attribute, value in repo_line.attrib.iteritems():
                        if 'path' in attribute:
                            if value!='poky':
                                bblayers.write("/TP/source/" + value + ' \ \n')

        # add closing '"'
        bblayers.write('"')

        # see if directory exists if not create
        directory=os.path.dirname(os.path.abspath(out_name))
        if not directory:
            os.makedirs(directory)

        # close the file and check if it closes correctly
        bblayers.close()
        if bblayers.closed is False:
            raise Exception("Something went wrong while closing the bblayers file")

    def create_local_conf(self, out_name):
        """
            function used to create the bblayers.conf for bitbake
        """

        # if the passed file exists remove it
        if os.path.exists(out_name):
            os.remove(out_name)

        # write the default file in the local_conf file
        local_conf = open(out_name, 'a')

        try:
            local_tamplate = open('default-configs/default_local', 'r')
        except:
            raise Exception('Could not create local.conf, no default local.conf found')

        for line in local_tamplate:
            local_conf.write(line)
        local_tamplate.close()

        # read all local_conf section from the redomat.xml and write it to a local.conf file
        for local_declaration in self.manifest_root.iter('local_conf'):
            for local_line in local_declaration.iter().next():
                local_conf.write(local_line.tag + '="' + local_line.text + '"\n')

        # see if directory exists if not create
        directory=os.path.dirname(os.path.abspath(out_name))
        if not directory:
            os.makedirs(directory)

        # close the local_conf file and check if it is closed correctly
        local_conf.close()
        if local_conf.closed is False:
            raise Exception("Something went wrong while closing the local.conf")

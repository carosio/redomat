#!/usr/bin/env python3
# coding:utf-8
from __future__ import print_function

'PackagesHTTPD - stream folder content as .tar over http'

__author__ =  'Mathias Gumz <mgumz@tpip.net>'
__license__ = 'MPL2'
__version__ = ''

import sys
import os, os.path
import zipfile, tarfile
try:
    from http.server import SimpleHTTPRequestHandler, HTTPServer
except ImportError: # assume py2
    from BaseHTTPServer import HTTPServer
    from SimpleHTTPServer import SimpleHTTPRequestHandler


class PackagesHTTPD(SimpleHTTPRequestHandler):
    '''
    httpd-server to stream the contents of a given folder as
    /packages.tar if /packages.tar is accessed. otherwise
    it acts just like SimpleHTTPRequestHandler
    '''

    def do_GET(self):
        '''
        /packages.tar  - serve the contents of the folder referenced in
                         self.server.packages as a streamd .tar file
        /packages/*    - serve the files of the folder referenced in
                         self.server.packages (chrooting into it)
        /*             - serve the files of the folder referenced in
                         self.server.chroot

        '''
        if self.path == '/packages.tar':
            self._serve_folder_as_tar(self.server.packages)
            return

        SimpleHTTPRequestHandler.do_GET(self)

    def translate_path(self, path):
        '''
        translates 'path' (the path-part of an uri) to a file-system based
        path. 

        we assume self.server.folder to be the standard chroot-folder. if
        the user tries to access /packages, the self.server.packages folder
        is used as the chroot

        '''

        chroot = self.server.chroot
        if path.find('/packages/') == 0:
            chroot = self.server.packages
            _, path = path.split('/packages/', 1)

        if not os.path.isabs(chroot):
            chroot = os.path.abspath(chroot)

        result = SimpleHTTPRequestHandler.translate_path(self, path)
        _, result = result.split(os.getcwd(), 1)
        if len(result) > 0 and result[0] == '/':
            result = result[1:]

        result = os.path.join(chroot, result)
        return result


    def _serve_folder_as_tar(self, folder):

        tfile = tarfile.open(name='packages.tar', mode='w|', fileobj=self.wfile)

        self.send_response(200)
        self.send_header('Content-type', 'application/x-tar')
        self.end_headers()

        tfile.add(folder, arcname='packages')
        tfile.close()


    def _serve_zip_entry(self, name):
        try:
            entry = self.server.zipfile.open(name, 'r')
        except KeyError:
            self.send_response(404)
            self.end_headers()
            return


    @staticmethod
    def _create_zipfile(zname, zdir):

        zfile = zipfile.ZipFile(zname, 'w', zipfile.ZIP_STORED, True)
        for root, dirs, files in os.walk(zdir):
            for f in files:
                fname = os.path.join(root, f)
                zfile.write(fname)

        zfile.close()



if __name__ == '__main__':

    def main():
        if len(sys.argv) < 4:
            print('usage: %s <port> <chroot> <packages_chroot>' % __file__)
            return

        port, chroot, packages_chroot = int(sys.argv[1]), sys.argv[2], sys.argv[3]

        server_class = HTTPServer
        httpd = server_class(('', port), PackagesHTTPD)
        httpd.chroot = chroot
        httpd.packages = packages_chroot
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        httpd.server_close()

    main()

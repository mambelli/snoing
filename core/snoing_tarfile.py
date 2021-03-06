#!/usr/bin/env python
#
# TarFile
#
# Steal of the tarfile extractall function, this ensures snoing works on python 2.4 systems. When
# this requirement is lost this file should be deleted.
#
# Author P G Jones - 04/09/2012 <p.g.jones@qmul.ac.uk> : First revision
####################################################################################################
import tarfile
import copy
import operator
import os

class TarFile(tarfile.TarFile):
    def extractall(self, path=".", members=None):
        """Extract all members from the archive to the current working
           directory and set owner, modification time and permissions on
           directories afterwards. `path' specifies a different directory
           to extract to. `members' is optional and must be a subset of the
           list returned by getmembers().
        """
        directories = []
        if members is None:
            members = self
        for tarinfo in members:
            if tarinfo.isdir():
                # Extract directories with a safe mode.
                directories.append(tarinfo)
                tarinfo = copy.copy(tarinfo)
                tarinfo.mode = 0700
            self.extract(tarinfo, path)
        # Reverse sort directories.
        directories.sort(key=operator.attrgetter('name'))
        directories.reverse()
        # Set correct owner, mtime and filemode on directories.
        for tarinfo in directories:
            dirpath = os.path.join(path, tarinfo.name)
            try:
                self.chown(tarinfo, dirpath)
                self.utime(tarinfo, dirpath)
                self.chmod(tarinfo, dirpath)
            except ExtractError, e:
                if self.errorlevel > 1:
                    raise
                else:
                    self._dbg(1, "tarfile: %s" % e)

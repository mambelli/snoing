#!/usr/bin/env python
#
# Xm
#
# The xm library is hard to find and requires this special code.
#
# Author P G Jones - 11/07/2012 <p.g.jones@qmul.ac.uk> : First revision
# Author P G Jones - 22/09/2012 <p.g.jones@qmul.ac.uk> : Major refactor of snoing.
####################################################################################################
import systempackage
import system
import os

class Xm(systempackage.SystemPackage):
    """ Package for the Open Motif/Xm library."""
    def __init__(self, system):
        super(Xm, self).__init__("Xm", system, "Install Xm-dev (OpenMotif or motif-devel) on this system.")
    def check_state(self):
        """ Check the Xm state, slightly more involved on macs."""
        if self._system.get_os_type() == system.System.Mac:
            flags = []
            if os.path.exists("/sw/include/Xm"):
                flags = [ "-I%s" % "/sw/include", "-L%s" % "/sw/lib" ]
            elif os.path.exists("/usr/OpenMotif"):
                flags = [ "-I%s" % "/usr/OpenMotif/include", "-L%s" % "/usr/OpenMotif/lib" ]
            self._installed = self._system._test_compile(["Xm/Xm.h"], flags)
        else:
            self._installed = self._system.test_library("Xm", ["Xm/Xm.h"])

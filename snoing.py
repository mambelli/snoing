#!/usr/bin/env python
# Author P G Jones - 12/05/2012 <p.g.jones@qmul.ac.uk> : First revision
# SNO+ package manager
import PackageManager
import os
import inspect
import PackageUtil
import Rat
import TextLogger
import GraphicalLogger
import Util
import sys
import Exceptions

class snoing( PackageManager.PackageManager ):
    """ The package manager for sno+."""
    def __init__( self, options ):
        """ Initialise the snoing package manager."""
        super( snoing, self ).__init__()
        # Build the folders, initialise the logger and check the system
        PackageUtil.kCachePath = Util.BuildDirectory( options.cachePath )
        PackageUtil.kInstallPath = Util.BuildDirectory( options.installPath )
        if PackageUtil.kVerbose:
            self._logger = TextLogger.TextLogger(os.path.join(os.path.dirname(__file__), "snoing.log"),
                                                 os.path.join(PackageUtil.kInstallPath, "README.md"))
        else:
            self._logger = GraphicalLogger.GraphicalLogger(os.path.join(os.path.dirname(__file__), "snoing.log"),
                                                           os.path.join(PackageUtil.kInstallPath, "README.md"))

        Util.CheckSystem(self._logger)
        # Now ready to start
        self._logger.info(options)
        self._logger.info(os.uname()[0])
        self._logger.info(os.uname()[2])
        self._logger.info("Caching to %s, installing to %s" % (PackageUtil.kCachePath, PackageUtil.kInstallPath))
        # Now check the install options are compatible with install directory
        if options.graphical == True and options.grid == True:
            self._logger.error("Cannot be both graphical and grid.")
            self.print_error_message()
        snoingSettingsPath = os.path.join( PackageUtil.kInstallPath, "snoing.pkl" )
        installModes = Util.DeSerialise( snoingSettingsPath )
        # Set the file options if not set
        if installModes is None: 
            installModes = { "Graphical" : options.graphical, "Grid" : options.grid }
            Util.Serialise( snoingSettingsPath, installModes )
        # Check the options match
        if installModes["Graphical"] != options.graphical or installModes["Grid"] != options.grid:
            self._logger.error( "Install mode for install directory does not match that specified. Install path is graphical %s and grid %s" \
                                    % ( options.graphical, options.grid ) )
            self.print_error_message()
        PackageUtil.kGraphical = options.graphical
        PackageUtil.kGrid = options.grid
        return
    def Authenticate( self, options ):
        """ Set the github authentication."""
        # Now set the username or token for the rat packages
        for package in self._Packages:
            if isinstance( self._Packages[package], Rat.RatRelease ):
                self._Packages[package].SetGithubAuthentication( options.username, options.token )
    def print_error_message(self):
        """Print a standard error message if snoing fails."""
        self._logger.error("Snoing has failed, please consult the above error messages or the snoing.log file.")
        self._logger._running = False
        sys.exit(1)


if __name__ == "__main__":
    import optparse
    # Load defaults from file
    defaultFilePath = os.path.join( os.path.dirname( __file__ ), "settings.pkl" )
    defaults = Util.DeSerialise( defaultFilePath )
    if defaults is None: # No defaults
        defaults = { "cache" : "cache", "install" : "install" }
    parser = optparse.OptionParser( usage = "usage: %prog [options] [package]", version="%prog 0.3" )
    parser.add_option( "-c", type="string", dest="cachePath", help="Cache path.", default=defaults["cache"] )
    parser.add_option( "-i", type="string", dest="installPath", help="Install path.", default=defaults["install"] )
    parser.add_option( "-v", action="store_true", dest="verbose", help="Verbose Install?", default=False )
    parser.add_option( "-a", action="store_true", dest="all", help="All packages?" )

    installerGroup = optparse.OptionGroup( parser, "Optional Install modes", "Default snoing action is to install non graphically, i.e. no viewer. This can be changed with the -g option. If installing on the grid use the -x option." )
    installerGroup.add_option( "-g", action="store_true", dest="graphical", help="Graphical install?", default=False )
    installerGroup.add_option( "-x", action="store_true", dest="grid", help="Grid install (NO X11)?", default=False )
    parser.add_option_group( installerGroup )

    actionGroup = optparse.OptionGroup( parser, "Optional Actions", "Default snoing action is to install the specified package, which defaults to rat-dev." )
    actionGroup.add_option( "-q", action="store_true", dest="query", help="Query Package Status?" )
    actionGroup.add_option( "-r", action="store_true", dest="remove", help="Remove the package?" )
    actionGroup.add_option( "-R", action="store_true", dest="forceRemove", help=optparse.SUPPRESS_HELP, default=False )
    actionGroup.add_option( "-d", action="store_true", dest="dependency", help="Install dependencies only?" )
    actionGroup.add_option( "-p", action="store_true", dest="progress", help="Progress/update the package?" )
    parser.add_option_group( actionGroup )

    githubGroup = optparse.OptionGroup( parser, "Github authentication Options", "Supply a username or a github token, not both." )
    githubGroup.add_option( "-u", type="string", dest="username", help="Github username" )
    githubGroup.add_option( "-t", type="string", dest="token", help="Github token" )
    parser.add_option_group( githubGroup )
    (options, args) = parser.parse_args()
    # Save the defaults to file
    defaults["cache"] = options.cachePath
    defaults["install"] = options.installPath
    Util.Serialise( defaultFilePath, defaults )
    # Construct snoing installer
    PackageUtil.kVerbose = options.verbose or options.query
    installer = snoing( options )
    # Default action is to assume installing, check for other actions
    try:
        # First import all register all packages in the versions folder
        installer.RegisterPackagesInDirectory( os.path.join( os.path.dirname( __file__ ), "versions" ) )
        installer.Authenticate( options )
        installer._logger.info("Registering Packages")
        if options.all: # Wish to act on all packages
            if options.query: # Wish to query all packages
                pass # Nothing todo, done automatically
            elif options.remove: # Wish to remove all packages
                shutil.rmtree( PackageUtil.kInstallPath )
            elif options.dependency: # Doesn't make sense
                self._logger.error("Input options don't make sense.")
                installer.print_error_message()
            elif options.progress: # Update all installed
                installer.UpdateAll()
            else: # Wish to install all
                installer.InstallAll()
        else: # Only act on one package
            if options.grid == False: # Default local package
                packageName = "rat-dev"
            else: # Default grid package
                packageName = "rat-3"
            if len(args) != 0:
                packageName = args[0]
            if options.query: # Wish to query the package
                installer._logger.info( "Checking package %s install status" % packageName )
                if installer.CheckPackage( packageName ):
                    installer._logger.package_installed(packageName)
                else:
                    installer._logger.info("Not Installed")
            elif options.remove or options.forceRemove: # Wish to remove the package
                installer.RemovePackage( packageName, options.forceRemove )
            elif options.dependency: # Wish to install only the dependencies
                installer.InstallDependencies( packageName )
            elif options.progress: # Wish to update the package
                installer.UpdatePackage( packageName )
            else: # Wish to install the package
                installer.InstallPackage( packageName )
        installer._logger._running = False
    except Exceptions.InstallException, e:
        print e
        installer.print_error_message()
    except (KeyboardInterrupt, SystemExit):
        installer.print_error_message()

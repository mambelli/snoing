#!/usr/bin/env python
#
# PackageManager
#
# Manages the packages on the system, installs, removes and updates.
#
# Author P G Jones - 12/05/2012 <p.g.jones@qmul.ac.uk> : First revision
# Author P G Jones - 25/07/2012 <p.g.jones@qmul.ac.uk> : Refactor for multiple dependency versions
# Author P G Jones - 23/06/2012 <p.g.jones@qmul.ac.uk> : Major refactor of snoing.
####################################################################################################
import package
import localpackage
import inspect
import snoing_exceptions
import types
import os
import rat
import rattools
import xsnoed

class PackageManager(object):
    """ Manages a dictionary of packages for installation on the system."""
    def __init__(self, system, logger):
        """ Initialise with the system and a logger."""
        self._system = system
        self._logger = logger
        self._packages = {} # Dict of packages keyed by name
    def register_package(self, package):
        """ Register an instance of a package."""
        instance = package(self._system)
        self._logger.package_registered(instance.get_name())
        instance.check_state()
        if isinstance(instance, localpackage.LocalPackage) and instance.is_downloaded():
            self._logger.package_downloaded(instance.get_name())
        if instance.is_installed():
            self._logger.package_installed(instance.get_name())
        self._packages[instance.get_name()] = instance
    def register_packages(self, path):
        """ Register all the packages in the path. """
        for module in os.listdir(path):
            if module[-3:] != '.py':
                continue
            package_set = __import__(module[:-3], locals(), globals())
            for name, obj in inspect.getmembers(package_set):
                if inspect.isclass(obj):
                    self.register_package(obj)
####################################################################################################
    # Functions that act on single packages
    def check_installed(self, package_name):
        """ Check the install status of the package, package_name. Return True if installed, else 
        False.
        """
        self._check_package(package_name)
        return self._packages[package_name].is_installed()
    def install_package(self, package_name):
        """ Install a package, installing all it's dependencies first."""
        if self.check_installed(package_name):
            return
        package = self._packages[package_name]
        self._check_mode(package)
        if not isinstance(package, localpackage.LocalPackage):
            raise snoing_exceptions.PackageException("Package cannot be installed by snoing. " + package.get_help_text(), package_name)
        dependencies = self._install_dependencies(package)
        package.set_dependency_paths(dependencies)
        try:
            self._logger.set_state("Downloading", package_name)
            package.download()
            self._logger.package_downloaded(package_name)
            self._logger.set_state("Installing", package_name)
            package.install()
            self._logger.package_installed(package_name)
        except snoing_exceptions.SystemException, e:
            self._logger.error(e.args[0])
            self._logger.detail(e.Details)
            raise snoing_exceptions.PackageException("Installation fail", package_name)
        return package.get_install_path()
    def install_package_dependencies(self, package_name):
        """ Install the dependencies for named package."""
        self._check_package(package_name) # Check package_name exists...
        self._install_dependencies(self._packages[package_name])
        return
    def update_package(self, package_name):
        """ Update a package and all packages that depend on it."""
        self._check_package(package_name)
        package = self._packages[package_name]
        self._check_mode(package)
        if not isinstance(package, localpackage.LocalPackage):
            raise snoing_exceptions.PackageException("Package cannot be updated by snoing. " + package.get_help_text(), package_name)
        if package.is_updated(): # Nothing todo if already updated
            return
        dependencies = self._install_dependencies( package )
        package.set_dependency_paths(dependencies)
        try:
            self._logger.set_state("Updating", package_name)
            package.update()
        except snoing_exceptions.SystemException, e:
            self._logger.error(e.args[0])
            self._logger.detail(e.Details)
            raise snoing_exceptions.PackageException("Installation fail", package_name)
        for dependent_name in self._package_dependents(package_name):
            if self.check_installed(dependent_name): #Best update this package as well
                self.update_package(dependent_name)
    def remove_package(self, package_name, force=False):
        """ Remove a package, don't remove if force is False and packages depend on package_name."""
        package = self._packages[package_name]
        self._logger.set_state("Removing", package_name)
        if force:
            package.remove()
        else:
            if not self.check_installed(package_name):
                raise snoing_exceptions.PackageException("Cannot remove, not installed.", package_name)
            if not force:
                for dependent_name in self._package_dependents(package_name):
                    if self.check_installed(dependent_name):
                        raise snoing_exceptions.PackageException("Cannot remove as %s depends on it." % \
                                                                     dependent_name, package_name)
                # If get here then package can be deleted
                package.remove()
####################################################################################################
    # Functions that act on all packages
    def check_all_installed(self):
        """ Check the install status of all the packages."""
        for package_name in self._packages.iterkeys():
            self.check_installed(package_name)
    def install_all(self):
        """ Install all the packages."""
        for package_name in self._packages.iterkeys():
            self.install_package(package_name)
    def update_all(self):
        """ Update all the installed packages."""
        for package_name in self._packages.iterkeys():
            self.update_package(package_name)
    def authenticate(self, username, token):
        """ Pass the authentication information over to the packages that need it."""
        for package in self._packages.itervalues():
            if isinstance(package, rat.RatRelease) or isinstance(package, rattools.RatToolsRelease) or \
                    isinstance(package, xsnoed.XsnoedRelease):
                package.authenticate(username, token)
####################################################################################################
    # Internal functions
    def _check_package(self, package_name):
        """ Check a package with package_name exists."""
        if not package_name in self._packages.iterkeys():
            raise snoing_exceptions.PackageException("Package doesn't exist.", package_name)
        self._packages[package_name].check_state()
    def _check_mode(self, package):
        """ Check the package install mode is compatible with the system."""
        if isinstance(package, localpackage.LocalPackage):
            if package.get_install_mode() is not None and \
                    package.get_install_mode() != self._system.get_install_mode():
                raise snoing_exceptions.PackageException(("Package install mode is incompatible with the "
                                                          "system"),
                                                         package.get_name())
    def install_dependencies(self, package_name):
        """ Install the dependencies (if required)"""
        self._install_dependencies(self._packages[package_name])
    def _install_dependencies(self, package):
        """ Install the dependencies (if required)."""
        dependency_paths = {} # Dictionary of dependency paths
        for dependency in package.get_dependencies():
            # First need to check if dependency is installed, if dependency is a list should check
            # at least one is installed.
            if isinstance(dependency, types.ListType): # Multiple optional dependencies
                for opt_dependency in dependency:
                    if self.check_installed(opt_dependency): # Great found one!
                        dependency_paths[opt_dependency] = \
                            self._packages[opt_dependency].get_install_path()
                        break
                else: # No optional dependency is installed, thus install the first
                    dependency_paths[dependency[0]] = self.install_package(dependency[0])
            else: # Just a single dependency
                if self.check_installed(dependency):
                    dependency_paths[dependency] = self._packages[dependency].get_install_path()
                else: # Must install it
                    dependency_paths[dependency] = self.install_package(dependency)
        # Massive success, return dict of install paths
        return dependency_paths
    def _package_dependents(self, package_name):
        """ Yield the name of any packages that are dependent on package_name."""
        # Now update all packages that depend on this one
        for test_name, test_package in self._packages.iteritems():
            if not isinstance(test_package, localpackage.LocalPackage): # Nothing todo
                continue
            # If test package has this package as a dependency then update the test package
            for dependency in test_package.get_dependencies():
                if isinstance(dependency, types.ListType): # deal with optional dependencies
                    if package_name in dependency:
                        yield test_name
                elif dependency == package_name:
                    yield test_name

#!/usr/bin/env python
# Author P G Jones - 24/08/2012 <p.g.jones@qmul.ac.uk> : First revision
# Graphical logger class, this displays the information in a cool way.
import Logger
import threading
import curses
import snoflake
import random
from time import sleep

class GraphicalLogger(Logger.Logger, threading.Thread):
    """ Update with pacakages state change information, and convey information to the
    screen in different colours and movement :).
    """

    def __init__(self, local, install):
        """ Call the base class init and take control of the terminal."""
        super(GraphicalLogger, self).__init__(local, install)
        threading.Thread.__init__(self)
        self._packages = {} # Dict between package name and state (0 registered, 1 downloaded, 2 installed)
        self._screen = curses.initscr()
        self._snoflakes = [snoflake.SnoFlake(self._screen) for i in range( 0, 60 )] # Available snoflakes
        curses.curs_set(0) # No blinking curser
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
        self._state = "Initialising"
        self._errors = ""
        self._lock = threading.Lock()
        self.draw_splash()
        sleep(2)
        self._running = True
        self.start()

    def end(self):
        """ Close the screen and cleanup."""
        self._running = False
        self.join()
        curses.endwin()
        print self._errors

    def package_registered(self, package_name):
        """ Notify that a package has been registered."""
        super(GraphicalLogger, self).package_registered(package_name)
        self._lock.acquire()
        self._packages[package_name] = 0
        self._lock.release()

    def package_downloaded(self, package_name):
        """ Notify that a package has been downloaded."""
        super(GraphicalLogger, self).package_downloaded(package_name)
        self._lock.acquire()
        self._packages[package_name] = 1
        self._lock.release()

    def package_installed(self, package_name):
        """ Notify that a package has been installed."""
        super(GraphicalLogger, self).package_installed(package_name)
        self._lock.acquire()
        self._packages[package_name] = 2
        self._lock.release()
        x = int(random.random() * (self._screen.getmaxyx()[1] - 2)) + 1
        for snoflake in self._snoflakes:
            if not snoflake.active():
                snoflake.begin(1, x, package_name)
                break

    def package_removed(self, package_name):
        """ Notify that a package has been removed."""
        super(GraphicalLogger, self).package_removed(package_name)
        self._lock.acquire()
        self._packages[package_name] = 0
        self._lock.release()

    def package_updated(self, package_name):
        """ Notify that a package has been updated."""
        super(GraphicalLogger, self).package_updated(package_name)

    def set_state(self, state):
        """ Notify the current state."""
        super(GraphicalLogger, self).set_state(state)
        self._state = state

    def info(self, info_message):
        """ Output some information."""
        super(GraphicalLogger, self).info(info_message)

    def error(self, error_message):
        """ Notify that an error has occurred."""
        self._errors += error_message + "\n"
        super(GraphicalLogger, self).error(error_message)

    # Graphical aspects
    def draw_splash(self):
        """ Draw the splash screen."""
        window_size = self._screen.getmaxyx() # In y,x
        self._screen.clear() 
        snoing_str = "snoing 2012"
        self._screen.addstr(window_size[0] / 2, (window_size[1] - len(snoing_str)) / 2, snoing_str)
        author_str = "P Jones M Mottram O Wasalski"
        self._screen.addstr(window_size[0] - 1, window_size[1] - len(author_str) - 1, author_str)
        self._screen.refresh()

    def run(self):
        """ The main loop."""
        while self._running:
            sleep(1.0) # Sleep for 1 second (refresh rate)
            window_size = self._screen.getmaxyx() # In y,x
            topCursor = [1,0] # In y,x, first row is state
            bottomCursor = [window_size[0] - 1,0] # In y,x
            self._screen.clear() 
            # Draw the package information
            self._lock.acquire()
            for package in self._packages:
                if(self._packages[package] == 0 or self._packages[package] == 1): # Draw at top
                    if topCursor[1] + len(package) + 1 >= window_size[1]: # Word wrap
                        topCursor[1] = 0
                        topCursor[0] += 1
                    self._screen.addstr(topCursor[0], topCursor[1], package + " ", curses.color_pair(self._packages[package]))
                    topCursor[1] += len(package) + 1
                elif(self._packages[package] == 2): # Draw at bottom
                    if bottomCursor[1] + len(package) + 1 >= window_size[1]: # Word wrap
                        bottomCursor[1] = 0
                        bottomCursor[0] -= 1
                    self._screen.addstr(bottomCursor[0], bottomCursor[1], package, curses.color_pair(self._packages[package]))
                    bottomCursor[1] += len(package) + 1
            self._lock.release()
            # Draw the snoflake information
            for snoflake in self._snoflakes:
                if snoflake.active():
                    snoflake.update(bottomCursor[0]) # Moves and renders
                elif( random.random() > 0.9 ): # Create it?
                    x = int(random.random() * (window_size[1] - 2)) + 1
                    snoflake.begin(topCursor[0] + 1, x, "*")
            # Draw the state information
            self._screen.addstr(0, (window_size[1] - len(self._state)) / 2, self._state, curses.color_pair(3))
            self._screen.refresh()

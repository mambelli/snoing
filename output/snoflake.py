#!/usr/bin/env python
# Author P G Jones - 24/08/2012 <p.g.jones@qmul.ac.uk> : First revision
# Displays a falling snoflake

class SnoFlake(object):
    """ Falls down the screen."""

    def __init__(self, screen):
        self._active = False
        self._counter = 0
        self._y = 0
        self._x = 0
        self._screen = screen
        self._str = "*"

    def begin(self, y, x, text):
        """ Initialise the snoflake."""
        self._y = y
        self._x = x
        self._str = text
        self._active = True

    def active(self):
        """ Is the snoflake active?"""
        return self._active

    def update(self, maxY):
        """ Update the snoflake position, use the counter to float from
        left to right.
        """
        if self._counter % 4 == 0:
            self._screen.move( self._y, self._x )
        elif self._counter % 4 == 1:
            self._screen.move( self._y, self._x + 1 )
        elif self._counter % 4 == 2:
            self._screen.move( self._y, self._x )
        elif self._counter % 4 == 3:
            self._screen.move( self._y, self._x - 1 )
        self._y += 1
        self._counter += 1
        if self._y > maxY:
            self._active = False
            self._counter = 0
            self._y = 0
        else:
            self._screen.addstr( self._str )

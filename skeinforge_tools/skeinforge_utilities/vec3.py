"""
Vec3 is a three dimensional vector class.

#Class vec3 is deprecated, please use Vec3 instead.

Below are examples of Vec3 use.

>>> from vec3 import Vec3
>>> origin = Vec3()
>>> origin
0.0, 0.0, 0.0
>>> pythagoras = Vec3( 3, 4, 0 )
>>> pythagoras
3.0, 4.0, 0.0
>>> pythagoras.length()
5.0
>>> pythagoras.length2()
25
>>> triplePythagoras = pythagoras.times( 3.0 )
>>> triplePythagoras
9.0, 12.0, 0.0
>>> plane = pythagoras.dropAxis( 2 )
>>> plane
(3+4j)
"""

from __future__ import absolute_import
try:
	import psyco
	psyco.full()
except:
	pass
#Init has to be imported first because it has code to workaround the python bug where relative imports don't work if the module is imported as a main module.
import __init__

import math


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__credits__ = 'Nophead <http://forums.reprap.org/profile.php?12,28>\nArt of Illusion <http://www.artofillusion.org/>'
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


class Vec3:
    "A three dimensional vector class."
    __slots__ = [ 'x', 'y', 'z' ]

    def __init__( self, x = 0.0, y = 0.0, z = 0.0 ):
        self.x = x
        self.y = y
        self.z = z

    def __eq__( self, another ):
        "Determine whether this vector is identical to another one."
        return self.equals( another )

    def __hash__( self ):
        "Determine whether this vector is identical to another one."
        return self.__repr__().__hash__()

    def __ne__( self, another ):
        "Determine whether this vector is not identical to another one."
        return not self.__eq__( another )

    def __repr__( self ):
        "Get the string representation of this Vec3."
        return '%s, %s, %s' % (self.x, self.y, self.z)

    def add( self, another ):
        "Add another Vec3 to this one."
        self.x += another.x
        self.y += another.y
        self.z += another.z

    def distance( self, another ):
        """Get the Euclidean distance between this vector and another one."""
        return math.sqrt( self.distance2( another ) )

    def distanceXYPlane( self, another ):
        """Get the Euclidean distance between this vector and another one in the xy plane."""
        return math.sqrt( self.distance2XYPlane( another ) )

    def distance2( self, another ):
        """Get the square of the Euclidean distance between this vector and another one."""
        separationX = self.x - another.x
        separationY = self.y - another.y
        separationZ = self.z - another.z
        return separationX * separationX + separationY * separationY + separationZ * separationZ

    def distance2XYPlane( self, another ):
        """Get the square of the Euclidean distance between this vector and another one in the xy plane."""
        separationX = self.x - another.x
        separationY = self.y - another.y
        return separationX * separationX + separationY * separationY

    def dot( self, another ):
        "Calculate the dot product of this vector with another one."
        return self.x * another.x + self.y * another.y + self.z * another.z

    def dropAxis( self, which ):
        """Get a complex by removing one axis of this one.

        Keyword arguments:
        which -- the axis to drop (0=X, 1=Y, 2=Z)"""
        if which == 0:
            return complex( self.y, self.z )
        if which == 1:
            return complex( self.x, self.z )
        if which == 2:
            return complex( self.x, self.y )

    def equals( self, another ):
        "Determine whether this vector is identical to another one."
        if another == None:
            return False
        if self.x != another.x:
            return False
        if self.y != another.y:
            return False
        return self.z == another.z

    def getFromVec3( self, another ):
        """Get a new Vec3 identical to another one."""
        self.setToVec3( another )
        return self

    def getFromXYZ( self, x, y, z ):
        """Get a new Vec3 with the specified x, y, and z components."""
        self.setToXYZ( x, y, z )
        return self

    def length( self ):
        """Get the length of the Vec3."""
        return math.sqrt( self.length2() )

    def lengthXYPlane( self ):
        """Get the length of the Vec3."""
        return math.sqrt( self.length2XYPlane() )

    def length2( self ):
        """Get the square of the length of the Vec3."""
        return self.x * self.x + self.y * self.y + self.z * self.z

    def length2XYPlane( self ):
        """Get the square of the length of the Vec3 in the xy plane."""
        return self.x * self.x + self.y * self.y

    def minus( self, subtractVec3 ):
        """Get the difference between the Vec3 and another one.

        Keyword arguments:
        subtractVec3 -- Vec3 which will be subtracted from the original"""
        return Vec3( self.x - subtractVec3.x, self.y - subtractVec3.y, self.z - subtractVec3.z )

    def multiply( self, another ):
        "Multiply each component of this vector by the corresponding component of another vector."
        self.x *= another.x
        self.y *= another.y
        self.z *= another.z

    def normalize( self ):
        "Scale each component of this Vec3 so that it has a length of 1. If this Vec3 has a length of 0, this method has no effect."
        length = self.length()
        if length == 0.0:
            return
        self.scale( 1.0 / length )

    def plus( self, plusVec3 ):
        """Get the sum of this Vec3 and another one.

        Keyword arguments:
        plusVec3 -- Vec3 which will be added to the original"""
        return Vec3( self.x + plusVec3.x, self.y + plusVec3.y, self.z + plusVec3.z )

    def scale( self, multiplier ):
        "Scale each component of this Vec3 by a multiplier."
        self.x *= multiplier
        self.y *= multiplier
        self.z *= multiplier

    def setToVec3( self, another ):
        "Set this Vec3 to be identical to another one."
        self.x = another.x
        self.y = another.y
        self.z = another.z

    def setToXYZ( self, x, y, z ):
        "Set the x, y, and z components of this Vec3."
        self.x = x
        self.y = y
        self.z = z

    def subtract( self, another ):
        "Subtract another Vec3 from this one."
        self.x -= another.x
        self.y -= another.y
        self.z -= another.z

    def times( self, multiplier ):
        "Get a new Vec3 by multiplying each component of this one by a multiplier."
        return Vec3().getFromXYZ( self.x * multiplier, self.y * multiplier, self.z * multiplier )

#class vec3( Vec3 ):
#    "A three dimensional vector class which completely inherits from Vec3 and is deprecated, please use Vec3 instead."
#    def __init__( self, x = 0.0, y = 0.0, z = 0.0 ):
#        self.x = x
#        self.y = y
#        self.z = z

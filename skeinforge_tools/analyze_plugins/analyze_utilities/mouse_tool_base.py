"""
Display line is a mouse tool to display the line index of the line clicked, counting from one, and the line itself.

"""

from __future__ import absolute_import
#Init has to be imported first because it has code to workaround the python bug where relative imports don't work if the module is imported as a main module.
import __init__


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


class MouseToolBase:
	"The mouse tool base class, which does nothing."
	def __init__( self ):
		"Initialize."
		self.items = []

	def button1( self, event ):
		"The left button was clicked, <Button-1> function."
		pass

	def buttonRelease1( self, event ):
		"The left button was released, <ButtonRelease-1> function."
		pass

	def destroyEverything( self ):
		"Destroy items."
		self.destroyItems()

	def destroyItems( self ):
		"Destroy items."
		for item in self.items:
			self.canvas.delete( item )
		self.items = []

	def getReset( self, window ):
		"Reset the mouse tool to default."
		self.setCanvasItems( window.canvas )
		return self

	def getTagsGivenXY( self, x, y ):
		"Get the tag for the x and y."
		tags = self.canvas.itemcget( self.canvas.find_closest( x, y ), 'tags' )
		currentEnd = ' current'
		if tags.find( currentEnd ) != - 1:
			return tags[ : - len( currentEnd ) ]
		return tags

	def motion( self, event ):
		"The mouse moved, <Motion> function."
		pass

	def setCanvasItems( self, canvas ):
		"Set the canvas and items."
		self.canvas = canvas

"""
Display line is a mouse tool to display the line index of the line clicked, counting from one, and the line itself.

"""

from __future__ import absolute_import
#Init has to be imported first because it has code to workaround the python bug where relative imports don't work if the module is imported as a main module.
import __init__

from skeinforge_tools.analyze_plugins.analyze_utilities.mouse_tool_base import MouseToolBase
from skeinforge_tools.skeinforge_utilities import preferences


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


def getNewMouseTool():
	"Get a new mouse tool."
	return ZoomIn()


class ZoomIn( MouseToolBase ):
	"The zoom in mouse tool."
	def button1( self, event, shift = False ):
		"Print line text and connection line."
		scaleSetting = self.window.repository.scale
		scaleSetting.value *= self.getMultiplier()
		delta = complex( float( event.x ) / float( self.window.screenSize.real ), float( event.y ) / float( self.window.screenSize.imag ) ) - self.window.canvasScreenCenterComplex
		delta *= 1.0 - 1.0 / self.getMultiplier()
		scrollPaneCenter = self.window.getScrollPaneCenter() + delta
		self.window.updateNewDestroyOld( scrollPaneCenter )

	def click( self, event = None ):
		"Set the window mouse tool to this."
		self.window.destroyMouseToolRaiseMouseButtons()
		self.window.mouseTool = self
		self.mouseButton[ 'relief' ] = preferences.Tkinter.SUNKEN

	def getReset( self, window ):
		"Reset the mouse tool to default."
		self.setCanvasItems( window.canvas )
		self.mouseButton = None
		self.window = window
		return self

	def getMultiplier( self ):
		"Get the scale multiplier."
		return 2.0

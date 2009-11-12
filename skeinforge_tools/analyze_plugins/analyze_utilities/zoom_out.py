"""
Display line is a mouse tool to display the line index of the line clicked, counting from one, and the line itself.

"""

from __future__ import absolute_import
#Init has to be imported first because it has code to workaround the python bug where relative imports don't work if the module is imported as a main module.
import __init__

from skeinforge_tools.analyze_plugins.analyze_utilities import zoom_in
from skeinforge_tools.skeinforge_utilities import preferences


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


def getNewMouseTool():
	"Get a new mouse tool."
	return ZoomOut()


class ZoomOut( zoom_in.ZoomIn ):
	"The zoom out mouse tool."
	def getMultiplier( self ):
		"Get the scale multiplier."
		return 0.5

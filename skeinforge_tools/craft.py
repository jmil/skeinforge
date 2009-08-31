"""
Craft is a script to access the plugins which craft a gcode file.

An explanation of the gcodes is at:
http://reprap.org/bin/view/Main/Arduino_GCode_Interpreter

A gode example is at:
http://forums.reprap.org/file.php?12,file=565

"""

from __future__ import absolute_import
#Init has to be imported first because it has code to workaround the python bug where relative imports don't work if the module is imported as a main module.
import __init__

from skeinforge_tools.skeinforge_utilities import consecution
from skeinforge_tools.skeinforge_utilities import gcodec
from skeinforge_tools.skeinforge_utilities import interpret
from skeinforge_tools.skeinforge_utilities import preferences
from skeinforge_tools import polyfile
import cStringIO
import os
import sys


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


def getCraftPluginFilenames():
	"Get craft plugin fileNames."
	return gcodec.getPluginFilenames( 'craft_plugins', __file__ )

def writeOutput( fileName = '' ):
	"Craft a gcode file.  If no fileName is specified, comment the first gcode file in this folder that is not modified."
	pluginModule = consecution.getLastModule()
	if pluginModule != None:
		pluginModule.writeOutput( fileName )


class CraftPreferences:
	"A class to handle the craft preferences."
	def __init__( self ):
		"Set the default preferences, execute title & preferences fileName."
		#Set the default preferences.
		self.archive = []
		self.craftLabel = preferences.LabelDisplay().getFromName( 'Open Preferences: ' )
		self.archive.append( self.craftLabel )
		importantFilenames = [ 'carve', 'raft', 'speed' ]
		self.archive += preferences.getDisplayToolButtons( 'craft_plugins', importantFilenames, __file__, getCraftPluginFilenames(), [] )
		self.fileNameInput = preferences.Filename().getFromFilename( interpret.getGNUTranslatorGcodeFileTypeTuples(), 'Open File to be Crafted', '' )
		self.archive.append( self.fileNameInput )
		#Create the archive, title of the execute button, title of the dialog & preferences fileName.
		self.executeTitle = 'Craft'
		self.saveTitle = None
		preferences.setHelpPreferencesFileNameTitleWindowPosition( self, 'skeinforge_tools.craft.html' )
		self.windowPositionPreferences.value = '400+0'

	def execute( self ):
		"Craft button has been clicked."
		fileNames = polyfile.getFileOrDirectoryTypesUnmodifiedGcode( self.fileNameInput.value, [], self.fileNameInput.wasCancelled )
		for fileName in fileNames:
			writeOutput( fileName )


def main( hashtable = None ):
	"Display the craft dialog."
	if len( sys.argv ) > 1:
		writeOutput( ' '.join( sys.argv[ 1 : ] ) )
	else:
		preferences.displayDialog( CraftPreferences() )

if __name__ == "__main__":
	main()

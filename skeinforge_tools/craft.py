"""
Craft is a script to access the plugins which craft a gcode file.

The plugin buttons which are commonly used are bolded and the ones which are rarely used have normal font weight.

"""

from __future__ import absolute_import
#Init has to be imported first because it has code to workaround the python bug where relative imports don't work if the module is imported as a main module.
import __init__

from skeinforge_tools.skeinforge_utilities import consecution
from skeinforge_tools.skeinforge_utilities import gcodec
from skeinforge_tools.skeinforge_utilities import interpret
from skeinforge_tools.skeinforge_utilities import preferences
from skeinforge_tools import polyfile
import sys


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


def getCraftPluginFilenames():
	"Get craft plugin fileNames."
	craftSequence = consecution.getReadCraftSequence()
	craftSequence.sort()
	return craftSequence

def getPreferencesConstructor():
	"Get the preferences constructor."
	return CraftPreferences()

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
		importantFilenames = [ 'carve', 'chop', 'feed', 'flow', 'lift', 'raft', 'speed' ]
		self.archive += preferences.getDisplayToolButtons( gcodec.getAbsoluteFolderPath( __file__, 'craft_plugins' ), importantFilenames, getCraftPluginFilenames(), [] )
		self.fileNameInput = preferences.Filename().getFromFilename( interpret.getGNUTranslatorGcodeFileTypeTuples(), 'Open File to be Crafted', '' )
		self.archive.append( self.fileNameInput )
		#Create the archive, title of the execute button, title of the dialog & preferences fileName.
		self.executeTitle = 'Craft'
		self.saveCloseTitle = 'Save and Close'
		preferences.setHelpPreferencesFileNameTitleWindowPosition( self, 'skeinforge_tools.craft.html' )

	def execute( self ):
		"Craft button has been clicked."
		fileNames = polyfile.getFileOrDirectoryTypesUnmodifiedGcode( self.fileNameInput.value, [], self.fileNameInput.wasCancelled )
		for fileName in fileNames:
			writeOutput( fileName )


def main():
	"Display the craft dialog."
	if len( sys.argv ) > 1:
		writeOutput( ' '.join( sys.argv[ 1 : ] ) )
	else:
		preferences.startMainLoopFromConstructor( getPreferencesConstructor() )

if __name__ == "__main__":
	main()

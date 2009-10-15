"""
Analyze is a script to access the plugins which analyze a gcode file.

The plugin buttons which are commonly used are bolded and the ones which are rarely used have normal font weight.

An explanation of the gcodes is at:
http://reprap.org/bin/view/Main/Arduino_GCode_Interpreter

A gode example is at:
http://forums.reprap.org/file.php?12,file=565

"""

from __future__ import absolute_import
#Init has to be imported first because it has code to workaround the python bug where relative imports don't work if the module is imported as a main module.
import __init__

from skeinforge_tools.skeinforge_utilities import gcodec
from skeinforge_tools.skeinforge_utilities import preferences
from skeinforge_tools import polyfile
import os
import sys


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


def getAnalyzePluginFilenames():
	"Get analyze plugin fileNames."
	return gcodec.getPluginFilenamesFromDirectoryPath( gcodec.getAbsoluteFolderPath( __file__, 'analyze_plugins' ) )

def getPreferencesConstructor():
	"Get the preferences constructor."
	return AnalyzePreferences()

def writeOutput( fileName = '', gcodeText = '' ):
	"Analyze a gcode file.  If no fileName is specified, comment the first gcode file in this folder that is not modified."
	if fileName == '':
		unmodified = gcodec.getUncommentedGcodeFiles()
		if len( unmodified ) == 0:
			print( "There is no gcode file in this folder that is not a comment file." )
			return
		fileName = unmodified[ 0 ]
	if gcodeText == '':
		gcodeText = gcodec.getFileText( fileName )
	analyzePluginFilenames = getAnalyzePluginFilenames()
	for analyzePluginFilename in analyzePluginFilenames:
		pluginModule = gcodec.getModule( analyzePluginFilename, 'analyze_plugins', __file__ )
		if pluginModule != None:
			pluginModule.writeOutput( fileName, gcodeText )


class AnalyzePreferences:
	"A class to handle the analyze preferences."
	def __init__( self ):
		"Set the default preferences, execute title & preferences fileName."
		#Set the default preferences.
		self.archive = []
		self.analyzeLabel = preferences.LabelDisplay().getFromName( 'Open Preferences: ' )
		self.archive.append( self.analyzeLabel )
		importantFilenames = [ 'behold', 'skeinview', 'statistic' ]
		self.archive += preferences.getDisplayToolButtons( gcodec.getAbsoluteFolderPath( __file__, 'analyze_plugins' ), importantFilenames, getAnalyzePluginFilenames(), [] )
		self.fileNameInput = preferences.Filename().getFromFilename( [ ( 'Gcode text files', '*.gcode' ) ], 'Open File to be Analyzed', '' )
		self.archive.append( self.fileNameInput )
		#Create the archive, title of the execute button, title of the dialog & preferences fileName.
		self.executeTitle = 'Analyze'
		self.saveCloseTitle = 'Save and Close'
		preferences.setHelpPreferencesFileNameTitleWindowPosition( self, 'skeinforge_tools.analyze.html' )

	def execute( self ):
		"Analyze button has been clicked."
		fileNames = polyfile.getFileOrDirectoryTypesUnmodifiedGcode( self.fileNameInput.value, [], self.fileNameInput.wasCancelled )
		for fileName in fileNames:
			writeOutput( fileName )


def main():
	"Display the analyze dialog."
	if len( sys.argv ) > 1:
		writeOutput( ' '.join( sys.argv[ 1 : ] ) )
	else:
		preferences.startMainLoopFromConstructor( getPreferencesConstructor() )

if __name__ == "__main__":
	main()

"""
Analyze is a script to access the plugins which analyze a gcode file.

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
import cStringIO
import os
import sys


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


def getAnalyzePluginFilenames():
	"Get analyze plugin filenames."
	return gcodec.getPluginFilenames( 'analyze_plugins', __file__ )

def writeOutput( filename = '', gcodeText = '' ):
	"Analyze a gcode file.  If no filename is specified, comment the first gcode file in this folder that is not modified."
	if filename == '':
		unmodified = gcodec.getUncommentedGcodeFiles()
		if len( unmodified ) == 0:
			print( "There is no gcode file in this folder that is not a comment file." )
			return
		filename = unmodified[ 0 ]
	if gcodeText == '':
		gcodeText = gcodec.getFileText( filename )
	analyzePluginFilenames = getAnalyzePluginFilenames()
	for analyzePluginFilename in analyzePluginFilenames:
		pluginModule = gcodec.getModule( analyzePluginFilename, 'analyze_plugins', __file__ )
		if pluginModule != None:
			pluginModule.writeOutput( filename, gcodeText )


class AnalyzePreferences:
	"A class to handle the analyze preferences."
	def __init__( self ):
		"Set the default preferences, execute title & preferences filename."
		#Set the default preferences.
		self.archive = []
		self.analyzeLabel = preferences.LabelDisplay().getFromName( 'Open Preferences: ' )
		self.archive.append( self.analyzeLabel )
		analyzePluginFilenames = getAnalyzePluginFilenames()
		self.analyzePlugins = []
		for analyzePluginFilename in analyzePluginFilenames:
			analyzePlugin = preferences.DisplayToolButton().getFromFolderName( 'analyze_plugins', __file__, analyzePluginFilename )
			self.analyzePlugins.append( analyzePlugin )
#		self.analyzePlugins.sort( key = preferences.RadioCapitalized.getLowerName )
		self.archive += self.analyzePlugins
		self.filenameInput = preferences.Filename().getFromFilename( [ ( 'Gcode text files', '*.gcode' ) ], 'Open File to be Analyzed', '' )
		self.archive.append( self.filenameInput )
		#Create the archive, title of the execute button, title of the dialog & preferences filename.
		self.executeTitle = 'Analyze'
		self.filenamePreferences = preferences.getPreferencesFilePath( 'analyze.csv' )
		self.filenameHelp = 'skeinforge_tools.analyze.html'
		self.saveTitle = None
		self.title = 'Analyze Preferences'

	def execute( self ):
		"Analyze button has been clicked."
		filenames = polyfile.getFileOrDirectoryTypesUnmodifiedGcode( self.filenameInput.value, [], self.filenameInput.wasCancelled )
		for filename in filenames:
			writeOutput( filename )


def main( hashtable = None ):
	"Display the analyze dialog."
	if len( sys.argv ) > 1:
		writeOutput( ' '.join( sys.argv[ 1 : ] ) )
	else:
		preferences.displayDialog( AnalyzePreferences() )

if __name__ == "__main__":
	main()

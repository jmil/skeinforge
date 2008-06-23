"""
Analyze is a script to analyze and comment a gcode file.

To run analyze, install python 2.x on your machine, which is avaliable from http://www.python.org/download/

Then in the folder which analyze is in, type 'python' in a shell to run the python interpreter.  Finally type
'from analyze import *' to import this program.
To get documentation for this program, open a shell in the fill.py directory, then type 'pydoc fill.py'.


This example analyzes and comments the gcode file Hollow Square.gcode.  This example is run in a terminal in the folder which contains Hollow Square.gcode and analyze.py.

>>> import fillet
Fillet has been imported.
The gcode files in this directory that are not already beveled or filleted are the following:
['Hollow Square.gcode']


>>> fillet.arcPoint()
File Hollow Square.gcode is being filleted into arc points.
( GCode generated by March 29,2007 Skeinforge )
( Extruder Initialization )
..
many lines of gcode
..
The arc point file is saved as Hollow Square_arc_point.gcode


>>> fillet.arcPointFile("Hollow Square.gcode")
File Hollow Square.gcode is being filleted into arc points.
..
The arc point file is saved as Hollow Square_arc_point.gcode


>>> fillet.arcPointFiles(["Hollow Square.gcode"])
File Hollow Square.gcode is being filleted into arc points.
..
The arc point file is saved as Hollow Square_arc_point.gcode


>>> fillet.arcRadius()
File Hollow Square.gcode is being filleted into arc radiuses.
..
The arc radius file is saved as Hollow Square_arc_radius.gcode


>>> fillet.arcRadiusFile("Hollow Square.gcode")
File Hollow Square.gcode is being filleted into arc radiuses.
..
The arc radius file is saved as Hollow Square_arc_radius.gcode


>>> fillet.arcRadiusFiles(["Hollow Square.gcode"])
File Hollow Square.gcode is being filleted into arc radiuses.
..
The arc radius file is saved as Hollow Square_arc_radius.gcode


>>> fillet.arcSegment()
File Hollow Square.gcode is being arc segmented.
..
The arc segment file is saved as Hollow Square_arc_segment.gcode


>>> fillet.arcSegmentFile("Hollow Square.gcode")
File Hollow Square.gcode is being arc segmented.
..
The arc segment file is saved as Hollow Square_arc_segment.gcode


>>> fillet.arcSegmentFiles(["Hollow Square.gcode"])
File Hollow Square.gcode is being arc segmented.
..
The arc segment file is saved as Hollow Square_arc_segment.gcode

"""

from vec3 import Vec3
import cStringIO
import euclidean
import gcodec
import math
import preferences


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


#add open webbrowser first time file is created choice
def getVectorGcode( gcodeText, fileordirectoryPreferences = None ):
	"Write a gcode text."
	if gcodeText == '':
		return ''
	if fileordirectoryPreferences == None:
		fileordirectoryPreferences = FileOrDirectoryPreferences()
		preferences.readPreferences( fileordirectoryPreferences )
	skein = FileOrDirectorySkein()
	skein.parseGcode( gcodeText, fileordirectoryPreferences )
	return skein.vectorWindow.getVectorFormattedText()

def writeSkeinforgeVectorFile( filename ):
	"Write scalable vector graphics for a skeinforge gcode file, if 'Write Scalable Vector Graphics for Skeinforge Chain' is selected."
	fileordirectoryPreferences = FileOrDirectoryPreferences()
	preferences.readPreferences( fileordirectoryPreferences )
	if fileordirectoryPreferences.writeSkeinforgeSVG.value:
		writeVectorFile( filename )

def writeVectorFile( filename = '' ):
	"Write scalable vector graphics for a gcode file.  If no filename is specified, write scalable vector graphics for the first gcode file in this folder."
	if filename == '':
		unmodified = gcodec.getFilesWithFileTypeWithoutWords( 'gcode' )
		if len( unmodified ) == 0:
			print( "There is no gcode file in this folder." )
			return
		filename = unmodified[ 0 ]
	fileordirectoryPreferences = FileOrDirectoryPreferences()
	preferences.readPreferences( fileordirectoryPreferences )
	print( 'Scalable vector graphics are being generated for the file ' + gcodec.getSummarizedFilename( filename ) )
	fileText = gcodec.getFileText( filename )
	suffixFilename = filename[ : filename.rfind( '.' ) ] + '.svg'
	suffixFilename = suffixFilename.replace( ' ', '_' )
	gcodec.writeFileText( suffixFilename, getVectorGcode( fileText, fileordirectoryPreferences ) )
	print( 'The scalable vector graphics file is saved as ' + gcodec.getSummarizedFilename( suffixFilename ) )


class FileOrDirectoryPreferences:
	"A class to handle the fileordirectory preferences."
	def __init__( self ):
		"Set the default preferences, execute title & preferences filename."
		#Set the default preferences.
		self.pixelsWidthExtrusion = preferences.FloatPreference().getFromValue( 'Pixels for the Width of the Extrusion (ratio):', 10.0 )
		self.writeSkeinforgeSVG = preferences.BooleanPreference().getFromValue( 'Write Scalable Vector Graphics for Skeinforge Chain:', True )
		directoryRadio = []
		self.directoryPreference = preferences.RadioLabel().getFromRadioLabel( 'Write Vector Graphics for All Unmodified Files in a Directory', 'File or Directory Choice:', directoryRadio, False )
		self.filePreference = preferences.Radio().getFromRadio( 'Write Vector Graphics File', directoryRadio, True )
		self.filenameInput = preferences.Filename().getFromFilename( [ ( 'Gcode text files', '*.gcode' ) ], 'Open File to Write Vector Graphics for', '' )
		#Create the archive, title of the execute button, title of the dialog & preferences filename.
		self.archive = [ self.pixelsWidthExtrusion, self.writeSkeinforgeSVG, self.directoryPreference, self.filePreference, self.filenameInput ]
		self.executeTitle = 'Write Vector Graphics'
		self.filenamePreferences = preferences.getPreferencesFilePath( 'fileordirectory.csv' )
		self.filenameHelp = 'fileordirectory.html'
		self.title = 'File or Directory Preferences'

	def execute( self ):
		"Write button has been clicked."
		filenames = gcodec.getGcodeDirectoryOrFile( self.directoryPreference.value, self.filenameInput.value, self.filenameInput.wasCancelled )
		for filename in filenames:
			writeVectorFile( filename )


def main( hashtable = None ):
	"Display the file or directory dialog."
	preferences.displayDialog( FileOrDirectoryPreferences() )

if __name__ == "__main__":
	main()
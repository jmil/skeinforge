"""
Gifscene is a script to display a gif for each layer of a gcode file.

The default 'Activate Gifscene' checkbox is on.  When it is on, the functions described below will work when called from the
skeinforge toolchain, when it is off, the functions will not be called from the toolchain.  The functions will still be called, whether
or not the 'Activate Gifscene' checkbox is on, when gifscene is run directly.

To run gifscene, in a shell in the folder which gifscene is in type:
> python gifscene.py

To run gifscene you need the Python Imaging Library, which can be downloaded from:
www.pythonware.com/products/pil/

I have not been able to install the Python Imaging Library, so I can only hope that I'm calling Nophead's code correctly.  If you
have the Python Imaging Library and gifscene still does not work for you, please post that in the 'How to Print Gcode from Host'
thread at:
http://forums.reprap.org/read.php?12,10772

An explanation of the gcodes is at:
http://reprap.org/bin/view/Main/Arduino_GCode_Interpreter

and at:
http://reprap.org/bin/view/Main/MCodeReference

A gode example is at:
http://forums.reprap.org/file.php?12,file=565

This example displays gifs for the gcode file Screw Holder.gcode.  This example is run in a terminal in the folder which
contains Screw Holder.gcode and gifscene.py.


> python
Python 2.5.1 (r251:54863, Sep 22 2007, 01:43:31)
[GCC 4.2.1 (SUSE Linux)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import gifscene
>>> gifscene.main()
This brings up the gifscene dialog.


>>> gifscene.gifsceneFile()
A gif for each layer of a gcode file is displayed.

"""

#Init has to be imported first because it has code to workaround the python bug where relative imports don't work if the module is imported as a main module.
import __init__

from skeinforge_tools.skeinforge_utilities import gcodec
from skeinforge_tools.skeinforge_utilities import preferences
from skeinforge_tools import polyfile
import cStringIO
import sys

__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


def gifsceneFile( filename = '' ):
	"Gifscene a gcode file.  If no filename is specified, gifscene the first gcode file in this folder that is not modified."
	if filename == '':
		unmodified = gcodec.getUnmodifiedGCodeFiles()
		if len( unmodified ) == 0:
			print( "There are no unmodified gcode files in this folder." )
			return
		filename = unmodified[ 0 ]
	writeGifsceneFileGivenText( filename, gcodec.getFileText( filename ) )

def getGifsceneGcode( gcodeText ):
	"Get gcode text with added gifscenes."
	skein = GifsceneSkein()
	skein.parseGcode( gcodeText )
	return skein.output.getvalue()

def writeGifsceneFileGivenText( filename, gcodeText ):
	"Write a gifsceneed gcode file for a gcode file."
	from skeinforge_tools.analyze_plugins.analyze_utilities import preview
	preview.viewGif( filename, gcodeText )

def writeOutput( filename, gcodeText = '' ):
	"Write a gifsceneed gcode file for a skeinforge gcode file, if 'Write Gifsceneed File for Skeinforge Chain' is selected."
	gifscenePreferences = GifscenePreferences()
	preferences.readPreferences( gifscenePreferences )
	if gcodeText == '':
		gcodeText = gcodec.getFileText( filename )
	if gifscenePreferences.activateGifscene.value:
		writeGifsceneFileGivenText( filename, gcodeText )


class GifsceneSkein:
	"A class to gifscene a gcode skein."
	def __init__( self ):
		self.oldLocation = None
		self.output = cStringIO.StringIO()

	def addGifscene( self, gifscene ):
		"Add a gcode gifscene and a newline to the output."
		self.output.write( "( " + gifscene + " )\n" )

	def linearMove( self, splitLine ):
		"Gifscene a linear move."
		location = gcodec.getLocationFromSplitLine( self.oldLocation, splitLine )
		self.addGifscene( "Linear move to " + str( location ) + "." );
		self.oldLocation = location

	def parseGcode( self, gcodeText ):
		"Parse gcode text and store the gifsceneed gcode."
		lines = gcodec.getTextLines( gcodeText )
		for line in lines:
			self.parseLine( line )

	def parseLine( self, line ):
		"Parse a gcode line and add it to the gifsceneed gcode."
		splitLine = line.split( ' ' )
		if len( splitLine ) < 1:
			return
		firstWord = splitLine[ 0 ]
		if firstWord == 'G1':
			self.linearMove( splitLine )
		elif firstWord == 'G2':
			self.setHelicalMoveEndpoint( splitLine )
			self.addGifscene( "Helical clockwise move to " + str( self.oldLocation ) + "." )
		self.output.write( line + "\n" )

	def setHelicalMoveEndpoint( self, splitLine ):
		"Get the endpoint of a helical move."
		if self.oldLocation == None:
			print( "A helical move is relative and therefore must not be the first move of a gcode file." )
			return
		location = gcodec.getLocationFromSplitLine( self.oldLocation, splitLine )
		location.add( self.oldLocation )
		self.oldLocation = location


class GifscenePreferences:
	"A class to handle the gifscene preferences."
	def __init__( self ):
		"Set the default preferences, execute title & preferences filename."
		#Set the default preferences.
		self.archive = []
		self.activateGifscene = preferences.BooleanPreference().getFromValue( 'Activate Gifscene', False )
		self.archive.append( self.activateGifscene )
		self.filenameInput = preferences.Filename().getFromFilename( [ ( 'Gcode text files', '*.gcode' ) ], 'Open File to Display Gifs for', '' )
		self.archive.append( self.filenameInput )
		#Create the archive, title of the execute button, title of the dialog & preferences filename.
		self.executeTitle = 'Display Gifs'
		self.filenamePreferences = preferences.getPreferencesFilePath( 'gifscene.csv' )
		self.filenameHelp = 'skeinforge_tools.analyze_plugins.gifscene.html'
		self.saveTitle = 'Save Preferences'
		self.title = 'Gifscene Preferences'

	def execute( self ):
		"Write button has been clicked."
		filenames = polyfile.getFileOrGcodeDirectory( self.filenameInput.value, self.filenameInput.wasCancelled )
		for filename in filenames:
                        print filename
			gifsceneFile( filename )


def main( hashtable = None ):
        if len(sys.argv) > 1:
                gifsceneFile(sys.argv[1])
        else:
                "Display the gifscene dialog."
                preferences.displayDialog( GifscenePreferences() )

if __name__ == "__main__":
	main()


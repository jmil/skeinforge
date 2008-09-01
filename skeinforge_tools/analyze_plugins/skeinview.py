"""
Skeinview is a script to display each layer of a gcode file.

The default 'Activate Skeinview' checkbox is on.  When it is on, the functions described below will work when called from the
skeinforge toolchain, when it is off, the functions will not be called from the toolchain.  The functions will still be called, whether
or not the 'Activate Skeinview' checkbox is on, when skeinview is run directly.

If "Go Around Extruder Off Travel" is selected, the display will include the travel when the extruder is off, which means it will
include the nozzle wipe path if any.  The "Pixels over Extrusion Width" preference is the scale of the image, the higher the
number, the greater the size of the display.  If the number is too high, the display will be larger than the screen.

To run skeinview, in a shell in the folder which skeinview is in type:
> python skeinview.py

An explanation of the gcodes is at:
http://reprap.org/bin/view/Main/Arduino_GCode_Interpreter

and at:
http://reprap.org/bin/view/Main/MCodeReference

A gode example is at:
http://forums.reprap.org/file.php?12,file=565

This example displays a skein view for the gcode file Screw Holder.gcode.  This example is run in a terminal in the folder which
contains Screw Holder.gcode and skeinview.py.


> python skeinview.py
This brings up the skeinview dialog.


> python skeinview.py Screw Holder.gcode
This brings up a skein window to view each layer of a gcode file.


> python
Python 2.5.1 (r251:54863, Sep 22 2007, 01:43:31)
[GCC 4.2.1 (SUSE Linux)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import skeinview
>>> skeinview.main()
This brings up the skeinview dialog.


>>> skeinview.skeinviewFile()
This brings up a skein window to view each layer of a gcode file.

"""

from __future__ import absolute_import
#Init has to be imported first because it has code to workaround the python bug where relative imports don't work if the module is imported as a main module.
import __init__

from skeinforge_tools.skeinforge_utilities.vec3 import Vec3
from skeinforge_tools.skeinforge_utilities import euclidean
from skeinforge_tools.skeinforge_utilities import gcodec
from skeinforge_tools.skeinforge_utilities import preferences
from skeinforge_tools import polyfile
import cStringIO
import sys


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


def displaySkeinviewFileGivenText( gcodeText, skeinviewPreferences = None ):
	"Display a skeinviewed gcode file for a gcode file."
	if gcodeText == '':
		return ''
	if skeinviewPreferences == None:
		skeinviewPreferences = SkeinviewPreferences()
		preferences.readPreferences( skeinviewPreferences )
	skein = SkeinviewSkein()
	skein.parseGcode( gcodeText, skeinviewPreferences )
	SkeinWindow( skein.scaleSize, skein.skeinPanes )

def skeinviewFile( filename = '' ):
	"Skeinview a gcode file.  If no filename is specified, skeinview the first gcode file in this folder that is not modified."
	if filename == '':
		unmodified = gcodec.getUnmodifiedGCodeFiles()
		if len( unmodified ) == 0:
			print( "There are no unmodified gcode files in this folder." )
			return
		filename = unmodified[ 0 ]
	gcodeText = gcodec.getFileText( filename )
	displaySkeinviewFileGivenText( gcodeText )

def writeOutput( filename, gcodeText = '' ):
	"Write a skeinviewed gcode file for a skeinforge gcode file, if 'Activate Skeinview' is selected."
	skeinviewPreferences = SkeinviewPreferences()
	preferences.readPreferences( skeinviewPreferences )
	if skeinviewPreferences.activateSkeinview.value:
		if gcodeText == '':
			gcodeText = gcodec.getFileText( filename )
		displaySkeinviewFileGivenText( gcodeText, skeinviewPreferences )


class ColoredLine:
	"A colored line."
	def __init__( self, colorName, complexBegin, complexEnd ):
		"Set the color name and corners."
		self.colorName = colorName
		self.complexBegin = complexBegin
		self.complexEnd = complexEnd
	
	def __repr__( self ):
		"Get the string representation of this colored line."
		return '%s, %s, %s' % ( self.colorName, self.complexBegin, self.complexEnd )


class SkeinviewPreferences:
	"A class to handle the skeinview preferences."
	def __init__( self ):
		"Set the default preferences, execute title & preferences filename."
		#Set the default preferences.
		self.archive = []
		self.activateSkeinview = preferences.BooleanPreference().getFromValue( 'Activate Skeinview', True )
		self.archive.append( self.activateSkeinview )
		self.filenameInput = preferences.Filename().getFromFilename( [ ( 'Gcode text files', '*.gcode' ) ], 'Open File to Skeinview', '' )
		self.archive.append( self.filenameInput )
		self.goAroundExtruderOffTravel = preferences.BooleanPreference().getFromValue( 'Go Around Extruder Off Travel', False )
		self.archive.append( self.goAroundExtruderOffTravel )
		self.pixelsWidthExtrusion = preferences.FloatPreference().getFromValue( 'Pixels over Extrusion Width (ratio):', 5.0 )
		self.archive.append( self.pixelsWidthExtrusion )
		#Create the archive, title of the execute button, title of the dialog & preferences filename.
		self.executeTitle = 'Skeinview'
		self.filenamePreferences = preferences.getPreferencesFilePath( 'skeinview.csv' )
		self.filenameHelp = 'skeinforge_tools.analyze_plugins.skeinview.html'
		self.saveTitle = 'Save Preferences'
		self.title = 'Skeinview Preferences'

	def execute( self ):
		"Write button has been clicked."
		filenames = polyfile.getFileOrGcodeDirectory( self.filenameInput.value, self.filenameInput.wasCancelled )
		for filename in filenames:
			skeinviewFile( filename )


class SkeinviewSkein:
	"A class to write a get a scalable vector graphics text for a gcode skein."
	def __init__( self ):
		self.extrusionNumber = 0
		self.extrusionWidth = 0.4
		self.skeinPanes = []

	def addToPath( self, location, nextLine ):
		"Add a point to travel and maybe extrusion."
		if self.oldLocation == None:
			return
		beginningComplex = self.oldLocation.dropAxis( 2 )
		endComplex = location.dropAxis( 2 )
		colorName = 'gray'
		if self.extruderActive:
			colorName = self.colorNames[ self.extrusionNumber % len( self.colorNames ) ]
		else:
			splitLine = nextLine.split( ' ' )
			firstWord = ''
			if len( splitLine ) > 0:
				firstWord = splitLine[ 0 ]
			if firstWord != 'G1':
				segment = endComplex - beginningComplex
				segmentLength = abs( segment )
				if segmentLength > 0.0:
					truncation = 0.3 * min( segmentLength, self.extrusionWidth )
					endComplex -= segment / segmentLength * truncation
		coloredLine = ColoredLine( colorName, self.scale * beginningComplex - self.marginCornerLow, self.scale * endComplex - self.marginCornerLow )
		self.skeinPane.append( coloredLine )

	def initializeActiveLocation( self ):
		"Set variables to default."
		self.extruderActive = False
		self.oldLocation = None

	def linearCorner( self, splitLine ):
		"Update the bounding corners."
		location = gcodec.getLocationFromSplitLine( self.oldLocation, splitLine )
		if self.extruderActive or self.goAroundExtruderOffTravel:
			self.cornerHigh = euclidean.getPointMaximum( self.cornerHigh, location )
			self.cornerLow = euclidean.getPointMinimum( self.cornerLow, location )
		self.oldLocation = location

	def linearMove( self, splitLine, nextLine ):
		"Get statistics for a linear move."
		location = gcodec.getLocationFromSplitLine( self.oldLocation, splitLine )
		self.addToPath( location, nextLine )
		self.oldLocation = location

	def parseCorner( self, line ):
		"Parse a gcode line and use the location to update the bounding corners."
		splitLine = line.split()
		if len( splitLine ) < 1:
			return
		firstWord = splitLine[ 0 ]
		if firstWord == 'G1':
			self.linearCorner( splitLine )
		elif firstWord == 'M101':
			self.extruderActive = True
		elif firstWord == 'M103':
			self.extruderActive = False
		elif firstWord == '(<extrusionWidth>':
			self.extrusionWidth = float( splitLine[ 1 ] )

	def parseGcode( self, gcodeText, skeinviewPreferences ):
		"Parse gcode text and store the vector output."
		self.initializeActiveLocation()
		self.cornerHigh = Vec3( - 999999999.0, - 999999999.0, - 999999999.0 )
		self.cornerLow = Vec3( 999999999.0, 999999999.0, 999999999.0 )
		self.goAroundExtruderOffTravel = skeinviewPreferences.goAroundExtruderOffTravel.value
		lines = gcodec.getTextLines( gcodeText )
		for line in lines:
			self.parseCorner( line )
		self.scale = skeinviewPreferences.pixelsWidthExtrusion.value / self.extrusionWidth
		self.scaleCornerHigh = self.scale * self.cornerHigh.dropAxis( 2 )
		self.scaleCornerLow = self.scale * self.cornerLow.dropAxis( 2 )
		margin = complex( 5.0, 5.0 )
		self.marginCornerLow = self.scaleCornerLow - margin
		self.scaleSize = margin + self.scaleCornerHigh - self.marginCornerLow
		self.initializeActiveLocation()
		self.colorNames = [ 'brown', 'red', 'orange', 'yellow', 'green', 'blue', 'purple' ]
		for lineIndex in range( len( lines ) ):
			line = lines[ lineIndex ]
			nextLine = ''
			nextIndex = lineIndex + 1
			if nextIndex < len( lines ):
				nextLine = lines[ nextIndex ]
			self.parseLine( line, nextLine )

	def parseLine( self, line, nextLine ):
		"Parse a gcode line and add it to the vector output."
		splitLine = line.split()
		if len( splitLine ) < 1:
			return
		firstWord = splitLine[ 0 ]
		if firstWord == 'G1':
			self.linearMove( splitLine, nextLine )
		elif firstWord == 'M101':
			self.extruderActive = True
			self.extrusionNumber += 1
		elif firstWord == 'M103':
			self.extruderActive = False
		elif firstWord == '(<layerStart>':
			self.extrusionNumber = 0
			self.skeinPane = []
			self.skeinPanes.append( self.skeinPane )


class SkeinWindow:
	def __init__( self, size, skeinPanes ):
		self.index = 0
		self.skeinPanes = skeinPanes
		self.root = preferences.Tkinter.Tk()
		self.root.title( "Skeinview from HydraRaptor" )
		frame = preferences.Tkinter.Frame( self.root )
		frame.pack()
		self.canvas = preferences.Tkinter.Canvas( frame, width = int( size.real ), height = int( size.imag ) )
		self.canvas.pack()
		self.canvas.config( scrollregion = self.canvas.bbox( preferences.Tkinter.ALL ) )
		self.exit_button = preferences.Tkinter.Button( frame, text = "Exit", fg = "red", command = frame.quit )
		self.exit_button.pack( side=preferences.Tkinter.RIGHT )
		self.down_button = preferences.Tkinter.Button( frame, text = "Down", command = self.down )
		self.down_button.pack( side=preferences.Tkinter.LEFT )
		self.up_button = preferences.Tkinter.Button( frame, text = "Up", command = self.up )
		self.up_button.pack( side=preferences.Tkinter.LEFT )
		self.update()
		if preferences.globalIsMainLoopRunning:
			return
		preferences.globalIsMainLoopRunning = True
		self.root.mainloop()
		preferences.globalIsMainLoopRunning = False

	def update( self ):
		skeinPane = self.skeinPanes[ self.index ]
		self.canvas.delete( preferences.Tkinter.ALL )
		for coloredLine in skeinPane:
			self.canvas.create_line( coloredLine.complexBegin.real, coloredLine.complexBegin.imag, coloredLine.complexEnd.real, coloredLine.complexEnd.imag, fill = coloredLine.colorName )
		if self.index < len( self.skeinPanes ) - 1:
			self.up_button.config( state = preferences.Tkinter.NORMAL )
		else:
			self.up_button.config( state = preferences.Tkinter.DISABLED )
		if self.index > 0:
			self.down_button.config( state = preferences.Tkinter.NORMAL )
		else:
			self.down_button.config( state = preferences.Tkinter.DISABLED )

	def up( self ):
		self.index += 1
		self.update()

	def down( self ):
		self.index -= 1
		self.update()


def main():
	"Display the skeinview dialog."
	if len( sys.argv ) > 1:
		skeinviewFile( ' '.join( sys.argv[ 1 : ] ) )
	else:
		preferences.displayDialog( SkeinviewPreferences() )

if __name__ == "__main__":
	main()

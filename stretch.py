"""
Stretch is a script to stretch the threads to partially compensate for filament shrinkage when extruded.

The important value for the stretch preferences is "Maximum Stretch Over Half Extrusion Width (ratio)" which is the ratio of the
maximum amount the thread will be stretched compared to half of the extrusion width. The default is 0.3, if you do not want to
use stretch, set the value to zero.  With a value of one or more, the script might stretch a couple of threads in opposite directions
so much that they overlap.  In theory this would be because they'll contract back to the desired places, but in practice they might
not.  The optimal value of stretch will be different for different materials, so the default value of 0.3 is chosen because it will
counter the contraction a bit, but not enough to cause overlap trouble.

In general, stretch will widen holes and push corners out.  The algorithm works by checking at each turning point on the
extrusion path what the direction of the thread is at a distance of "Stretch from Distance over Extrusion Width (ratio)" times the
extrusion width, on both sides, and moves the thread in the opposite direction.  The magnitude of the stretch increases with the
amount that the direction of the two threads is similar and by the "Maximum Stretch Over Half Extrusion Width (ratio)".  The
script then also stretches the thread at two locations on the path on close to the turning points.  In practice the filament
contraction will be similar but different from the algorithm, so even once the optimal parameters are determined, the stretch
script will not be able to eliminate the inaccuracies caused by contraction, but it should reduce them.  To run stretch, in a shell
type:
> python stretch.py

To run stretch, install python 2.x on your machine, which is avaliable from http://www.python.org/download/

To use the preferences dialog you'll also need Tkinter, which probably came with the python installation.  If it did not, look for it at:
www.tcl.tk/software/tcltk/

To export a GNU Triangulated Surface file from Art of Illusion, you can use the Export GNU Triangulated Surface script at:
http://members.axion.net/~enrique/Export%20GNU%20Triangulated%20Surface.bsh

To bring it into Art of Illusion, drop it into the folder ArtOfIllusion/Scripts/Tools/.

The GNU Triangulated Surface format is supported by Mesh Viewer, and it is described at:
http://gts.sourceforge.net/reference/gts-surfaces.html#GTS-SURFACE-WRITE

To turn an STL file into filled, stretched gcode, first import the file using the STL import plugin in the import submenu of the file menu
of Art of Illusion.  Then from the Scripts submenu in the Tools menu, choose Export GNU Triangulated Surface and select the
imported STL shape.  Then type 'python slice.py' in a shell in the folder which slice & stretch are in and when the dialog pops up, set
the parameters and click 'Save Preferences'.  Then type 'python fill.py' in a shell in the folder which fill is in and when the dialog
pops up, set the parameters and click 'Save Preferences'.  Then type 'python comb.py' in a shell and when the dialog pops up,
change the parameters if you wish but the default 'Comb Hair' is fine.  Then type 'python stretch.py' in a shell and when the dialog pops up,
change the parameters if you wish but the default is fine to start.  Then click 'Stretch', choose the file which you exported in
Export GNU Triangulated Surface and the filled & stretched file will be saved with the suffix '_stretch'.  Once you've made a shape, then
you can decide what the optimal value of "Maximum Stretch Over Half Extrusion Width (ratio)" is for that material.

To write documentation for this program, open a shell in the stretch.py directory, then type 'pydoc -w stretch', then open 'stretch.html' in
a browser or click on the '?' button in the dialog.  To write documentation for all the python scripts in the directory, type 'pydoc -w ./'.
To use other functions of stretch, type 'python' in a shell to run the python interpreter, then type 'import stretch' to import this program.

The computation intensive python modules will use psyco if it is available and run about twice as fast.  Psyco is described at:
http://psyco.sourceforge.net/index.html

The psyco download page is:
http://psyco.sourceforge.net/download.html

The following examples stretch the files Hollow Square.gcode & Hollow Square.gts.  The examples are run in a terminal in the folder which contains
Hollow Square.gcode, Hollow Square.gts and stretch.py.  The stretch function will stretch if 'Comb Hair' is true, which can be set in the dialog or by changing
the preferences file 'stretch.csv' with a text editor or a spreadsheet program set to separate tabs.  The functions stretchChainFile and
getStretchChainGcode check to see if the text has been stretched, if not they call the getFillChainGcode in fill.py to fill the text; once they
have the filled text, then they stretch.


> pydoc -w stretch
wrote stretch.html


> python stretch.py
This brings up the dialog, after clicking 'Stretch', the following is printed:
File Hollow Square.gts is being chain stretched.
The stretched file is saved as Hollow Square_stretch.gcode


>python
Python 2.5.1 (r251:54863, Sep 22 2007, 01:43:31)
[GCC 4.2.1 (SUSE Linux)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import stretch
>>> stretch.main()
This brings up the stretch dialog.


>>> stretch.stretchChainFile()
Hollow Square.gts
File Hollow Square.gts is being chain stretched.
The stretched file is saved as Hollow Square_stretch.gcode


>>> stretch.stretchFile()
File Hollow Square.gcode is being stretched.
The stretched file is saved as Hollow Square_stretch.gcode


>>> stretch.getStretchGcode("
( GCode generated by May 8, 2008 slice.py )
( Extruder Initialization )
..
many lines of gcode
..
")


>>> stretch.getStretchChainGcode("
( GCode generated by May 8, 2008 slice.py )
( Extruder Initialization )
..
many lines of gcode
..
")

"""

from vec3 import Vec3
import comb
import cStringIO
import euclidean
import gcodec
import intercircle
import multifile
import preferences
import time
import vectorwrite


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


def getStretchChainGcode( gcodeText, stretchPreferences = None ):
	"Stretch a gcode linear move text.  Chain stretch the gcode if it is not already stretched."
	if not gcodec.isProcedureDone( gcodeText, 'comb' ):
		gcodeText = comb.getCombChainGcode( gcodeText )
	return getStretchGcode( gcodeText, stretchPreferences )

def getStretchGcode( gcodeText, stretchPreferences = None ):
	"Stretch a gcode linear move text."
	if gcodeText == '':
		return ''
	if gcodec.isProcedureDone( gcodeText, 'stretch' ):
		return gcodeText
	if stretchPreferences == None:
		stretchPreferences = StretchPreferences()
		preferences.readPreferences( stretchPreferences )
	if stretchPreferences.stretchOverHalfExtrusionWidth.value <= 0.0:
		return gcodeText
	skein = StretchSkein()
	skein.parseGcode( gcodeText, stretchPreferences )
	return skein.output.getvalue()

def stretchChainFile( filename = '' ):
	"""Stretch a gcode linear move file.  Chain stretch the gcode if it is not already stretched.
	Depending on the preferences, either arcPoint, arcRadius, arcSegment, bevel or do nothing.
	If no filename is specified, stretch the first unmodified gcode file in this folder."""
	if filename == '':
		unmodified = gcodec.getGNUGcode()
		if len( unmodified ) == 0:
			print( "There are no unmodified gcode files in this folder." )
			return
		filename = unmodified[ 0 ]
	stretchPreferences = StretchPreferences()
	preferences.readPreferences( stretchPreferences )
	startTime = time.time()
	print( 'File ' + gcodec.getSummarizedFilename( filename ) + ' is being chain stretched.' )
	gcodeText = gcodec.getFileText( filename )
	if gcodeText == '':
		return
	suffixFilename = filename[ : filename.rfind( '.' ) ] + '_stretch.gcode'
	gcodec.writeFileText( suffixFilename, getStretchChainGcode( gcodeText, stretchPreferences ) )
	print( 'The stretched file is saved as ' + gcodec.getSummarizedFilename( suffixFilename ) )
	vectorwrite.writeSkeinforgeVectorFile( suffixFilename )
	print( 'It took ' + str( int( round( time.time() - startTime ) ) ) + ' seconds to stretch the file.' )

def stretchFile( filename = '' ):
	"""Stretch a gcode linear move file.  Depending on the preferences, either arcPoint, arcRadius, arcSegment, bevel or do nothing.
	If no filename is specified, stretch the first unmodified gcode file in this folder."""
	if filename == '':
		unmodified = gcodec.getUnmodifiedGCodeFiles()
		if len( unmodified ) == 0:
			print( "There are no unmodified gcode files in this folder." )
			return
		filename = unmodified[ 0 ]
	stretchPreferences = StretchPreferences()
	preferences.readPreferences( stretchPreferences )
	print( 'File ' + gcodec.getSummarizedFilename( filename ) + ' is being stretched.' )
	gcodeText = gcodec.getFileText( filename )
	if gcodeText == '':
		return
	suffixFilename = filename[ : filename.rfind( '.' ) ] + '_stretch.gcode'
	gcodec.writeFileText( suffixFilename, getStretchGcode( gcodeText, stretchPreferences ) )
	print( 'The stretched file is saved as ' + suffixFilename )
	vectorwrite.writeSkeinforgeVectorFile( suffixFilename )

class StretchSkein:
	"A class to stretch a skein of extrusions."
	def __init__( self ):
		self.bridgeExtrusionWidthOverSolid = 1.0
		self.extruderActive = False
		self.feedrateMinute = 960.0
		self.halfExtrusionWidth = 0.2
		self.layer = None
		self.layers = []
		self.lineIndex = 0
		self.lines = None
		self.oldLocation = None
		self.output = cStringIO.StringIO()

	def addAlongWayLine( self, alongRatio, location ):
		"Add stretched gcode line, along the way from the old location to the location."
		oneMinusAlong = 1.0 - alongRatio
		alongWayLocation = self.oldLocation.times( alongRatio ).plus( location.times( oneMinusAlong ) )
		alongWayLine = self.getStretchedLineFromIndexLocation( self.lineIndex - 1, self.lineIndex, alongWayLocation )
		self.addLine( alongWayLine )

	def addLine( self, line ):
		"Add a line of text and a newline to the output."
		self.output.write( line + "\n" )

	def addStretchesBeforePoint( self, location ):
		"Get stretched gcode line."
		distanceToOld = location.distance( self.oldLocation )
		if distanceToOld == 0.0:
			print( 'This should never happen, there are two identical points in a row.' )
			print( location )
			return
		alongRatio = self.stretchFromDistance / distanceToOld
		if alongRatio > 0.7:
			return
		if alongRatio > 0.33333333333:
			alongRatio = 0.33333333333
		self.addAlongWayLine( 1.0 - alongRatio, location )
		self.addAlongWayLine( alongRatio, location )

	def getRelativeStretch( self, location, lineIndexRange ):
		"Get relative stretch for a location minus a point."
		locationComplex = location.dropAxis( 2 )
		lastLocationComplex = locationComplex
		oldTotalLength = 0.0
		pointComplex = locationComplex
		stretchRatio = 1.0
		totalLength = 0.0
		if not self.extruderActive:
			stretchRatio = self.stretchPreferences.travelOverExtrusionStretch.value
		for lineIndex in lineIndexRange:
			line = self.lines[ lineIndex ]
			splitLine = line.split( ' ' )
			firstWord = ''
			if len( splitLine ) > 0:
				firstWord = splitLine[ 0 ]
			if firstWord == 'G1':
				pointComplex = gcodec.getLocationFromSplitLine( self.oldLocation, splitLine ).dropAxis( 2 )
				locationMinusPoint = lastLocationComplex - pointComplex
				locationMinusPointLength = abs( locationMinusPoint )
				totalLength += locationMinusPointLength
				if totalLength >= self.stretchFromDistance:
					distanceFromRatio = ( self.stretchFromDistance - oldTotalLength ) / locationMinusPointLength
					totalPoint = distanceFromRatio * pointComplex + ( 1.0 - distanceFromRatio ) * lastLocationComplex
					locationMinusTotalPoint = locationComplex - totalPoint
					return stretchRatio * locationMinusTotalPoint / self.stretchFromDistance
				lastLocationComplex = pointComplex
				oldTotalLength = totalLength
			elif firstWord == 'M103':
				stretchRatio = self.stretchPreferences.travelOverExtrusionStretch.value
		locationMinusPoint = locationComplex - pointComplex
		locationMinusPointLength = abs( locationMinusPoint )
		if locationMinusPointLength > 0.0:
			return stretchRatio * locationMinusPoint / locationMinusPointLength
		return complex()

	def getStretchedLine( self, splitLine ):
		"Get stretched gcode line."
		location = gcodec.getLocationFromSplitLine( self.oldLocation, splitLine )
		self.feedrateMinute = gcodec.getFeedrateMinute( self.feedrateMinute, splitLine )
		if self.oldLocation != None:
			self.addStretchesBeforePoint( location )
		self.oldLocation = location
		return self.getStretchedLineFromIndexLocation( self.lineIndex - 1, self.lineIndex + 1, location )

	def getStretchedLineFromIndexLocation( self, indexPreviousStart, indexNextStart, location ):
		"Get stretched gcode line from line index and location."
		nextRange = range( indexNextStart, len( self.lines ) )
		previousRange = range( indexPreviousStart, 3, - 1 )
		relativeStretch = self.getRelativeStretch( location, nextRange ) + self.getRelativeStretch( location, previousRange )
		relativeStretch *= 0.8
		relativeStretchLength = abs( relativeStretch )
		if relativeStretchLength > 1.0:
			relativeStretch /= relativeStretchLength
		absoluteStretch = relativeStretch * self.maximumAbsoluteStretch
		stretchedLocation = location.plus( Vec3( absoluteStretch.real, absoluteStretch.imag, 0.0 ) )
		stretchedLine = "G1 X" + euclidean.getRoundedToThreePlaces( stretchedLocation.x ) + " Y" + euclidean.getRoundedToThreePlaces( stretchedLocation.y )
		return stretchedLine + " Z" + euclidean.getRoundedToThreePlaces( stretchedLocation.z ) + ' F' + euclidean.getRoundedToThreePlaces( self.feedrateMinute )

	def parseGcode( self, gcodeText, stretchPreferences ):
		"Parse gcode text and store the stretch gcode."
		self.lines = gcodec.getTextLines( gcodeText )
		self.layerIndex = - 1
		self.stretchPreferences = stretchPreferences
		for self.lineIndex in range( len( self.lines ) ):
			line = self.lines[ self.lineIndex ]
			self.parseStretch( line )

	def parseStretch( self, line ):
		"Parse a gcode line and add it to the stretch skein."
		splitLine = line.split( ' ' )
		if len( splitLine ) < 1:
			return
		firstWord = splitLine[ 0 ]
		if firstWord == 'G1':
			line = self.getStretchedLine( splitLine )
		elif firstWord == 'M101':
			self.extruderActive = True
		elif firstWord == 'M103':
			self.extruderActive = False
		elif firstWord == '(<bridgeExtrusionWidthOverSolid>':
			self.bridgeExtrusionWidthOverSolid = float( splitLine[ 1 ] )
		elif firstWord == '(<bridgeLayer>':
			self.layerMaximumAbsoluteStretch = self.maximumAbsoluteStretch * self.bridgeExtrusionWidthOverSolid
			self.layerStretchFromDistance= self.stretchFromDistance * self.bridgeExtrusionWidthOverSolid
		elif firstWord == '(<extrusionWidth>':
			extrusionWidth = float( splitLine[ 1 ] )
			self.halfExtrusionWidth = 0.5 * extrusionWidth
			self.maximumAbsoluteStretch = self.halfExtrusionWidth * self.stretchPreferences.stretchOverHalfExtrusionWidth.value
			self.stretchFromDistance = self.stretchPreferences.stretchFromDistanceOverExtrusionWidth.value * extrusionWidth
		elif firstWord == '(<layerStart>':
			self.layerMaximumAbsoluteStretch = self.maximumAbsoluteStretch
			self.layerStretchFromDistance = self.stretchFromDistance
		elif firstWord == '(<extrusionStart>':
			self.addLine( '(<procedureDone> stretch )' )
		self.addLine( line )


class StretchPreferences:
	"A class to handle the stretch preferences."
	def __init__( self ):
		"Set the default preferences, execute title & preferences filename."
		#Set the default preferences.
		self.stretchFromDistanceOverExtrusionWidth = preferences.FloatPreference().getFromValue( 'Stretch From Distance Over Extrusion Width (ratio):', 2.0 )
		self.stretchOverHalfExtrusionWidth = preferences.FloatPreference().getFromValue( 'Maximum Stretch Over Half Extrusion Width (ratio):', 0.3 )
		self.travelOverExtrusionStretch = preferences.FloatPreference().getFromValue( 'Travel Stretch Over Extrusion Stretch (ratio):', 0.2 )
		self.filenameInput = preferences.Filename().getFromFilename( [ ( 'GNU Triangulated Surface text files', '*.gts' ), ( 'Gcode text files', '*.gcode' ) ], 'Open File to be Stretched', '' )
		#Create the archive, title of the execute button, title of the dialog & preferences filename.
		self.archive = [
			self.stretchFromDistanceOverExtrusionWidth,
			self.stretchOverHalfExtrusionWidth,
			self.travelOverExtrusionStretch,
			self.filenameInput ]
		self.executeTitle = 'Stretch'
		self.filenamePreferences = preferences.getPreferencesFilePath( 'stretch.csv' )
		self.filenameHelp = 'stretch.html'
		self.title = 'Stretch Preferences'

	def execute( self ):
		"Stretch button has been clicked."
		filenames = multifile.getFileOrGNUUnmodifiedGcodeDirectory( self.filenameInput.value, self.filenameInput.wasCancelled )
		for filename in filenames:
			stretchChainFile( filename )


def main( hashtable = None ):
	"Display the stretch dialog."
	preferences.displayDialog( StretchPreferences() )

if __name__ == "__main__":
	main()

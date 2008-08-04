"""
Vectorwrite is a script to write Scalable Vector Graphics for a gcode file.

The default 'Activate Vectorwrite' checkbox is on.  When it is on, the functions described below will work when called from the
skeinforge toolchain, when it is off, the functions will not be called from the toolchain.  The functions will still be called, whether
or not the 'Activate Vectorwrite' checkbox is on, when vectorwrite is run directly.

The 'Pixels over Extrusion Width' preference is the scale of the graphic in pixels per extrusion width.

To run vectorwrite, in a shell in the folder which vectorwrite is in type:
> python vectorwrite.py

The Scalable Vector Graphics file can be opened by an SVG viewer or an SVG capable browser like Mozilla:
http://www.mozilla.com/firefox/

This example writes vector graphics for the gcode file Screw Holder.gcode.  This example is run in a terminal in the folder which
contains Screw Holder.gcode and vectorwrite.py.


> python
Python 2.5.1 (r251:54863, Sep 22 2007, 01:43:31)
[GCC 4.2.1 (SUSE Linux)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import vectorwrite
>>> vectorwrite.main()
This brings up the vectorwrite dialog.


>>> vectorwrite.vectorwriteFile()
The vector file is saved as Screw Holder_vectorwrite.svg

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
import math
import sys

__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__credits__ = 'Nophead <http://hydraraptor.blogspot.com/>'
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


#add open webbrowser first time file is created choice
def getVectorGcode( gcodeText, vectorwritePreferences = None ):
	"Write a gcode text."
	if gcodeText == '':
		return ''
	if vectorwritePreferences == None:
		vectorwritePreferences = VectorwritePreferences()
		preferences.readPreferences( vectorwritePreferences )
	skein = VectorwriteSkein()
	skein.parseGcode( gcodeText, vectorwritePreferences )
	return skein.vectorWindow.getVectorFormattedText()

def writeOutput( filename, gcodeText = '' ):
	"Write scalable vector graphics for a skeinforge gcode file, if 'Write Scalable Vector Graphics for Skeinforge Chain' is selected."
	vectorwritePreferences = VectorwritePreferences()
	preferences.readPreferences( vectorwritePreferences )
	if gcodeText == '':
		gcodeText = gcodec.getFileText( filename )
	if vectorwritePreferences.activateVectorwrite.value:
		writeVectorFileGivenText( filename, gcodeText, vectorwritePreferences )

def writeVectorFile( filename = '' ):
	"Write scalable vector graphics for a gcode file.  If no filename is specified, write scalable vector graphics for the first gcode file in this folder."
	if filename == '':
		unmodified = gcodec.getFilesWithFileTypeWithoutWords( 'gcode' )
		if len( unmodified ) == 0:
			print( "There is no gcode file in this folder." )
			return
		filename = unmodified[ 0 ]
	vectorwritePreferences = VectorwritePreferences()
	preferences.readPreferences( vectorwritePreferences )
	gcodeText = gcodec.getFileText( filename )
	writeVectorFileGivenText( filename, gcodeText, vectorwritePreferences )

def writeVectorFileGivenText( filename, gcodeText, vectorwritePreferences ):
	"Write scalable vector graphics for a gcode file."
	suffixFilename = filename[ : filename.rfind( '.' ) ] + '.svg'
	suffixFilename = suffixFilename.replace( ' ', '_' )
	gcodec.writeFileText( suffixFilename, getVectorGcode( gcodeText, vectorwritePreferences ) )
	print( 'The scalable vector graphics file is saved as ' + gcodec.getSummarizedFilename( suffixFilename ) )

class VectorWindow:
	"A class to accumulate a scalable vector graphics text."
	def __init__( self ):
		self.height = 0
		self.leftMargin = 20
		self.text = cStringIO.StringIO()
		self.width = 0

	def __repr__( self ):
		"Get the string representation of this VectorWindow."
		return str( self.height ) + ' ' + str( self.width )

	def addColoredLine( self, pointFirst, pointSecond, colorName ):
		"Add a colored line to the text."
		cornerPlusHeight = self.height + self.bottomLeftCorner.imag
		x1String = str( int( round( pointFirst.real - self.bottomLeftCorner.real + self.leftMargin ) ) )
		x2String = str( int( round( pointSecond.real - self.bottomLeftCorner.real + self.leftMargin ) ) )
		y1String = str( int( round( cornerPlusHeight - pointFirst.imag ) ) )
		y2String = str( int( round( cornerPlusHeight - pointSecond.imag ) ) )
		self.addLine( '    <line x1="' + x1String + '" y1="' + y1String + '" x2="' + x2String + '" y2="' + y2String + '" stroke="' + colorName + '" />' )

	def addFontHeight( self, fontSize ):
		"Add quadruple the font size to the height."
		self.height += 4 * fontSize

	def addLine( self, line ):
		"Add a line to the text and a newline."
		self.text.write( line + "\n" )

	def addPane( self ):
		"Add a new window pane for drawing lines."
		self.height += self.topRightCorner.imag - self.bottomLeftCorner.imag

	def addText( self, fontSize, line ):
		"Add a colored line to the text."
		yString = str( 3 * fontSize + self.height )
		self.addLine( '    <text x="'  + str( self.leftMargin ) + '" y="' + yString + '" font-size="24" style="fill-opacity:1.0; stroke:black; stroke-width:0;">' )
		self.addLine( '      ' + line )
		self.addLine( '    </text>' )
		self.addFontHeight( fontSize )
		self.width = max( self.width, fontSize * len( line ) )

	def getVectorFormattedText( self ):
		"Get the text in scalable vector graphics format."
		textBeginning = '<?xml version="1.0"?>\n<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n'
		textBeginning += '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" height="' + str( math.ceil( self.height ) ) + '" width="' + str( self.width + self.leftMargin ) + '">\n'
		textBeginning += '  <g style="fill-opacity:1.0; stroke:black; stroke-width:1;">\n'
		return textBeginning + self.text.getvalue() + '  </g>\n</svg>\n'

	def setPaneCorners( self, bottomLeftCorner, topRightCorner ):
		"Set the corners for the window pane."
		self.bottomLeftCorner = bottomLeftCorner
		self.topRightCorner = topRightCorner
		self.width = self.topRightCorner.real - self.bottomLeftCorner.real


class VectorwriteSkein:
	"A class to write a get a scalable vector graphics text for a gcode skein."
	def __init__( self ):
		self.extrusionNumber = 0
		self.extrusionWidth = 0.4
		self.fontSize = 24

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
		self.vectorWindow.addColoredLine( self.scale * beginningComplex, self.scale * endComplex, colorName )

	def initializeActiveLocation( self ):
		"Set variables to default."
		self.extruderActive = False
		self.layerIndex = 0
		self.oldLocation = None

	def linearCorner( self, splitLine ):
		"Update the bounding corners."
		location = gcodec.getLocationFromSplitLine( self.oldLocation, splitLine )
		if self.extruderActive:
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
		splitLine = line.split( ' ' )
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

	def parseGcode( self, gcodeText, vectorwritePreferences ):
		"Parse gcode text and store the vector output."
		self.initializeActiveLocation()
		self.cornerHigh = Vec3( - 999999999.0, - 999999999.0, - 999999999.0 )
		self.cornerLow = Vec3( 999999999.0, 999999999.0, 999999999.0 )
		lines = gcodec.getTextLines( gcodeText )
		for line in lines:
			self.parseCorner( line )
		self.initializeActiveLocation()
		self.colorNames = [ 'brown', 'red', 'orange', 'yellow', 'green', 'blue', 'purple' ]
		self.scale = vectorwritePreferences.pixelsWidthExtrusion.value / self.extrusionWidth
		self.vectorWindow = VectorWindow()
		self.vectorWindow.setPaneCorners( self.scale * self.cornerLow.dropAxis( 2 ), self.scale * self.cornerHigh.dropAxis( 2 ) )
		for lineIndex in range( len( lines ) ):
			line = lines[ lineIndex ]
			nextLine = ''
			nextIndex = lineIndex + 1
			if nextIndex < len( lines ):
				nextLine = lines[ nextIndex ]
			self.parseLine( line, nextLine )

	def parseLine( self, line, nextLine ):
		"Parse a gcode line and add it to the vector output."
		splitLine = line.split( ' ' )
		if len( splitLine ) < 1 or len( line ) < 1:
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
			if self.layerIndex > 0:
				self.vectorWindow.addFontHeight( self.fontSize )
			self.vectorWindow.addText( self.fontSize, 'Layer index ' + str( self.layerIndex ) + ', z ' + splitLine[ 1 ] )
			self.layerIndex += 1
			self.vectorWindow.addPane()


class VectorwritePreferences:
	"A class to handle the vectorwrite preferences."
	def __init__( self ):
		"Set the default preferences, execute title & preferences filename."
		#Set the default preferences.
		self.archive = []
		self.activateVectorwrite = preferences.BooleanPreference().getFromValue( 'Activate Vectorwrite', True )
		self.archive.append( self.activateVectorwrite )
		self.filenameInput = preferences.Filename().getFromFilename( [ ( 'Gcode text files', '*.gcode' ) ], 'Open File to Write Vector Graphics for', '' )
		self.archive.append( self.filenameInput )
		self.pixelsWidthExtrusion = preferences.FloatPreference().getFromValue( 'Pixels over Extrusion Width (ratio):', 10.0 )
		self.archive.append( self.pixelsWidthExtrusion )
		#Create the archive, title of the execute button, title of the dialog & preferences filename.
		self.executeTitle = 'Write Vector Graphics'
		self.filenamePreferences = preferences.getPreferencesFilePath( 'vectorwrite.csv' )
		self.filenameHelp = 'skeinforge_tools.analyze_plugins.vectorwrite.html'
		self.saveTitle = 'Save Preferences'
		self.title = 'Vectorwrite Preferences'

	def execute( self ):
		"Write button has been clicked."
		filenames = polyfile.getFileOrGcodeDirectory( self.filenameInput.value, self.filenameInput.wasCancelled )
		for filename in filenames:
			writeVectorFile( filename )


def main( hashtable = None ):
	"Display the vectorwrite dialog."
	if len( sys.argv ) > 1:
		writeVectorFile( sys.argv[ 1 ] )
	else:
		preferences.displayDialog( VectorwritePreferences() )

if __name__ == "__main__":
	main()

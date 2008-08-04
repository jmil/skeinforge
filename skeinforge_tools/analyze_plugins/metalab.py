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
import Tkinter, tkMessageBox

__author__ = "Marius Kintel <kintel@sim.no>, metalab.at"
__license__ = "GPL 3.0"

def getMetalabGcode( gcodeText ):
	"Get metalab for a gcode text."
	skein = MetalabSkein()
	skein.parseGcode( gcodeText )
        return skein.output.getvalue()

def metalabFile( filename = '' ):
	"Write metalab for a gcode file.  If no filename is specified, write metalab for the first gcode file in this folder that is not modified."
	if filename == '':
		unmodified = gcodec.getUnmodifiedGCodeFiles()
		if len( unmodified ) == 0:
			print( "There are no unmodified gcode files in this folder." )
			return
		filename = unmodified[ 0 ]
	metalabPreferences = MetalabPreferences()
	preferences.readPreferences( metalabPreferences )
	writeMetalabFileGivenText( filename, gcodec.getFileText( filename ), metalabPreferences )

def writeOutput( filename, gcodeText = '' ):
	"Write metalab for a skeinforge gcode file, if 'Write Metalab File for Skeinforge Chain' is selected."
	metalabPreferences = MetalabPreferences()
	preferences.readPreferences( metalabPreferences )
	if gcodeText == '':
		gcodeText = gcodec.getFileText( filename )
	if metalabPreferences.activateMetalab.value:
		writeMetalabFileGivenText( filename, gcodeText, metalabPreferences )

def writeMetalabFileGivenText( filename, gcodeText, metalabPreferences ):
	"Write metalab for a gcode file."
	print( 'Metalab are being generated for the file ' + gcodec.getSummarizedFilename( filename ) )
	metalabGcode = getMetalabGcode( gcodeText )
	gcodec.writeFileMessageEnd( '.txt', filename, metalabGcode, 'The metalab file is saved as ' )
	if metalabPreferences.printMetalabFileSkeinforge.value:
		print( metalabGcode )


class MetalabSkein:
	"A class to get metalab for a gcode skein."
	def __init__( self ):
		self.oldLocation = None
		self.output = cStringIO.StringIO()

	def addLine( self, line ):
		"Add a line of text and a newline to the output."
		self.output.write( line + "\n" )

	def addToPath( self, location ):
		"Add a point to travel and maybe extrusion."
		if self.oldLocation != None:
                        self.cornerHigh = euclidean.getPointMaximum( self.cornerHigh, location )
                        self.cornerLow = euclidean.getPointMinimum( self.cornerLow, location )
		self.oldLocation = location

	def getLocationSetFeedrateToSplitLine( self, splitLine ):
		location = gcodec.getLocationFromSplitLine( self.oldLocation, splitLine )
		indexOfF = gcodec.indexOfStartingWithSecond( "F", splitLine )
		if indexOfF > 0:
			self.feedrateMinute = gcodec.getDoubleAfterFirstLetter( splitLine[ indexOfF ] )
		return location

	def helicalMove( self, isCounterclockwise, splitLine ):
		"Get metalab for a helical move."
		if self.oldLocation == None:
			return
		location = self.getLocationSetFeedrateToSplitLine( splitLine )
		location.add( self.oldLocation )
		center = Vec3().getFromVec3( self.oldLocation )
		indexOfR = gcodec.indexOfStartingWithSecond( "R", splitLine )
		if indexOfR > 0:
			radius = gcodec.getDoubleAfterFirstLetter( splitLine[ indexOfR ] )
			halfLocationMinusOld = location.minus( self.oldLocation )
			halfLocationMinusOld.scale( 0.5 )
			halfLocationMinusOldLength = halfLocationMinusOld.length()
			centerMidpointDistance = math.sqrt( radius * radius - halfLocationMinusOldLength * halfLocationMinusOldLength )
			centerMinusMidpoint = euclidean.getRotatedWiddershinsQuarterAroundZAxis( halfLocationMinusOld )
			centerMinusMidpoint.normalize()
			centerMinusMidpoint.scale( centerMidpointDistance )
			if isCounterclockwise:
				center.setToVec3( halfLocationMinusOld.plus( centerMinusMidpoint ) )
			else:
				center.setToVec3( halfLocationMinusOld.minus( centerMinusMidpoint ) )
		else:
			center.x = gcodec.getDoubleForLetter( "I", splitLine )
			center.y = gcodec.getDoubleForLetter( "J", splitLine )
		curveSection = 0.5
		center.add( self.oldLocation )
		afterCenterSegment = location.minus( center )
		beforeCenterSegment = self.oldLocation.minus( center )
		afterCenterDifferenceAngle = euclidean.getAngleAroundZAxisDifference( afterCenterSegment, beforeCenterSegment )
		absoluteDifferenceAngle = abs( afterCenterDifferenceAngle )
		steps = int( round( 0.5 + max( absoluteDifferenceAngle * 2.4, absoluteDifferenceAngle * beforeCenterSegment.length() / curveSection ) ) )
		stepPlaneAngle = euclidean.getPolar( afterCenterDifferenceAngle / steps, 1.0 )
		zIncrement = ( afterCenterSegment.z - beforeCenterSegment.z ) / float( steps )
		for step in range( 1, steps ):
			beforeCenterSegment = euclidean.getRoundZAxisByPlaneAngle( stepPlaneAngle, beforeCenterSegment )
			beforeCenterSegment.z += zIncrement
			arcPoint = center.plus( beforeCenterSegment )
			self.addToPath( arcPoint )
		self.addToPath( location )

	def linearMove( self, splitLine ):
		"Get metalab for a linear move."
		location = self.getLocationSetFeedrateToSplitLine( splitLine )
		self.addToPath( location )

	def parseGcode( self, gcodeText ):
		"Parse gcode text and store the metalab."
		self.cornerHigh = Vec3( - 999999999.0, - 999999999.0, - 999999999.0 )
		self.cornerLow = Vec3( 999999999.0, 999999999.0, 999999999.0 )
		lines = gcodec.getTextLines( gcodeText )
		for line in lines:
			self.parseLine( line )
		halfExtrusionWidth = 0.5 * self.extrusionWidth
		halfExtrusionCorner = Vec3( halfExtrusionWidth, halfExtrusionWidth, halfExtrusionWidth )
		self.cornerLow.subtract( halfExtrusionCorner )
		roundedLow = euclidean.getRoundedPoint( self.cornerLow )

                if roundedLow.x < 0: 
                        self.addLine("Warning: X coordinate is negative!")
                if roundedLow.y < 0: 
                        self.addLine("Warning: Y coordinate is negative!")
                if roundedLow.z < 0: 
                        self.addLine("Error: Z coordinate is negative!")
                        tkMessageBox.showerror('Error', "Negative Z coordinate found!")

	def parseLine( self, line ):
		"Parse a gcode line and add it to the metalab."
		splitLine = line.split( ' ' )
		if len( splitLine ) < 1 or len( line ) < 1:
			return
		firstWord = splitLine[ 0 ]
		if firstWord == 'G1':
			self.linearMove( splitLine )
		elif firstWord == 'G2':
			self.helicalMove( False, splitLine )
		elif firstWord == 'G3':
			self.helicalMove( True, splitLine )
		elif firstWord == '(<extrusionDiameter>':
			self.extrusionDiameter = gcodec.getDoubleAfterFirstLetter( splitLine[ 1 ] )
		elif firstWord == '(<extrusionWidth>':
			self.extrusionWidth = gcodec.getDoubleAfterFirstLetter( splitLine[ 1 ] )
		elif firstWord == '(<extrusionHeight>':
			self.extrusionHeight = gcodec.getDoubleAfterFirstLetter( splitLine[ 1 ] )

class MetalabPreferences:
	"A class to handle the metalab preferences."
	def __init__( self ):
		"Set the default preferences, execute title & preferences filename."
		#Set the default preferences.
		self.archive = []
		self.activateMetalab = preferences.BooleanPreference().getFromValue( 'Activate Metalab', False )
		self.archive.append( self.activateMetalab )
		self.filenameInput = preferences.Filename().getFromFilename( [ ( 'Gcode text files', '*.gcode' ) ], 'Open File to Generate Metalab for', '' )
		self.archive.append( self.filenameInput )
		self.printMetalabFileSkeinforge = preferences.BooleanPreference().getFromValue( 'Print Metalab', False )
		self.archive.append( self.printMetalabFileSkeinforge )
		#Create the archive, title of the execute button, title of the dialog & preferences filename.
		self.executeTitle = 'Generate Metalab'
		self.filenamePreferences = preferences.getPreferencesFilePath( 'metalab.csv' )
		self.filenameHelp = 'skeinforge_tools.analyze_plugins.metalab.html'
		self.saveTitle = 'Save Preferences'
		self.title = 'Metalab Preferences'

	def execute( self ):
		"Write button has been clicked."
		filenames = polyfile.getFileOrGcodeDirectory( self.filenameInput.value, self.filenameInput.wasCancelled )
		for filename in filenames:
			metalabFile( filename )


def main( hashtable = None ):
	"Display the Metalab dialog."
	preferences.displayDialog( MetalabPreferences() )

if __name__ == "__main__":
	main()

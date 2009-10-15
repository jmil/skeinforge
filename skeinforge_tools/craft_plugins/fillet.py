"""
Fillet is a script to fillet or bevel the corners on a gcode file.

The default 'Activate Fillet' checkbox is on.  When it is on, the functions described below will work, when it is off, the functions
will not be called.

Fillet rounds the corners slightly in a variety of ways.  This is to reduce corner blobbing and sudden extruder acceleration.
The 'Arc Point' method fillets the corners with an arc using the gcode point form.  The 'Arc Radius' method fillets with an arc
using the gcode radius form.  The 'Arc Segment' method fillets corners with an arc composed of several segments.  The
'Bevel' method bevels each corner.  The default radio button choice is 'Bevel'.

The 'Corner FeedRate over Operating FeedRate' is the ratio of the feedRate in corners over the operating feedRate.  With a high
value the extruder will move quickly in corners, accelerating quickly and leaving a thin extrusion.  With a low value, the
extruder will move slowly in corners, accelerating gently and leaving a thick extrusion.  The default value is 1.0.  The 'Fillet
Radius over Extrusion Width' ratio determines how much wide the fillet will be, the default is 0.35.  The 'Reversal Slowdown
over Extrusion Width' ratio determines how far before a path reversal the extruder will slow down.  Some tools, like nozzle
wipe, double back the path of the extruder and this option will add a slowdown point in that path so there won't be a sudden
jerk at the end of the path.  The default value is 0.5 and if the value is less than 0.1 a slowdown will not be added.  If
'Use Intermediate FeedRate in Corners' is chosen, the feedRate entering the corner will be the average of the old feedRate and
the new feedRate, the default is true.

The following examples fillet the Screw Holder Bottom.stl.  The examples are run in a terminal in the folder which contains Screw Holder Bottom.stl
and fillet.py.


> python fillet.py
This brings up the fillet dialog.


> python fillet.py Screw Holder Bottom.stl
The fillet tool is parsing the file:
Screw Holder Bottom.stl
..
The fillet tool has created the file:
.. Screw Holder Bottom_fillet.gcode


> python
Python 2.5.1 (r251:54863, Sep 22 2007, 01:43:31)
[GCC 4.2.1 (SUSE Linux)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import fillet
>>> fillet.main()
This brings up the fillet dialog.


>>> fillet.writeOutput()
The fillet tool is parsing the file:
Screw Holder Bottom.stl
..
The fillet tool has created the file:
.. Screw Holder Bottom_fillet.gcode

"""

from __future__ import absolute_import
#Init has to be imported first because it has code to workaround the python bug where relative imports don't work if the module is imported as a main module.
import __init__

from skeinforge_tools import polyfile
from skeinforge_tools.skeinforge_utilities import consecution
from skeinforge_tools.skeinforge_utilities import euclidean
from skeinforge_tools.skeinforge_utilities import gcodec
from skeinforge_tools.skeinforge_utilities import interpret
from skeinforge_tools.skeinforge_utilities import preferences
import math
import sys


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


def arcPointFile( fileName = '' ):
	"Fillet a gcode linear move file into a helical point move file.  If no fileName is specified, arc point the first unmodified gcode file in this folder."
	if fileName == '':
		unmodified = gcodec.getUnmodifiedGCodeFiles()
		if len( unmodified ) == 0:
			print( "There are no unmodified gcode files in this folder." )
			return
		fileName = unmodified[ 0 ]
	filletPreferences = FilletPreferences()
	preferences.getReadPreferences( filletPreferences )
	print( 'File ' + gcodec.getSummarizedFilename( fileName ) + ' is being filleted into arc points.' )
	gcodeText = gcodec.getFileText( fileName )
	if gcodeText == '':
		return
	gcodec.writeFileMessageSuffix( fileName, getArcPointGcode( filletPreferences, gcodeText ), 'The arc point file is saved as ', '_fillet' )

def arcRadiusFile( fileName = '' ):
	"Fillet a gcode linear move file into a helical radius move file.  If no fileName is specified, arc radius the first unmodified gcode file in this folder."
	if fileName == '':
		unmodified = gcodec.getUnmodifiedGCodeFiles()
		if len( unmodified ) == 0:
			print( "There are no unmodified gcode files in this folder." )
			return
		fileName = unmodified[ 0 ]
	filletPreferences = FilletPreferences()
	preferences.getReadPreferences( filletPreferences )
	print( 'File ' + gcodec.getSummarizedFilename( fileName ) + ' is being filleted into arc radiuses.' )
	gcodeText = gcodec.getFileText( fileName )
	if gcodeText == '':
		return
	gcodec.writeFileMessageSuffix( fileName, getArcRadiusGcode( filletPreferences, gcodeText ), 'The arc radius file is saved as ', '_fillet' )

def arcSegmentFile( fileName = '' ):
	"Fillet a gcode linear move file into an arc segment linear move file.  If no fileName is specified, arc segment the first unmodified gcode file in this folder."
	if fileName == '':
		unmodified = gcodec.getUnmodifiedGCodeFiles()
		if len( unmodified ) == 0:
			print( "There are no unmodified gcode files in this folder." )
			return
		fileName = unmodified[ 0 ]
	filletPreferences = FilletPreferences()
	preferences.getReadPreferences( filletPreferences )
	print( 'File ' + gcodec.getSummarizedFilename( fileName ) + ' is being arc segmented.' )
	gcodeText = gcodec.getFileText( fileName )
	if gcodeText == '':
		return
	gcodec.writeFileMessageSuffix( fileName, getArcSegmentGcode( filletPreferences, gcodeText ), 'The arc segment file is saved as ', '_fillet' )

def bevelFile( fileName = '' ):
	"Bevel a gcode linear move file.  If no fileName is specified, bevel the first unmodified gcode file in this folder."
	if fileName == '':
		unmodified = gcodec.getUnmodifiedGCodeFiles()
		if len( unmodified ) == 0:
			print( "There are no unmodified gcode files in this folder." )
			return
		fileName = unmodified[ 0 ]
	filletPreferences = FilletPreferences()
	preferences.getReadPreferences( filletPreferences )
	print( 'File ' + gcodec.getSummarizedFilename( fileName ) + ' is being beveled.' )
	gcodeText = gcodec.getFileText( fileName )
	if gcodeText == '':
		return
	gcodec.writeFileMessageSuffix( fileName, getBevelGcode( filletPreferences, gcodeText ), 'The beveled file is saved as ', '_fillet' )

def getArcPointGcode( filletPreferences, gcodeText ):
	"Arc point a gcode linear move text into a helical point move gcode text."
	return ArcPointSkein().getCraftedGcode( filletPreferences, gcodeText )

def getArcRadiusGcode( filletPreferences, gcodeText ):
	"Arc radius a gcode linear move text into a helical radius move gcode text."
	return ArcRadiusSkein().getCraftedGcode( filletPreferences, gcodeText )

def getArcSegmentGcode( filletPreferences, gcodeText ):
	"Arc segment a gcode linear move text into an arc segment linear move gcode text."
	return ArcSegmentSkein().getCraftedGcode( filletPreferences, gcodeText )

def getBevelGcode( filletPreferences, gcodeText ):
	"Bevel a gcode linear move text."
	return BevelSkein().getCraftedGcode( filletPreferences, gcodeText )

def getCraftedText( fileName, text, filletPreferences = None ):
	"Fillet a gcode linear move file or text."
	return getCraftedTextFromText( gcodec.getTextIfEmpty( fileName, text ), filletPreferences )

def getCraftedTextFromText( gcodeText, filletPreferences = None ):
	"Fillet a gcode linear move text."
	if gcodec.isProcedureDoneOrFileIsEmpty( gcodeText, 'fillet' ):
		return gcodeText
	if filletPreferences == None:
		filletPreferences = preferences.getReadPreferences( FilletPreferences() )
	if not filletPreferences.activateFillet.value:
		return gcodeText
	if filletPreferences.arcPoint.value:
		return getArcPointGcode( filletPreferences, gcodeText )
	elif filletPreferences.arcRadius.value:
		return getArcRadiusGcode( filletPreferences, gcodeText )
	elif filletPreferences.arcSegment.value:
		return getArcSegmentGcode( filletPreferences, gcodeText )
	elif filletPreferences.bevel.value:
		return getBevelGcode( filletPreferences, gcodeText )
	return gcodeText

def getPreferencesConstructor():
	"Get the preferences constructor."
	return FilletPreferences()

def writeOutput( fileName = '' ):
	"Fillet a gcode linear move file. Depending on the preferences, either arcPoint, arcRadius, arcSegment, bevel or do nothing."
	fileName = interpret.getFirstTranslatorFileNameUnmodified( fileName )
	if fileName != '':
		consecution.writeChainTextWithNounMessage( fileName, 'fillet' )


class BevelSkein:
	"A class to bevel a skein of extrusions."
	def __init__( self ):
		self.distanceFeedRate = gcodec.DistanceFeedRate()
		self.extruderActive = False
		self.feedRateMinute = 960.0
		self.filletRadius = 0.2
		self.lineIndex = 0
		self.lines = None
		self.oldFeedRateMinute = None
		self.oldLocation = None
		self.shouldAddLine = True

	def addLinearMovePoint( self, feedRateMinute, point ):
		"Add a gcode linear move, feedRate and newline to the output."
		self.distanceFeedRate.addLine( self.distanceFeedRate.getLinearGcodeMovementWithFeedRate( feedRateMinute, point.dropAxis( 2 ), point.z ) )

	def getCornerFeedRate( self ):
		"Get the corner feedRate, which may be based on the intermediate feedRate."
		feedRateMinute = self.feedRateMinute
		if self.filletPreferences.useIntermediateFeedRateInCorners.value:
			if self.oldFeedRateMinute != None:
				feedRateMinute = 0.5 * ( self.oldFeedRateMinute + self.feedRateMinute )
		return feedRateMinute * self.cornerFeedRateOverOperatingFeedRate

	def getCraftedGcode( self, filletPreferences, gcodeText ):
		"Parse gcode text and store the bevel gcode."
		self.cornerFeedRateOverOperatingFeedRate = filletPreferences.cornerFeedRateOverOperatingFeedRate.value
		self.lines = gcodec.getTextLines( gcodeText )
		self.filletPreferences = filletPreferences
		self.parseInitialization( filletPreferences )
		for self.lineIndex in xrange( self.lineIndex, len( self.lines ) ):
			line = self.lines[ self.lineIndex ]
			self.parseLine( line )
		return self.distanceFeedRate.output.getvalue()

	def getExtruderOffReversalPoint( self, afterSegment, beforeSegment, location ):
		"If the extruder is off and the path is reversing, add intermediate slow points."
		if self.reversalSlowdownDistance < 0.1:
			return None
		reversalBufferSlowdownDistance = self.reversalSlowdownDistance * 1.2
		if afterSegment.magnitude() < reversalBufferSlowdownDistance:
			return None
		if beforeSegment.magnitude() < reversalBufferSlowdownDistance:
			return None
		afterSegmentNormalized = afterSegment / afterSegment.magnitude()
		beforeSegmentNormalized = beforeSegment / beforeSegment.magnitude()
		planeDot = euclidean.getPlaneDot( beforeSegmentNormalized, afterSegmentNormalized )
		if self.extruderActive:
			return None
		if planeDot < 0.95:
			return None
		slowdownFeedRate = self.feedRateMinute * 0.333333333
		self.shouldAddLine = False
		beforePoint = euclidean.getPointPlusSegmentWithLength( self.reversalSlowdownDistance, location, beforeSegment )
		self.addLinearMovePoint( self.feedRateMinute, beforePoint )
		self.addLinearMovePoint( slowdownFeedRate, location )
		afterPoint = euclidean.getPointPlusSegmentWithLength( self.reversalSlowdownDistance, location, afterSegment )
		self.addLinearMovePoint( slowdownFeedRate, afterPoint )
		return afterPoint

	def getNextLocation( self ):
		"Get the next linear move.  Return none is none is found."
		for afterIndex in xrange( self.lineIndex + 1, len( self.lines ) ):
			line = self.lines[ afterIndex ]
			splitLine = line.split( ' ' )
			if gcodec.getFirstWord( splitLine ) == 'G1':
				nextLocation = gcodec.getLocationFromSplitLine( self.oldLocation, splitLine )
				return nextLocation
		return None

	def linearMove( self, splitLine ):
		"Bevel a linear move."
		location = gcodec.getLocationFromSplitLine( self.oldLocation, splitLine )
		self.feedRateMinute = gcodec.getFeedRateMinute( self.feedRateMinute, splitLine )
		if self.oldLocation != None:
			nextLocation = self.getNextLocation()
			if nextLocation != None:
				location = self.splitPointGetAfter( location, nextLocation )
		self.oldLocation = location
		self.oldFeedRateMinute = self.feedRateMinute

	def parseInitialization( self, filletPreferences ):
		"Parse gcode initialization and store the parameters."
		for self.lineIndex in xrange( len( self.lines ) ):
			line = self.lines[ self.lineIndex ]
			splitLine = line.split()
			firstWord = gcodec.getFirstWord( splitLine )
			self.distanceFeedRate.parseSplitLine( firstWord, splitLine )
			if firstWord == '(</extruderInitialization>)':
				self.distanceFeedRate.addLine( '(<procedureDone> fillet </procedureDone>)' )
				return
			elif firstWord == '(<perimeterWidth>':
				absoluteExtrusionWidth = abs( float( splitLine[ 1 ] ) )
				self.reversalSlowdownDistance = absoluteExtrusionWidth * filletPreferences.reversalSlowdownDistanceOverExtrusionWidth.value
				self.filletRadius = absoluteExtrusionWidth * filletPreferences.filletRadiusOverExtrusionWidth.value
			self.distanceFeedRate.addLine( line )

	def parseLine( self, line ):
		"Parse a gcode line and add it to the bevel gcode."
		self.shouldAddLine = True
		splitLine = line.split()
		if len( splitLine ) < 1:
			return
		firstWord = splitLine[ 0 ]
		if firstWord == 'G1':
			self.linearMove( splitLine )
		elif firstWord == 'M101':
			self.extruderActive = True
		elif firstWord == 'M103':
			self.extruderActive = False
		if self.shouldAddLine:
			self.distanceFeedRate.addLine( line )

	def splitPointGetAfter( self, location, nextLocation ):
		"Bevel a point and return the end of the bevel."
		bevelLength = 0.5 * self.filletRadius
		beforeSegment = self.oldLocation - location
		halfBeforeSegmentLength = 0.5 * beforeSegment.magnitude()
		if halfBeforeSegmentLength <= 0.0:
			return location
		afterSegment = nextLocation - location
		afterSegmentExtension = 0.333 * afterSegment.magnitude()
		if afterSegmentExtension <= 0.0:
			return location
		extruderOffReversalPoint = self.getExtruderOffReversalPoint( afterSegment, beforeSegment, location )
		if extruderOffReversalPoint != None:
			return extruderOffReversalPoint
		bevelLength = min( afterSegmentExtension, bevelLength )
		self.shouldAddLine = False
		if halfBeforeSegmentLength < bevelLength:
			bevelLength = halfBeforeSegmentLength
		else:
			beforePoint = euclidean.getPointPlusSegmentWithLength( bevelLength, location, beforeSegment )
			self.addLinearMovePoint( self.getCornerFeedRate(), beforePoint )
		afterPoint = euclidean.getPointPlusSegmentWithLength( bevelLength, location, afterSegment )
		self.addLinearMovePoint( self.feedRateMinute, afterPoint )
		return afterPoint


class ArcSegmentSkein( BevelSkein ):
	"A class to arc segment a skein of extrusions."
	def addArc( self, afterCenterDifferenceAngle, afterPoint, beforeCenterSegment, beforePoint, center ):
		"Add arc segments to the filleted skein."
		curveSection = 0.5
		absoluteDifferenceAngle = abs( afterCenterDifferenceAngle )
		steps = int( math.ceil( max( absoluteDifferenceAngle * 2.4, absoluteDifferenceAngle * abs( beforeCenterSegment ) / curveSection ) ) )
		stepPlaneAngle = euclidean.getPolar( afterCenterDifferenceAngle / steps, 1.0 )
		for step in xrange( 1, steps ):
			beforeCenterSegment = euclidean.getRoundZAxisByPlaneAngle( stepPlaneAngle, beforeCenterSegment )
			arcPoint = center + beforeCenterSegment
			self.addLinearMovePoint( self.getCornerFeedRate(), arcPoint )
		self.addLinearMovePoint( self.getCornerFeedRate(), afterPoint )

	def splitPointGetAfter( self, location, nextLocation ):
		"Fillet a point into arc segments and return the end of the last segment."
		afterSegment = nextLocation - location
		afterSegmentLength = afterSegment.magnitude()
		afterSegmentExtension = 0.5 * afterSegmentLength
		if afterSegmentExtension == 0.0:
			return location
		beforeSegment = self.oldLocation - location
		beforeSegmentLength = beforeSegment.magnitude()
		if beforeSegmentLength == 0.0:
			return location
		radius = self.filletRadius
		afterSegmentNormalized = afterSegment / afterSegmentLength
		beforeSegmentNormalized = beforeSegment / beforeSegmentLength
		betweenCenterDotNormalized = afterSegmentNormalized + beforeSegmentNormalized
		if betweenCenterDotNormalized.magnitude() < 0.01 * self.filletRadius:
			return location
		extruderOffReversalPoint = self.getExtruderOffReversalPoint( afterSegment, beforeSegment, location )
		if extruderOffReversalPoint != None:
			return extruderOffReversalPoint
		betweenCenterDotNormalized.normalize()
		beforeSegmentNormalizedWiddershins = euclidean.getRotatedWiddershinsQuarterAroundZAxis( beforeSegmentNormalized )
		betweenAfterPlaneDot = abs( euclidean.getPlaneDot( betweenCenterDotNormalized, beforeSegmentNormalizedWiddershins ) )
		if betweenAfterPlaneDot <= 0.0:
			return nextLocation
		centerDotDistance = radius / betweenAfterPlaneDot
		bevelLength = math.sqrt( centerDotDistance * centerDotDistance - radius * radius )
		radiusOverBevelLength = radius / bevelLength
		bevelLength = min( bevelLength, radius )
		bevelLength = min( afterSegmentExtension, bevelLength )
		beforePoint = self.oldLocation
		if beforeSegmentLength < bevelLength:
			bevelLength = beforeSegmentLength
		else:
			beforePoint = euclidean.getPointPlusSegmentWithLength( bevelLength, location, beforeSegment )
			self.addLinearMovePoint( self.feedRateMinute, beforePoint )
		self.shouldAddLine = False
		afterPoint = euclidean.getPointPlusSegmentWithLength( bevelLength, location, afterSegment )
		radius = bevelLength * radiusOverBevelLength
		centerDotDistance = radius / betweenAfterPlaneDot
		center = location + betweenCenterDotNormalized * centerDotDistance
		afterCenterSegment = afterPoint - center
		beforeCenterSegment = beforePoint - center
		afterCenterDifferenceAngle = euclidean.getAngleAroundZAxisDifference( afterCenterSegment, beforeCenterSegment )
		if afterCenterDifferenceAngle <= 0.0:
			self.addLinearMovePoint( self.getCornerFeedRate(), afterPoint )
			return afterPoint
		self.addArc( afterCenterDifferenceAngle, afterPoint, beforeCenterSegment, beforePoint, center )
		return afterPoint


class ArcPointSkein( ArcSegmentSkein ):
	"A class to arc point a skein of extrusions."
	def addArc( self, afterCenterDifferenceAngle, afterPoint, beforeCenterSegment, beforePoint, center ):
		"Add an arc point to the filleted skein."
		afterPointMinusBefore = afterPoint - beforePoint
		centerMinusBefore = center - beforePoint
		firstWord = 'G3'
		if afterCenterDifferenceAngle < 0.0:
			firstWord = 'G2'
		centerMinusBeforeComplex = centerMinusBefore.dropAxis( 2 )
		if abs( centerMinusBeforeComplex ) <= 0.0:
			return
		self.distanceFeedRate.output.write( self.distanceFeedRate.getFirstWordMovement( firstWord, afterPointMinusBefore ) )
		self.distanceFeedRate.output.write( self.getRelativeCenter( centerMinusBeforeComplex ) )
		self.distanceFeedRate.addLine( self.distanceFeedRate.getArcFeedRateString( afterCenterDifferenceAngle, afterPointMinusBefore, centerMinusBefore, self.getCornerFeedRate() ) )

	def getRelativeCenter( self, centerMinusBeforeComplex ):
		"Get the relative center."
		return ' I%s J%s' % ( self.distanceFeedRate.getRounded( centerMinusBeforeComplex.real ), self.distanceFeedRate.getRounded( centerMinusBeforeComplex.imag ) )


class ArcRadiusSkein( ArcPointSkein ):
	"A class to arc radius a skein of extrusions."
	def getRelativeCenter( self, centerMinusBeforeComplex ):
		"Get the relative center."
		radius = abs( centerMinusBeforeComplex )
		return ' R' + ( self.distanceFeedRate.getRounded( radius ) )


class FilletPreferences:
	"A class to handle the fillet preferences."
	def __init__( self ):
		"Set the default preferences, execute title & preferences fileName."
		#Set the default preferences.
		self.archive = []
		self.activateFillet = preferences.BooleanPreference().getFromValue( 'Activate Fillet', True )
		self.archive.append( self.activateFillet )
		self.filletProcedureChoiceLabel = preferences.LabelDisplay().getFromName( 'Fillet Procedure Choice: ' )
		self.archive.append( self.filletProcedureChoiceLabel )
		filletRadio = []
		self.arcPoint = preferences.Radio().getFromRadio( 'Arc Point', filletRadio, False )
		self.archive.append( self.arcPoint )
		self.arcRadius = preferences.Radio().getFromRadio( 'Arc Radius', filletRadio, False )
		self.archive.append( self.arcRadius )
		self.arcSegment = preferences.Radio().getFromRadio( 'Arc Segment', filletRadio, False )
		self.archive.append( self.arcSegment )
		self.bevel = preferences.Radio().getFromRadio( 'Bevel', filletRadio, True )
		self.archive.append( self.bevel )
		self.cornerFeedRateOverOperatingFeedRate = preferences.FloatPreference().getFromValue( 'Corner FeedRate over Operating FeedRate (ratio):', 1.0 )
		self.archive.append( self.cornerFeedRateOverOperatingFeedRate )
		self.filletRadiusOverExtrusionWidth = preferences.FloatPreference().getFromValue( 'Fillet Radius over Extrusion Width (ratio):', 0.35 )
		self.archive.append( self.filletRadiusOverExtrusionWidth )
		self.fileNameInput = preferences.Filename().getFromFilename( interpret.getGNUTranslatorGcodeFileTypeTuples(), 'Open File to be Filleted', '' )
		self.archive.append( self.fileNameInput )
		self.reversalSlowdownDistanceOverExtrusionWidth = preferences.FloatPreference().getFromValue( 'Reversal Slowdown Distance over Extrusion Width (ratio):', 0.5 )
		self.archive.append( self.reversalSlowdownDistanceOverExtrusionWidth )
		self.useIntermediateFeedRateInCorners = preferences.BooleanPreference().getFromValue( 'Use Intermediate FeedRate in Corners', True )
		self.archive.append( self.useIntermediateFeedRateInCorners )
		#Create the archive, title of the execute button, title of the dialog & preferences fileName.
		self.executeTitle = 'Fillet'
		self.saveCloseTitle = 'Save and Close'
		preferences.setHelpPreferencesFileNameTitleWindowPosition( self, 'skeinforge_tools.craft_plugins.fillet.html' )

	def execute( self ):
		"Fillet button has been clicked."
		fileNames = polyfile.getFileOrDirectoryTypesUnmodifiedGcode( self.fileNameInput.value, interpret.getImportPluginFilenames(), self.fileNameInput.wasCancelled )
		for fileName in fileNames:
			writeOutput( fileName )


def main():
	"Display the fillet dialog."
	if len( sys.argv ) > 1:
		writeOutput( ' '.join( sys.argv[ 1 : ] ) )
	else:
		preferences.startMainLoopFromConstructor( getPreferencesConstructor() )

if __name__ == "__main__":
	main()

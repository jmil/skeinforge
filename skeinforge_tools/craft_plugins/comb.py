"""
Comb is a script to comb the extrusion hair of a gcode file.

The default 'Activate Comb' checkbox is on.  When it is on, the functions described below will work, when it is off, the functions
will not be called.

Comb bends the extruder travel paths around holes in the carve, to avoid stringers.  It moves the extruder to the inside of outer
perimeters before turning the extruder on so any start up ooze will be inside the shape.  It jitters the loop end position to a
different place on each layer to prevent the a ridge from forming.  The 'Arrival Inset Follow Distance over Extrusion Width' is the
ratio of the amount before the start of the outer perimeter the extruder will be moved to.  A high value means the extruder will
move way before the beginning of the perimeter and a low value means the extruder will be moved just before the beginning.
The "Jitter Over Extrusion Width (ratio)" is the ratio of the amount the loop ends will be jittered.  A high value means the loops
will start all over the place and a low value means loops will start at roughly the same place on each layer.  The 'Minimum
Perimeter Departure Distance over Extrusion Width' is the ratio of the minimum distance that the extruder will travel and loop
before leaving an outer perimeter.  A high value means the extruder will loop many times before leaving, so that the ooze will
finish within the perimeter, a low value means the extruder will not loop and a stringer might be created from the outer
perimeter.

The following examples comb the Screw Holder Bottom.stl.  The examples are run in a terminal in the folder which contains Screw Holder Bottom.stl
and comb.py.


> python comb.py
This brings up the comb dialog.


> python comb.py Screw Holder Bottom.stl
The comb tool is parsing the file:
Screw Holder Bottom.stl
..
The comb tool has created the file:
.. Screw Holder Bottom_comb.gcode


> python
Python 2.5.1 (r251:54863, Sep 22 2007, 01:43:31)
[GCC 4.2.1 (SUSE Linux)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import comb
>>> comb.main()
This brings up the comb dialog.


>>> comb.writeOutput()
The comb tool is parsing the file:
Screw Holder Bottom.stl
..
The comb tool has created the file:
.. Screw Holder Bottom_comb.gcode

"""

from __future__ import absolute_import
#Init has to be imported first because it has code to workaround the python bug where relative imports don't work if the module is imported as a main module.
import __init__

from skeinforge_tools.skeinforge_utilities import consecution
from skeinforge_tools.skeinforge_utilities import euclidean
from skeinforge_tools.skeinforge_utilities import gcodec
from skeinforge_tools.skeinforge_utilities import intercircle
from skeinforge_tools.skeinforge_utilities import interpret
from skeinforge_tools.skeinforge_utilities import preferences
from skeinforge_tools import polyfile
import math
import sys


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"

#patched over falling tower comb bug if location.z < self.getBetweens()[ 0 ][ 0 ].z + 0.5 * self.perimeterWidth, but a real solution would be nice
#addLoopsBeforeLeavingPerimeter or something before crossing bug, seen on layer 8 of Screw holder
def getCraftedText( fileName, text, combPreferences = None ):
	"Comb a gcode linear move text."
	return getCraftedTextFromText( gcodec.getTextIfEmpty( fileName, text ), combPreferences )

def getCraftedTextFromText( gcodeText, combPreferences = None ):
	"Comb a gcode linear move text."
	if gcodec.isProcedureDoneOrFileIsEmpty( gcodeText, 'comb' ):
		return gcodeText
	if combPreferences == None:
		combPreferences = preferences.getReadPreferences( CombPreferences() )
	if not combPreferences.activateComb.value:
		return gcodeText
	return CombSkein().getCraftedGcode( combPreferences, gcodeText )

def getPreferencesConstructor():
	"Get the preferences constructor."
	return CombPreferences()

def isLoopNumberEqual( betweenX, betweenXIndex, loopNumber ):
	"Determine if the loop number is equal."
	if betweenXIndex >= len( betweenX ):
		return False
	return betweenX[ betweenXIndex ].index == loopNumber

def writeOutput( fileName = '' ):
	"Comb a gcode linear move file."
	fileName = interpret.getFirstTranslatorFileNameUnmodified( fileName )
	if fileName != '':
		consecution.writeChainTextWithNounMessage( fileName, 'comb' )


class CombPreferences:
	"A class to handle the comb preferences."
	def __init__( self ):
		"Set the default preferences, execute title & preferences fileName."
		#Set the default preferences.
		self.archive = []
		self.activateComb = preferences.BooleanPreference().getFromValue( 'Activate Comb', True )
		self.archive.append( self.activateComb )
		self.arrivalInsetFollowDistanceOverExtrusionWidth = preferences.FloatPreference().getFromValue( 'Arrival Inset Follow Distance over Extrusion Width (ratio):', 3.0 )
		self.archive.append( self.arrivalInsetFollowDistanceOverExtrusionWidth )
		self.jitterOverExtrusionWidth = preferences.FloatPreference().getFromValue( 'Jitter Over Extrusion Width (ratio):', 2.0 )
		self.archive.append( self.jitterOverExtrusionWidth )
		self.minimumPerimeterDepartureDistanceOverExtrusionWidth = preferences.FloatPreference().getFromValue( 'Minimum Perimeter Departure Distance over Extrusion Width (ratio):', 30.0 )
		self.archive.append( self.minimumPerimeterDepartureDistanceOverExtrusionWidth )
		self.fileNameInput = preferences.Filename().getFromFilename( interpret.getGNUTranslatorGcodeFileTypeTuples(), 'Open File to be Combed', '' )
		self.archive.append( self.fileNameInput )
		#Create the archive, title of the execute button, title of the dialog & preferences fileName.
		self.executeTitle = 'Comb'
		self.saveCloseTitle = 'Save and Close'
		preferences.setHelpPreferencesFileNameTitleWindowPosition( self, 'skeinforge_tools.craft_plugins.comb.html' )

	def execute( self ):
		"Comb button has been clicked."
		fileNames = polyfile.getFileOrDirectoryTypesUnmodifiedGcode( self.fileNameInput.value, interpret.getImportPluginFilenames(), self.fileNameInput.wasCancelled )
		for fileName in fileNames:
			writeOutput( fileName )


class CombSkein:
	"A class to comb a skein of extrusions."
	def __init__( self ):
		self.beforeLoopLocation = None
		self.betweenTable = {}
		self.boundaryLoop = None
		self.distanceFeedRate = gcodec.DistanceFeedRate()
		self.isPerimeter = False
		self.layer = None
		self.layers = []
		self.layerTable = {}
		self.layerZ = None
		self.lineIndex = 0
		self.lines = None
		self.nextLayerZ = None
		self.oldZ = None
		self.perimeter = None
		self.pointTable = {}
		self.initializeMoreParameters()

	def addGcodeFromThreadZ( self, thread, z ):
		"Add a gcode thread to the output."
		if len( thread ) > 0:
			self.addGcodeMovementZ( self.travelFeedRatePerMinute, thread[ 0 ], z )
		else:
			print( "zero length vertex positions array which was skipped over, this should never happen" )
		if len( thread ) < 2:
			return
		self.distanceFeedRate.addLine( 'M101' )
		self.addGcodePathZ( self.feedRateMinute, thread[ 1 : ], z )

	def addGcodeMovementZ( self, feedRateMinute, point, z ):
		"Add a movement to the output."
		if feedRateMinute == None:
			feedRateMinute = self.operatingFeedRatePerMinute
		self.distanceFeedRate.addGcodeMovementZWithFeedRate( feedRateMinute, point, z )

	def addGcodePathZ( self, feedRateMinute, path, z ):
		"Add a gcode path, without modifying the extruder, to the output."
		for point in path:
			self.addGcodeMovementZ( feedRateMinute, point, z )

	def addIfTravel( self, splitLine ):
		"Add travel move around loops if the extruder is off."
		location = gcodec.getLocationFromSplitLine( self.oldLocation, splitLine )
		if not self.extruderActive and self.oldLocation != None:
			if len( self.getBetweens() ) > 0:
				highestZ = max( location.z, self.oldLocation.z )
				self.addGcodePathZ( self.travelFeedRatePerMinute, self.getAroundBetweenPath( location ), highestZ )
		self.oldLocation = location

	def addPathBeforeEnd( self, aroundBetweenPath, location, loop ):
		"Add the path before the end of the loop."
		if self.arrivalInsetFollowDistance < self.lessThanFillInset:
			return
		slightlyMoreThanLessThanFillInset = 1.01 * self.lessThanFillInset
		muchGreaterThanLessThanFillInset = 2.5 * self.lessThanFillInset
		locationComplex = location.dropAxis( 2 )
		closestInset = None
		closestDistanceIndex = euclidean.DistanceIndex( 999999999999999999.0, - 1 )
		loop = euclidean.getAwayPoints( loop, self.perimeterWidth )
		circleNodes = intercircle.getCircleNodesFromLoop( loop, slightlyMoreThanLessThanFillInset )
		centers = []
		centers = intercircle.getCentersFromCircleNodes( circleNodes )
		for center in centers:
			inset = intercircle.getInsetFromClockwiseLoop( center, self.lessThanFillInset )
			if intercircle.isLargeSameDirection( inset, center, muchGreaterThanLessThanFillInset ):
				if euclidean.isPathInsideLoop( loop, inset ) == euclidean.isWiddershins( loop ):
					distanceIndex = euclidean.getNearestDistanceIndex( locationComplex, inset )
					if distanceIndex.distance < closestDistanceIndex.distance:
						closestInset = inset
						closestDistanceIndex = distanceIndex
		if closestInset == None:
			return
		perimeterHalfWidth = 0.5 * self.perimeterWidth
		closestInset = euclidean.getLoopStartingNearest( perimeterHalfWidth, locationComplex, closestInset )
		if euclidean.getPolygonLength( closestInset ) < 0.2 * self.arrivalInsetFollowDistance:
			return
		closestInset.append( closestInset[ 0 ] )
		closestInset = euclidean.getSimplifiedPath( closestInset, self.perimeterWidth )
		closestInset.reverse()
		pathBeforeArrival = euclidean.getClippedAtEndLoopPath( self.arrivalInsetFollowDistance, closestInset )
		pointBeforeArrival = pathBeforeArrival[ - 1 ]
		aroundBetweenPath.append( pointBeforeArrival )
		if self.arrivalInsetFollowDistance <= self.lessThanFillInset:
			return
		aroundBetweenPath += euclidean.getClippedAtEndLoopPath( self.lessThanFillInset, closestInset )[ len( pathBeforeArrival ) - 1 : ]

	def addPathBetween( self, aroundBetweenPath, betweenFirst, betweenSecond, isLeavingPerimeter, loopFirst ):
		"Add a path between the perimeter and the fill."
		clockwisePath = [ betweenFirst ]
		widdershinsPath = [ betweenFirst ]
		nearestFirstDistanceIndex = euclidean.getNearestDistanceIndex( betweenFirst, loopFirst )
		nearestSecondDistanceIndex = euclidean.getNearestDistanceIndex( betweenSecond, loopFirst )
		firstBeginIndex = ( nearestFirstDistanceIndex.index + 1 ) % len( loopFirst )
		secondBeginIndex = ( nearestSecondDistanceIndex.index + 1 ) % len( loopFirst )
		loopBeforeLeaving = euclidean.getAroundLoop( firstBeginIndex, firstBeginIndex, loopFirst )
		if nearestFirstDistanceIndex.index == nearestSecondDistanceIndex.index:
			nearestPoint = euclidean.getNearestPointOnSegment( loopFirst[ nearestSecondDistanceIndex.index ], loopFirst[ secondBeginIndex ], betweenSecond )
			widdershinsPath += [ nearestPoint ]
			clockwisePath += [ nearestPoint ]
			if euclidean.getPathLength( widdershinsPath ) < self.minimumPerimeterDepartureDistance:
				widdershinsPath = [ betweenFirst ] + loopBeforeLeaving + [ nearestPoint ]
				reversedLoop = loopBeforeLeaving[ : ]
				reversedLoop.reverse()
				clockwisePath = [ betweenFirst ] + reversedLoop + [ nearestPoint ]
		else:
			widdershinsLoop = euclidean.getAroundLoop( firstBeginIndex, secondBeginIndex, loopFirst )
			widdershinsPath += widdershinsLoop
			clockwiseLoop = euclidean.getAroundLoop( secondBeginIndex, firstBeginIndex, loopFirst )
			clockwiseLoop.reverse()
			clockwisePath += clockwiseLoop
			clockwisePath.append( betweenSecond )
			widdershinsPath.append( betweenSecond )
		if euclidean.getPathLength( widdershinsPath ) > euclidean.getPathLength( clockwisePath ):
			loopBeforeLeaving.reverse()
			widdershinsPath = clockwisePath
		if isLeavingPerimeter:
			totalDistance = euclidean.getPathLength( widdershinsPath )
			loopLength = euclidean.getPolygonLength( loopBeforeLeaving )
			while totalDistance < self.minimumPerimeterDepartureDistance:
				widdershinsPath = [ betweenFirst ] + loopBeforeLeaving + widdershinsPath[ 1 : ]
				totalDistance += loopLength
		aroundBetweenPath += widdershinsPath

	def addTailoredLoopPath( self ):
		"Add a clipped and jittered loop path."
		loop = self.loopPath.path[ : - 1 ]
		jitterDistance = self.layerJitter + self.arrivalInsetFollowDistance
		if self.beforeLoopLocation != None:
			perimeterHalfWidth = 0.5 * self.perimeterWidth
			loop = euclidean.getLoopStartingNearest( perimeterHalfWidth, self.beforeLoopLocation, loop )
		if jitterDistance != 0.0:
			loop = self.getJitteredLoop( jitterDistance, loop )
			loop = euclidean.getAwayPoints( loop, 0.2 * self.perimeterWidth )
		self.loopPath.path = loop + [ loop[ 0 ] ]
		self.addGcodeFromThreadZ( self.loopPath.path, self.loopPath.z )
		self.loopPath = None

	def addToLoop( self, location ):
		"Add a location to loop."
		if self.layer == None:
			if not self.oldZ in self.layerTable:
				self.layerTable[ self.oldZ ] = []
			self.layer = self.layerTable[ self.oldZ ]
		if self.boundaryLoop == None:
			self.boundaryLoop = [] #starting with an empty array because a closed loop does not have to restate its beginning
			self.layer.append( self.boundaryLoop )
		if self.boundaryLoop != None:
			self.boundaryLoop.append( location.dropAxis( 2 ) )

	def getAroundBetweenPath( self, location ):
		"Insert paths around and between the perimeter and the fill."
		aroundBetweenPath = []
		outerPerimeter = None
		if str( location ) in self.pointTable:
			perimeter = self.pointTable[ str( location ) ]
			if euclidean.isWiddershins( perimeter ):
				outerPerimeter = perimeter
		nextBeginning = self.getOutloopLocation( location )
		pathEnd = self.getOutloopLocation( self.oldLocation )
		self.insertPathsBetween( aroundBetweenPath, nextBeginning, pathEnd )
		if outerPerimeter != None:
			self.addPathBeforeEnd( aroundBetweenPath, location, outerPerimeter )
		return aroundBetweenPath

	def getBetweens( self ):
		"Set betweens for the layer."
		if self.layerZ in self.betweenTable:
			return self.betweenTable[ self.layerZ ]
		if self.layerZ not in self.layerTable:
			return []
		self.betweenTable[ self.layerZ ] = []
		for boundaryLoop in self.layerTable[ self.layerZ ]:
			self.betweenTable[ self.layerZ ] += intercircle.getInsetLoopsFromLoop( self.lessThanFillInset, boundaryLoop )
		return self.betweenTable[ self.layerZ ]

	def getCraftedGcode( self, combPreferences, gcodeText ):
		"Parse gcode text and store the comb gcode."
		self.lines = gcodec.getTextLines( gcodeText )
		self.parseInitialization( combPreferences )
		for self.lineIndex in xrange( self.lineIndex, len( self.lines ) ):
			line = self.lines[ self.lineIndex ]
			self.parseAddJitter( line )
		self.lines = gcodec.getTextLines( self.distanceFeedRate.output.getvalue() )
		self.initializeMoreParameters()
		for self.lineIndex in xrange( len( self.lines ) ):
			line = self.lines[ self.lineIndex ]
			self.parseLine( combPreferences, line )
		for self.lineIndex in xrange( len( self.lines ) ):
			line = self.lines[ self.lineIndex ]
			self.parseAddTravel( line )
		return self.distanceFeedRate.output.getvalue()

	def getJitteredLoop( self, jitterDistance, jitterLoop ):
		"Get a jittered loop path."
		loopLength = euclidean.getPolygonLength( jitterLoop )
		lastLength = 0.0
		pointIndex = 0
		totalLength = 0.0
		jitterPosition = ( jitterDistance + 256.0 * loopLength ) % loopLength
		while totalLength < jitterPosition and pointIndex < len( jitterLoop ):
			firstPoint = jitterLoop[ pointIndex ]
			secondPoint  = jitterLoop[ ( pointIndex + 1 ) % len( jitterLoop ) ]
			pointIndex += 1
			lastLength = totalLength
			totalLength += abs( firstPoint - secondPoint )
		remainingLength = jitterPosition - lastLength
		pointIndex = pointIndex % len( jitterLoop )
		ultimateJitteredPoint = jitterLoop[ pointIndex ]
		penultimateJitteredPointIndex = ( pointIndex + len( jitterLoop ) - 1 ) % len( jitterLoop )
		penultimateJitteredPoint = jitterLoop[ penultimateJitteredPointIndex ]
		segment = ultimateJitteredPoint - penultimateJitteredPoint
		segmentLength = abs( segment )
		originalOffsetLoop = euclidean.getAroundLoop( pointIndex, pointIndex, jitterLoop )
		if segmentLength <= 0.0:
			return [ penultimateJitteredPoint ] + originalOffsetLoop[ - 1 ]
		newUltimatePoint = penultimateJitteredPoint + segment * remainingLength / segmentLength
		return [ newUltimatePoint ] + originalOffsetLoop

	def getOutloopLocation( self, point ):
		"Get location outside of loop."
		pointComplex = point.dropAxis( 2 )
		if str( point ) not in self.pointTable:
			return pointComplex
		closestBetween = None
		closestDistanceIndex = euclidean.DistanceIndex( 999999999999999999.0, - 1 )
		for between in self.getBetweens():
			distanceIndex = euclidean.getNearestDistanceIndex( pointComplex, between )
			if distanceIndex.distance < closestDistanceIndex.distance:
				closestBetween = between
				closestDistanceIndex = distanceIndex
		if closestBetween == None:
			print( 'This should never happen, closestBetween should always exist in getOutloopLocation in comb.' )
			print( point )
			print( self.getBetweens() )
			return pointComplex
		closestIndex = closestDistanceIndex.index
		segmentBegin = closestBetween[ closestIndex ]
		segmentEnd = closestBetween[ ( closestIndex + 1 ) % len( closestBetween ) ]
		nearestPoint = euclidean.getNearestPointOnSegment( segmentBegin, segmentEnd, pointComplex )
		return pointComplex + 1.1 * ( nearestPoint - pointComplex )

	def getStartIndex( self, xIntersections ):
		"Get the start index of the intersections."
		startIndex = 0
		while startIndex < len( xIntersections ) - 1:
			xIntersectionFirst = xIntersections[ startIndex ]
			xIntersectionSecond = xIntersections[ startIndex + 1 ]
			loopFirst = self.getBetweens()[ xIntersectionFirst.index ]
			loopSecond = self.getBetweens()[ xIntersectionSecond.index ]
			if loopFirst == loopSecond:
				return startIndex % 2
			startIndex += 1
		return 0

	def initializeMoreParameters( self ):
		"Add a movement to the output."
		self.distanceFeedRate.resetLocationOutput()
		self.extruderActive = False
		self.feedRateMinute = None
		self.isLoopPerimeter = False
		self.layerGolden = 0.0
		self.loopPath = None
		self.oldLocation = None

	def insertPathsBetween( self, aroundBetweenPath, nextBeginning, pathEnd ):
		"Insert paths between the perimeter and the fill."
		betweenX = []
		switchX = []
		segment = euclidean.getNormalized( nextBeginning - pathEnd )
		segmentYMirror = complex( segment.real, - segment.imag )
		pathEndRotated = segmentYMirror * pathEnd
		nextBeginningRotated = segmentYMirror * nextBeginning
		y = pathEndRotated.imag
		for betweenIndex in xrange( len( self.getBetweens() ) ):
			between = self.getBetweens()[ betweenIndex ]
			betweenRotated = euclidean.getPointsRoundZAxis( segmentYMirror, between )
			euclidean.addXIntersectionIndexes( betweenRotated, betweenIndex, switchX, y )
		switchX.sort()
		maximumX = max( pathEndRotated.real, nextBeginningRotated.real )
		minimumX = min( pathEndRotated.real, nextBeginningRotated.real )
		for xIntersection in switchX:
			if xIntersection.x > minimumX and xIntersection.x < maximumX:
				betweenX.append( xIntersection )
		betweenXIndex = self.getStartIndex( betweenX )
		while betweenXIndex < len( betweenX ) - 1:
			betweenXFirst = betweenX[ betweenXIndex ]
			betweenXSecond = betweenX[ betweenXIndex + 1 ]
			loopFirst = self.getBetweens()[ betweenXFirst.index ]
			betweenFirst = segment * complex( betweenXFirst.x, y )
			betweenSecond = segment * complex( betweenXSecond.x, y )
			isLeavingPerimeter = False
			if betweenXSecond.index != betweenXFirst.index:
				isLeavingPerimeter = True
			self.addPathBetween( aroundBetweenPath, betweenFirst, betweenSecond, isLeavingPerimeter, loopFirst )
			betweenXIndex += 2

	def isNextExtruderOn( self ):
		"Determine if there is an extruder on command before a move command."
		line = self.lines[ self.lineIndex ]
		splitLine = line.split()
		for afterIndex in xrange( self.lineIndex + 1, len( self.lines ) ):
			line = self.lines[ afterIndex ]
			splitLine = line.split()
			firstWord = gcodec.getFirstWord( splitLine )
			if firstWord == 'G1' or firstWord == 'M103':
				return False
			elif firstWord == 'M101':
				return True
		return False

	def linearMove( self, splitLine ):
		"Add to loop path if this is a loop or path."
		location = gcodec.getLocationFromSplitLine( self.oldLocation, splitLine )
		self.feedRateMinute = gcodec.getFeedRateMinute( self.feedRateMinute, splitLine )
		if self.isLoopPerimeter:
			if self.isNextExtruderOn():
				self.loopPath = euclidean.PathZ( location.z )
				if self.oldLocation != None:
					self.beforeLoopLocation = self.oldLocation.dropAxis( 2 )
		if self.loopPath != None:
			self.loopPath.path.append( location.dropAxis( 2 ) )
		self.oldLocation = location

	def parseAddJitter( self, line ):
		"Parse a gcode line, jitter it and add it to the comb skein."
		splitLine = line.split()
		if len( splitLine ) < 1:
			return
		firstWord = splitLine[ 0 ]
		if firstWord == 'G1':
			self.linearMove( splitLine )
		elif firstWord == 'M103':
			self.isLoopPerimeter = False
			if self.loopPath != None:
				self.addTailoredLoopPath()
		elif firstWord == '(<layer>':
			self.layerGolden += 0.61803398874989479
			self.layerJitter = self.jitter * ( math.fmod( self.layerGolden, 1.0 ) - 0.5 )
		elif firstWord == '(<loop>)' or firstWord == '(<perimeter>)':
			self.isLoopPerimeter = True
		if self.loopPath == None:
			self.distanceFeedRate.addLine( line )

	def parseAddTravel( self, line ):
		"Parse a gcode line and add it to the comb skein."
		splitLine = line.split()
		if len( splitLine ) < 1:
			return
		firstWord = splitLine[ 0 ]
		if firstWord == 'G1':
			self.addIfTravel( splitLine )
			self.layerZ = self.nextLayerZ
		elif firstWord == 'M101':
			self.extruderActive = True
		elif firstWord == 'M103':
			self.extruderActive = False
		elif firstWord == '(<layer>':
			self.nextLayerZ = float( splitLine[ 1 ] )
			if self.layerZ == None:
				self.layerZ = self.nextLayerZ
		self.distanceFeedRate.addLine( line )

	def parseInitialization( self, combPreferences ):
		"Parse gcode initialization and store the parameters."
		for self.lineIndex in xrange( len( self.lines ) ):
			line = self.lines[ self.lineIndex ]
			splitLine = line.split()
			firstWord = gcodec.getFirstWord( splitLine )
			self.distanceFeedRate.parseSplitLine( firstWord, splitLine )
			if firstWord == '(</extruderInitialization>)':
				self.distanceFeedRate.addLine( '(<procedureDone> comb </procedureDone>)' )
				return
			elif firstWord == '(<fillInset>':
				fillInset = float( splitLine[ 1 ] )
				self.lessThanFillInset = 0.8 * fillInset # should be a fair way before the extrusion and loop interface
			elif firstWord == '(<operatingFeedRatePerSecond>':
				self.operatingFeedRatePerMinute = 60.0 * float( splitLine[ 1 ] )
			elif firstWord == '(<perimeterWidth>':
				self.perimeterWidth = float( splitLine[ 1 ] )
				self.arrivalInsetFollowDistance = combPreferences.arrivalInsetFollowDistanceOverExtrusionWidth.value * self.perimeterWidth
				self.jitter = combPreferences.jitterOverExtrusionWidth.value * self.perimeterWidth
				self.minimumPerimeterDepartureDistance = combPreferences.minimumPerimeterDepartureDistanceOverExtrusionWidth.value * self.perimeterWidth
			elif firstWord == '(<travelFeedRatePerSecond>':
				self.travelFeedRatePerMinute = 60.0 * float( splitLine[ 1 ] )
			self.distanceFeedRate.addLine( line )

	def parseLine( self, combPreferences, line ):
		"Parse a gcode line."
		splitLine = line.split()
		if len( splitLine ) < 1:
			return
		firstWord = splitLine[ 0 ]
		if firstWord == 'G1':
			if self.isPerimeter:
				location = gcodec.getLocationFromSplitLine( None, splitLine )
				self.pointTable[ str( location ) ] = self.boundaryLoop
		elif firstWord == 'M103':
			self.boundaryLoop = None
			self.isPerimeter = False
		elif firstWord == '(<boundaryPoint>':
			location = gcodec.getLocationFromSplitLine( None, splitLine )
			self.addToLoop( location )
		elif firstWord == '(<layer>':
			self.boundaryLoop = None
			self.layer = None
			self.oldZ = float( splitLine[ 1 ] )
		elif firstWord == '(<perimeter>)':
			self.isPerimeter = True


def main():
	"Display the comb dialog."
	if len( sys.argv ) > 1:
		writeOutput( ' '.join( sys.argv[ 1 : ] ) )
	else:
		preferences.startMainLoopFromConstructor( getPreferencesConstructor() )

if __name__ == "__main__":
	main()

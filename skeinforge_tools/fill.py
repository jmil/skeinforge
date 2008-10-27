#! /usr/bin/env python
"""
Fill is a script to fill the slices of a gcode file.

The following examples fill the files Hollow Square.gcode & Hollow Square.gts.  The examples are run in a terminal in the folder which contains
Hollow Square.gcode, Hollow Square.gts and fill.py.


> python fill.py
This brings up the dialog, after clicking 'Fill', the following is printed:
File Hollow Square.gts is being chain filled.
The filled file is saved as Hollow Square_fill.gcode


>python
Python 2.5.1 (r251:54863, Sep 22 2007, 01:43:31)
[GCC 4.2.1 (SUSE Linux)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import fill
>>> fill.main()
File Hollow Square.gts is being filled.
The filled file is saved as Hollow Square_fill.gcode
It took 3 seconds to fill the file.


>>> fill.writeOutput()
File Hollow Square.gts is being filled.
The filled file is saved as Hollow Square_fill.gcode
It took 3 seconds to fill the file.

"""

from __future__ import absolute_import
try:
	import psyco
	psyco.full()
except:
	pass
#Init has to be imported first because it has code to workaround the python bug where relative imports don't work if the module is imported as a main module.
import __init__

from skeinforge_tools.skeinforge_utilities import euclidean
from skeinforge_tools.skeinforge_utilities import gcodec
from skeinforge_tools.skeinforge_utilities import intercircle
from skeinforge_tools.skeinforge_utilities import preferences
from skeinforge_tools.skeinforge_utilities.vec3 import Vec3
from skeinforge_tools import analyze
from skeinforge_tools import import_translator
from skeinforge_tools import polyfile
from skeinforge_tools import slice_shape
import cStringIO
import math
import sys
import time


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/28/04 $"
__license__ = "GPL 3.0"

#one direction for while, one direction narrow then wide, split to weave, hex fill, loop inside sparse fill or run along sparse infill, fill in one direction for a number of layers
#use slice format, carve & inset
#bridge extrusion width
#fillet travel and reversals
#slice aoi xml
#raft supports overhangs
#change material
#multiply
#distance option
#extrude loops
#document gear script
#email marcus about peek extruder, raft offset problem and bridge extrusion width http://reprap.org/bin/view/Main/ExtruderImprovementsAndAlternatives
#mosaic
#transform
#pick and place
#stack
#infill first
#searchable help
#faster
#custom inclined plane, inclined plane from model, screw, fillet travel as well maybe
#later maybe addAroundClosest around arounds and check for closeness to other infills
#maybe much afterwards make congajure multistep view
#maybe bridge supports although staggered spans are probably better
#maybe update slice to add perimeter path intersection information to the large loop also
#maybe stripe although mosaic alone can handle it
#stretch fiber around shape
#multiple heads around edge
#angle shape for overhang extrusions
#free fabricator
def addAroundClosest( arounds, layerExtrusionWidth, paths, removedEndpointPoint ):
	"Add the closest removed endpoint to the path, with minimal twisting."
	closestDistanceSquared = 999999999999999999.0
	closestPathIndex = None
	for pathIndex in range( len( paths ) ):
		path = paths[ pathIndex ]
		for pointIndex in range( len( path ) ):
			point = path[ pointIndex ]
			distanceSquared = point.distance2( removedEndpointPoint )
			if distanceSquared < closestDistanceSquared:
				closestDistanceSquared = distanceSquared
				closestPathIndex = pathIndex
	if closestPathIndex == None:
		return
	if closestDistanceSquared < 0.8 * layerExtrusionWidth * layerExtrusionWidth:
		return
	closestPath = paths[ closestPathIndex ]
	closestPointIndex = getWithLeastLength( closestPath, removedEndpointPoint )
	pathJustAfter = closestPath[ closestPointIndex + 2 : ]
	pathJustBefore = closestPath[ : closestPointIndex - 1 ]
	otherPaths = paths[ : closestPathIndex ] + paths[ closestPathIndex + 1 : ] + [ pathJustAfter, pathJustBefore ]
	if isIntersectingLoopsPaths( arounds, otherPaths, removedEndpointPoint, closestPath[ min( closestPointIndex, len( closestPath ) - 1 ) ] ):
		return
	if closestPointIndex == 0 or closestPointIndex == len( closestPath ):
		closestPath.insert( closestPointIndex, removedEndpointPoint )
		return
	if not isIntersectingLoopsPaths( arounds, otherPaths, removedEndpointPoint, closestPath[ closestPointIndex - 1 ] ):
		closestPath.insert( closestPointIndex, removedEndpointPoint )

def addAroundGridPoint( arounds, gridPoint, gridRadius, layerExtrusionRadius, paths ):
	"Add the path around the grid point."
	closestPathIndex = None
	segmentFirstY = gridPoint.y - gridRadius
	segmentSecondY = gridPoint.y + gridRadius
	yIntersectionPaths = []
	for pathIndex in range( len( paths ) ):
		path = paths[ pathIndex ]
		for pointIndex in xrange( len( path ) - 1 ):
			pointFirst = path[ pointIndex ]
			pointSecond = path[ pointIndex + 1 ]
			yIntersection = getYIntersectionInsideYSegment( segmentFirstY, segmentSecondY, pointFirst, pointSecond, gridPoint.x )
			if yIntersection != None:
				yIntersectionPath = YIntersectionPath( path, pointIndex, yIntersection )
				yIntersectionPath.yMinusCenter = yIntersection - gridPoint.y
				yIntersectionPaths.append( yIntersectionPath )
	yIntersectionPaths.sort( compareDistanceFromCenter )
	if len( yIntersectionPaths ) < 1:
		return
	secondIntersectionPath = None
	beforeFirst = yIntersectionPaths[ 0 ].yMinusCenter < 0.0
	yIntersectionPathIndex = 1
	while yIntersectionPathIndex < len( yIntersectionPaths ):
		yIntersectionPath = yIntersectionPaths[ yIntersectionPathIndex ]
		beforeSecond = yIntersectionPath.yMinusCenter < 0.0
		if beforeFirst != beforeSecond:
			secondIntersectionPath = yIntersectionPath
			yIntersectionPathIndex += len( yIntersectionPaths )
		yIntersectionPathIndex += 1
	if secondIntersectionPath == None:
		yIntersectionPaths[ 0 ].path.insert( yIntersectionPaths[ 0 ].pointIndex + 1, gridPoint )
		return
	if not beforeFirst:
		layerExtrusionRadius = - layerExtrusionRadius
	gridPointYFirst = Vec3( gridPoint.x, gridPoint.y - layerExtrusionRadius, gridPoint.z )
	gridPointYSecond = Vec3( gridPoint.x, gridPoint.y + layerExtrusionRadius, gridPoint.z )
	firstPointIndexPlusOne = yIntersectionPaths[ 0 ].pointIndex + 1
	yIntersectionPaths[ 0 ].path.insert( firstPointIndexPlusOne, gridPointYFirst )
	secondPointIndexPlusOne = secondIntersectionPath.pointIndex + 1
	if yIntersectionPaths[ 0 ].path == secondIntersectionPath.path:
		if secondPointIndexPlusOne > firstPointIndexPlusOne:
			secondPointIndexPlusOne += 1
	secondIntersectionPath.path.insert( secondPointIndexPlusOne, gridPointYSecond )

def addPath( extrusionWidth, fill, path, rotationPlaneAngle ):
	"Add simplified path to fill."
	planeRotated = euclidean.getPathRoundZAxisByPlaneAngle( rotationPlaneAngle, euclidean.getSimplifiedPath( path, extrusionWidth ) )
	fill.append( planeRotated )

def addSparseEndpoints( doubleExtrusionWidth, endpoints, fillLine, horizontalSegments, infillDensity, removedEndpoints, solidSurfaceThickness, surroundingXIntersections ):
	"Add sparse endpoints."
	horizontalEndpoints = horizontalSegments[ fillLine ]
	for segment in horizontalEndpoints:
		addSparseEndpointsFromSegment( doubleExtrusionWidth, endpoints, fillLine, horizontalSegments, infillDensity, removedEndpoints, segment, solidSurfaceThickness, surroundingXIntersections )

def addSparseEndpointsFromSegment( doubleExtrusionWidth, endpoints, fillLine, horizontalSegments, infillDensity, removedEndpoints, segment, solidSurfaceThickness, surroundingXIntersections ):
	"Add sparse endpoints from a segment."
	endpointFirstPoint = segment[ 0 ].point
	endpointSecondPoint = segment[ 1 ].point
	if fillLine < 1 or fillLine >= len( horizontalSegments ) - 1 or surroundingXIntersections == None:
		endpoints += segment
		return
	if infillDensity > 0.0:
		if int( round( round( fillLine * infillDensity ) / infillDensity ) ) == fillLine:
			endpoints += segment
			return
	if endpointFirstPoint.distance( endpointSecondPoint ) < doubleExtrusionWidth:
		endpoints += segment
		return
	if not isSegmentAround( horizontalSegments[ fillLine - 1 ], segment ):
		endpoints += segment
		return
	if not isSegmentAround( horizontalSegments[ fillLine + 1 ], segment ):
		endpoints += segment
		return
	if solidSurfaceThickness == 0:
		removedEndpoints += segment
		return
	for surroundingIndex in xrange( 0, len( surroundingXIntersections ), 2 ):
		surroundingXFirst = surroundingXIntersections[ surroundingIndex ]
		surroundingXSecond = surroundingXIntersections[ surroundingIndex + 1 ]
		if euclidean.isSegmentCompletelyInX( segment, surroundingXFirst, surroundingXSecond ):
			removedEndpoints += segment
			return
	endpoints += segment

def compareDistanceFromCenter( self, other ):
	"Get comparison in order to sort y intersections in ascending order of distance from the center."
	distanceFromCenter = abs( self.yMinusCenter )
	distanceFromCenterOther = abs( other.yMinusCenter )
	if distanceFromCenter > distanceFromCenterOther:
		return 1
	if distanceFromCenter < distanceFromCenterOther:
		return - 1
	return 0

def createFillForSurroundings( surroundingLoops ):
	"Create extra fill loops for surrounding loops."
	for surroundingLoop in surroundingLoops:
		createExtraFillLoops( surroundingLoop )

def createExtraFillLoops( surroundingLoop ):
	"Create extra fill loops."
	for innerSurrounding in surroundingLoop.innerSurroundings:
		createFillForSurroundings( innerSurrounding.innerSurroundings )
#	if len( surroundingLoop.perimeterPaths ) > 0:
#		return
	outsides = []
	insides = euclidean.getInsidesAddToOutsides( surroundingLoop.getFillLoops(), outsides )
	allFillLoops = []
	for outside in outsides:
		transferredLoops = euclidean.getTransferredPaths( insides, outside )
		allFillLoops += getExtraFillLoops( transferredLoops, outside, surroundingLoop.extrusionWidth )
	if len( allFillLoops ) > 0:
		surroundingLoop.lastFillLoops = allFillLoops
	surroundingLoop.extraLoops += allFillLoops

def getExtraFillLoops( insideLoops, outsideLoop, radius ):
	"Get extra loops between inside and outside loops."
	greaterThanRadius = 1.4 * radius
	muchGreaterThanRadius = 2.5 * radius
	extraFillLoops = []
	circleNodes = intercircle.getCircleNodesFromLoop( outsideLoop, greaterThanRadius )
	for inside in insideLoops:
		circleNodes += intercircle.getCircleNodesFromLoop( inside, greaterThanRadius )
	#adding inside then outside avoids a weird crossing bug that I don't understand but was fixed anyways with normalize.
	centers = intercircle.getCentersFromCircleNodes( circleNodes )
	otherLoops = insideLoops + [ outsideLoop ]
	for center in centers:
		inset = intercircle.getSimplifiedInsetFromClockwiseLoop( center, radius )
		if euclidean.isLargeSameDirection( inset, center, muchGreaterThanRadius ):
			if isPathAlwaysInsideLoop( outsideLoop, inset ):
				if isPathAlwaysOutsideLoops( insideLoops, inset ):
					if not euclidean.isLoopIntersectingLoops( inset, otherLoops ):
						inset.reverse()
						extraFillLoops.append( inset )
	return extraFillLoops

def getFillChainGcode( filename, gcodeText, fillPreferences = None ):
	"Fill the slices of a gcode text.  Chain fill the gcode if it is not already sliced."
	gcodeText = gcodec.getGcodeFileText( filename, gcodeText )
	if not gcodec.isProcedureDone( gcodeText, 'slice_shape' ):
		gcodeText = slice_shape.getSliceGcode( filename )
	return getFillGcode( gcodeText, fillPreferences )

def getFillGcode( gcodeText, fillPreferences = None ):
	"Fill the slices of a gcode text."
	if gcodeText == '':
		return ''
	if gcodec.isProcedureDone( gcodeText, 'fill' ):
		return gcodeText
	if fillPreferences == None:
		fillPreferences = FillPreferences()
		preferences.readPreferences( fillPreferences )
	skein = FillSkein()
	skein.parseGcode( fillPreferences, gcodeText )
	return skein.output.getvalue()

def getHorizontalSegments( fillLoops, alreadyFilledArounds, y ):
	"Get horizontal segments inside loops."
	solidXIntersectionList = []
	euclidean.addXIntersectionsFromLoops( fillLoops, - 1, solidXIntersectionList, y )
	euclidean.addXIntersectionsFromLoopLists( alreadyFilledArounds, solidXIntersectionList, y )
	return euclidean.getSegmentsFromIntersections( solidXIntersectionList, y, fillLoops[ 0 ][ 0 ].z )

def getSurroundingXIntersections( doubleSolidSurfaceThickness, surroundingSlices, y ):
	"Get x intersections from surrounding layers."
	if len( surroundingSlices ) < doubleSolidSurfaceThickness:
		return None
	joinedX = []
	solidXIntersectionList = []
	for surroundingIndex in range( len( surroundingSlices ) ):
		surroundingSlice = surroundingSlices[ surroundingIndex ]
		euclidean.addXIntersectionsFromLoops( surroundingSlice, surroundingIndex, joinedX, y )
	solidTable = {}
	solid = False
	joinedX.sort()
	for solidX in joinedX:
		euclidean.toggleHashtable( solidTable, solidX.index, "" )
		oldSolid = solid
		solid = len( solidTable ) >= doubleSolidSurfaceThickness
		if oldSolid != solid:
			solidXIntersectionList.append( solidX.x )
	return solidXIntersectionList

def getWithLeastLength( path, point ):
	"Insert a point into a path, at the index at which the path would be shortest."
	shortestPointIndex = None
	shortestPathLength = 999999999999999999.0
	for pointIndex in range( len( path ) + 1 ):
		concatenation = path[ : ]
		concatenation.insert( pointIndex, point )
		concatenationLength = euclidean.getPathLength( concatenation )
		if concatenationLength < shortestPathLength:
			shortestPathLength = concatenationLength
			shortestPointIndex = pointIndex
	return shortestPointIndex

def getYIntersection( firstPoint, secondPoint, x ):
	"Get where the line crosses x."
	secondMinusFirst = secondPoint.minus( firstPoint )
	xMinusFirst = x - firstPoint.x
	return xMinusFirst / secondMinusFirst.x * secondMinusFirst.y + firstPoint.y

def getYIntersectionInsideYSegment( segmentFirstY, segmentSecondY, vector3First, vector3Second, x ):
	"Get the y intersection inside the y segment if it does, else none."
	isXAboveFirst = x > vector3First.x
	isXAboveSecond = x > vector3Second.x
	if isXAboveFirst == isXAboveSecond:
		return None
	yIntersection = getYIntersection( vector3First, vector3Second, x )
	if yIntersection <= min( segmentFirstY, segmentSecondY ):
		return None
	if yIntersection < max( segmentFirstY, segmentSecondY ):
		return yIntersection
	return None

def isIntersectingLoopsPaths( loops, paths, pointBegin, pointEnd ):
	"Determine if the segment between the first and second point is intersecting the loop list."
	normalizedSegment = pointEnd.dropAxis( 2 ) - pointBegin.dropAxis( 2 )
	normalizedSegmentLength = abs( normalizedSegment )
	if normalizedSegmentLength == 0.0:
		return False
	normalizedSegment /= normalizedSegmentLength
	segmentYMirror = complex( normalizedSegment.real, - normalizedSegment.imag )
	pointBeginRotated = euclidean.getRoundZAxisByPlaneAngle( segmentYMirror, pointBegin )
	pointEndRotated = euclidean.getRoundZAxisByPlaneAngle( segmentYMirror, pointEnd )
	if euclidean.isLoopListIntersectingInsideXSegment( loops, pointBeginRotated.x, pointEndRotated.x, segmentYMirror, pointBeginRotated.y ):
		return True
	return euclidean.isXSegmentIntersectingPaths( paths, pointBeginRotated.x, pointEndRotated.x, segmentYMirror, pointBeginRotated.y )

def isPathAlwaysInsideLoop( loop, path ):
	"Determine if all points of a path are inside another loop."
	for point in path:
		if euclidean.getNumberOfIntersectionsToLeft( point, loop ) % 2 == 0:
			return False
	return True

def isPathAlwaysOutsideLoops( loops, path ):
	"Determine if all points in a path are outside another loop in a list."
	for loop in loops:
		for point in path:
			if euclidean.getNumberOfIntersectionsToLeft( point, loop ) % 2 == 1:
				return False
	return True

def isPerimeterPathInSurroundLoops( surroundingLoops ):
	"Determine if there is a perimeter path in the surrounding loops."
	for surroundingLoop in surroundingLoops:
		if len( surroundingLoop.perimeterPaths ) > 0:
			return True
	return False

def isSegmentAround( aroundSegments, segment ):
	"Determine if there is another segment around."
	for aroundSegment in aroundSegments:
		endpoint = aroundSegment[ 0 ]
		if isSegmentInX( segment, endpoint.point.x, endpoint.otherEndpoint.point.x ):
			return True
	return False

def isSegmentInX( segment, xFirst, xSecond ):
	"Determine if the segment overlaps within x."
	segmentFirstX = segment[ 0 ].point.x
	segmentSecondX = segment[ 1 ].point.x
	if min( segmentFirstX, segmentSecondX ) > max( xFirst, xSecond ):
		return False
	return max( segmentFirstX, segmentSecondX ) > min( xFirst, xSecond )

def writeOutput( filename = '' ):
	"Fill the slices of a gcode file.  Chain slice the file if it is a GNU TriangulatedSurface file.  If no filename is specified, fill the first unmodified gcode file in this folder."
	if filename == '':
		unmodified = import_translator.getGNUTranslatorFilesUnmodified()
		if len( unmodified ) == 0:
			print( "There are no unmodified gcode files in this folder." )
			return
		filename = unmodified[ 0 ]
	startTime = time.time()
	fillPreferences = FillPreferences()
	preferences.readPreferences( fillPreferences )
	print( 'File ' + gcodec.getSummarizedFilename( filename ) + ' is being chain filled.' )
	suffixFilename = filename[ : filename.rfind( '.' ) ] + '_fill.gcode'
	fillGcode = getFillChainGcode( filename, '', fillPreferences )
	if fillGcode == '':
		return
	gcodec.writeFileText( suffixFilename, fillGcode )
	print( 'The filled file is saved as ' + suffixFilename )
	analyze.writeOutput( suffixFilename, fillGcode )
	print( 'It took ' + str( int( round( time.time() - startTime ) ) ) + ' seconds to fill the file.' )


class FillPreferences:
	"A class to handle the fill preferences."
	def __init__( self ):
		"Set the default preferences, execute title & preferences filename."
		#Set the default preferences.
		self.archive = []
		self.diaphragmPeriod = preferences.IntPreference().getFromValue( 'Diaphragm Period (layers):', 999999 )
		self.archive.append( self.diaphragmPeriod )
		self.diaphragmThickness = preferences.IntPreference().getFromValue( 'Diaphragm Thickness (layers):', 0 )
		self.archive.append( self.diaphragmThickness )
		self.extraShellsAlternatingSolidLayer = preferences.IntPreference().getFromValue( 'Extra Shells on Alternating Solid Layer (layers):', 1 )
		self.archive.append( self.extraShellsAlternatingSolidLayer )
		self.extraShellsBase = preferences.IntPreference().getFromValue( 'Extra Shells on Base (layers):', 0 )
		self.archive.append( self.extraShellsBase )
		self.extraShellsSparseLayer = preferences.IntPreference().getFromValue( 'Extra Shells on Sparse Layer (layers):', 1 )
		self.archive.append( self.extraShellsSparseLayer )
		self.filenameInput = preferences.Filename().getFromFilename( import_translator.getGNUTranslatorGcodeFileTypeTuples(), 'Open File to be Filled', '' )
		self.archive.append( self.filenameInput )
		self.infillBeginRotation = preferences.FloatPreference().getFromValue( 'Infill Begin Rotation (degrees):', 45.0 )
		self.archive.append( self.infillBeginRotation )
		self.infillDensity = preferences.FloatPreference().getFromValue( 'Infill Density (ratio):', 0.25 )
		self.archive.append( self.infillDensity )
		self.infillOddLayerExtraRotation = preferences.FloatPreference().getFromValue( 'Infill Odd Layer Extra Rotation (degrees):', 90.0 )
		self.archive.append( self.infillOddLayerExtraRotation )
#		infillPatternRadio = []
#		self.infillPatternGrid = preferences.RadioLabel().getFromRadioLabel( 'Grid', 'Infill Pattern:', infillPatternRadio, False )
#		self.archive.append( self.infillPatternGrid )
#		self.infillPatternLine = preferences.Radio().getFromRadio( 'Line', infillPatternRadio, True )
#		self.archive.append( self.infillPatternLine )
		self.solidSurfaceThickness = preferences.IntPreference().getFromValue( 'Solid Surface Thickness (layers):', 3 )
		self.archive.append( self.solidSurfaceThickness )
		#Create the archive, title of the execute button, title of the dialog & preferences filename.
		self.executeTitle = 'Fill'
		self.filenamePreferences = preferences.getPreferencesFilePath( 'fill.csv' )
		self.filenameHelp = 'skeinforge_tools.fill.html'
		self.saveTitle = 'Save Preferences'
		self.title = 'Fill Preferences'

	def execute( self ):
		"Fill button has been clicked."
		filenames = polyfile.getFileOrDirectoryTypesUnmodifiedGcode( self.filenameInput.value, import_translator.getGNUTranslatorFileTypes(), self.filenameInput.wasCancelled )
		for filename in filenames:
			writeOutput( filename )


class FillSkein:
	"A class to fill a skein of extrusions."
	def __init__( self ):
		self.decimalPlacesCarried = 3
		self.extruderActive = False
		self.fillInset = 0.18
		self.isPerimeter = False
		self.lastExtraShells = - 1
		self.lineIndex = 0
		self.oldLocation = None
		self.oldOrderedLocation = Vec3()
		self.output = cStringIO.StringIO()
		self.rotatedLayer = None
		self.rotatedLayers = []
		self.shutdownLineIndex = sys.maxint
		self.surroundingLoop = None
		self.thread = None

	def addFill( self, layerIndex ):
		"Add fill to the slice layer."
#		if layerIndex != 9:
#			return
		alreadyFilledArounds = []
		arounds = []
		back = - 999999999.0
		layerExtrusionWidth = self.extrusionWidth
		layerFillInset = self.fillInset
		z = self.rotatedLayers[ layerIndex ].surroundingLoops[ 0 ].boundary[ 0 ].z
		self.addLine( '(<layerStart> %s )' % z ) # Indicate that a new layer is starting.
		if self.rotatedLayers[ layerIndex ].rotation != None:
			layerExtrusionWidth = self.extrusionWidth * self.bridgeExtrusionWidthOverSolid
			layerFillInset = self.fillInset * self.bridgeExtrusionWidthOverSolid
			self.addLine( '(<bridgeLayer> )' ) # Indicate that this is a bridge layer.
		doubleExtrusionWidth = 2.0 * layerExtrusionWidth
		muchGreaterThanLayerFillInset = 2.5 * layerFillInset
		endpoints = []
		fill = []
		aroundInset = 0.7 * layerFillInset
		front = - back
		slightlyGreaterThanFill = 1.01 * layerFillInset
		layerRotationAroundZAngle = self.getLayerRoundZ( layerIndex )
		reverseRotationAroundZAngle = complex( layerRotationAroundZAngle.real, - layerRotationAroundZAngle.imag )
		rotatedExtruderLoops = []
		stretch = 0.5 * layerExtrusionWidth
		loops = []
		for surroundingLoop in self.rotatedLayers[ layerIndex ].surroundingLoops:
			loops.append( surroundingLoop.boundary )
		surroundingSlices = []
		layerRemainder = layerIndex % int( round( self.fillPreferences.diaphragmPeriod.value ) )
		if layerRemainder >= int( round( self.fillPreferences.diaphragmThickness.value ) ):
			for surroundingIndex in range( 1, self.solidSurfaceThickness + 1 ):
				self.addRotatedSlice( layerIndex - surroundingIndex, reverseRotationAroundZAngle, surroundingSlices )
				self.addRotatedSlice( layerIndex + surroundingIndex, reverseRotationAroundZAngle, surroundingSlices )
		extraShells = self.fillPreferences.extraShellsSparseLayer.value
		if len( surroundingSlices ) < self.doubleSolidSurfaceThickness:
			extraShells = self.fillPreferences.extraShellsAlternatingSolidLayer.value
			if self.lastExtraShells != self.fillPreferences.extraShellsBase.value:
				extraShells = self.fillPreferences.extraShellsBase.value
			self.lastExtraShells = extraShells
		else:
			self.lastExtraShells = - 1
		surroundingLoops = euclidean.getOrderedSurroundingLoops( layerExtrusionWidth, self.rotatedLayers[ layerIndex ].surroundingLoops )
		if isPerimeterPathInSurroundLoops( surroundingLoops ):
			extraShells = 0
		for extraShellIndex in range( extraShells ):
			createFillForSurroundings( surroundingLoops )
		fillLoops = euclidean.getFillOfSurroundings( surroundingLoops )
		for loop in fillLoops:
			alreadyFilledLoop = []
			alreadyFilledArounds.append( alreadyFilledLoop )
			planeRotatedPerimeter = euclidean.getPathRoundZAxisByPlaneAngle( reverseRotationAroundZAngle, loop )
			rotatedExtruderLoops.append( planeRotatedPerimeter )
#			arounds.append( planeRotatedPerimeter )
			circleNodes = intercircle.getCircleNodesFromLoop( planeRotatedPerimeter, slightlyGreaterThanFill )
			centers = intercircle.getCentersFromCircleNodes( circleNodes )
			for center in centers:
				alreadyFilledInset = intercircle.getSimplifiedInsetFromClockwiseLoop( center, layerFillInset )
				if euclidean.getMaximumSpan( alreadyFilledInset ) > muchGreaterThanLayerFillInset:
					alreadyFilledLoop.append( alreadyFilledInset )
					around = intercircle.getSimplifiedInsetFromClockwiseLoop( center, aroundInset )
					if euclidean.isPathInsideLoop( planeRotatedPerimeter, around ) == euclidean.isWiddershins( planeRotatedPerimeter ):
						arounds.append( around )
						for point in around:
							back = max( back, point.y )
							front = min( front, point.y )
		front = math.ceil( front / layerExtrusionWidth ) * layerExtrusionWidth
		fillWidth = back - front
		numberOfLines = int( math.ceil( fillWidth / layerExtrusionWidth ) )
#		fillRemainder = fillWidth - float( numberOfIntervals ) * layerExtrusionWidth
#		halfFillRemainder = 0.5 * fillRemainder
#		front += halfFillRemainder
		horizontalSegments = []
		for fillLine in xrange( numberOfLines ):
			y = front + float( fillLine ) * layerExtrusionWidth
			lineSegments = getHorizontalSegments( rotatedExtruderLoops, alreadyFilledArounds, y )
			horizontalSegments.append( lineSegments )
		removedEndpoints = []
		for fillLine in range( len( horizontalSegments ) ):
			y = front + float( fillLine ) * layerExtrusionWidth
			horizontalEndpoints = horizontalSegments[ fillLine ]
			surroundingXIntersections = getSurroundingXIntersections( self.doubleSolidSurfaceThickness, surroundingSlices, y )
			addSparseEndpoints( doubleExtrusionWidth, endpoints, fillLine, horizontalSegments, self.infillDensity, removedEndpoints, self.solidSurfaceThickness, surroundingXIntersections )
		if len( endpoints ) < 1:
			euclidean.addToThreadsRemoveFromSurroundings( self.oldOrderedLocation, surroundingLoops, self )
			return
		stretchedXSegments = []
		for beginningEndpoint in endpoints[ : : 2 ]:
			beginningPoint = beginningEndpoint.point
			stretchedXSegment = StretchedXSegment().getFromXYStretch( beginningPoint.x, beginningPoint.y, beginningEndpoint.otherEndpoint.point.x, stretch )
			stretchedXSegments.append( stretchedXSegment )
		endpointFirst = endpoints[ 0 ]
		endpoints.remove( endpointFirst )
		otherEndpoint = endpointFirst.otherEndpoint
		endpoints.remove( otherEndpoint )
		nextEndpoint = None
		path = []
		paths = [ path ]
		if len( endpoints ) > 1:
			nextEndpoint = otherEndpoint.getNearestMiss( arounds, endpoints, layerExtrusionWidth, path, paths, stretchedXSegments )
			if nextEndpoint != None:
				if nextEndpoint.point.distance2( endpointFirst.point ) < nextEndpoint.point.distance2( otherEndpoint.point ):
					endpointFirst = endpointFirst.otherEndpoint
					otherEndpoint = endpointFirst.otherEndpoint
		path.append( endpointFirst.point )
		path.append( otherEndpoint.point )
		while len( endpoints ) > 1:
			nextEndpoint = otherEndpoint.getNearestMiss( arounds, endpoints, layerExtrusionWidth, path, paths, stretchedXSegments )
			if nextEndpoint == None:
				path = []
				paths.append( path )
				nextEndpoint = otherEndpoint.getNearestEndpoint( endpoints )
			path.append( nextEndpoint.point )
			endpoints.remove( nextEndpoint )
			otherEndpoint = nextEndpoint.otherEndpoint
			hop = nextEndpoint.getHop( layerFillInset, path )
			if hop != None:
				path = [ hop ]
				paths.append( path )
			path.append( otherEndpoint.point )
			endpoints.remove( otherEndpoint )
#		if self.fillPreferences.infillPatternGrid.value:
#			self.addGrid( arounds, fillLoops, layerExtrusionWidth, paths, reverseRotationAroundZAngle, z )
		for removedEndpoint in removedEndpoints:
			removedEndpointPoint = removedEndpoint.point
			addAroundClosest( arounds, layerExtrusionWidth, paths, removedEndpointPoint )
		for path in paths:
			addPath( layerFillInset, fill, path, layerRotationAroundZAngle )
		euclidean.transferPathsToSurroundingLoops( fill, surroundingLoops )
		euclidean.addToThreadsRemoveFromSurroundings( self.oldOrderedLocation, surroundingLoops, self )

	def addGcodeFromThread( self, thread ):
		"Add a gcode thread to the output."
		if len( thread ) > 0:
			self.addGcodeMovement( thread[ 0 ] )
		else:
			print( "zero length vertex positions array which was skipped over, this should never happen" )
		if len( thread ) < 2:
			return
		self.addLine( 'M101' )
		for point in thread[ 1 : ]:
			self.addGcodeMovement( point )
		self.addLine( "M103" ) # Turn extruder off.

	def addGcodeMovement( self, point ):
		"Add a movement to the output."
		self.addLine( "G1 X%s Y%s Z%s" % ( self.getRounded( point.x ), self.getRounded( point.y ), self.getRounded( point.z ) ) )

	def addGrid( self, arounds, fillLoops, layerExtrusionWidth, paths, reverseRotationAroundZAngle, z ):
		"Add a grid to the infill."
		alreadyFilledArounds = []
		back = - 999999999.0
		front = - back
		layerExtrusionRadius = 0.5 * layerExtrusionWidth
		gridInset = 2.0 * self.extrusionWidth
		muchGreaterThanLayerFillInset = 1.5 * gridInset
		rotatedExtruderLoops = []
		slightlyGreaterThanFill = 1.01 * gridInset
		for loop in fillLoops:
			alreadyFilledLoop = []
			alreadyFilledArounds.append( alreadyFilledLoop )
			planeRotatedPerimeter = euclidean.getPathRoundZAxisByPlaneAngle( reverseRotationAroundZAngle, loop )
			rotatedExtruderLoops.append( planeRotatedPerimeter )
			circleNodes = intercircle.getCircleNodesFromLoop( planeRotatedPerimeter, slightlyGreaterThanFill )
			centers = intercircle.getCentersFromCircleNodes( circleNodes )
			for center in centers:
				alreadyFilledInset = intercircle.getSimplifiedInsetFromClockwiseLoop( center, gridInset )
				if euclidean.getMaximumSpan( alreadyFilledInset ) > muchGreaterThanLayerFillInset:
					alreadyFilledLoop.append( alreadyFilledInset )
					if euclidean.isPathInsideLoop( planeRotatedPerimeter, alreadyFilledInset ) == euclidean.isWiddershins( planeRotatedPerimeter ):
						for point in alreadyFilledInset:
							back = max( back, point.y )
							front = min( front, point.y )
		gridRadius = self.extrusionWidth / self.infillDensity
		gridWidth = 2.0 * gridRadius
		front = math.ceil( front / gridRadius ) * gridRadius
		fillWidth = back - front
		numberOfLines = int( math.ceil( fillWidth / gridRadius ) )
		horizontalSegments = []
		print(front  )
		for fillLine in xrange( numberOfLines ):
			y = front + float( fillLine ) * gridRadius
			lineSegments = getHorizontalSegments( rotatedExtruderLoops, alreadyFilledArounds, y )
			horizontalSegments.append( lineSegments )
		for horizontalSegment in horizontalSegments:
			for lineSegment in horizontalSegment:
				endpointFirst = lineSegment[ 0 ]
				endpointSecond = lineSegment[ 1 ]
				begin = min( endpointFirst.point.x, endpointSecond.point.x )
				end = max( endpointFirst.point.x, endpointSecond.point.x )
				y = endpointFirst.point.y
				offset = 0.0
				if round( y / gridRadius ) % 2 == 1:
					offset = gridRadius
				self.addGridLineSegments( arounds, begin, end, layerExtrusionRadius, offset, gridWidth, paths, y, z )

	def addGridLineSegments( self, arounds, begin, end, layerExtrusionRadius, offset, period, paths, y, z ):
		"Add the segments of one line of a grid to the infill."
		if period == 0.0:
			return
		gridX = offset - period * math.floor( ( offset - begin ) / period )
#		gridX = offset
		while gridX < end:
			gridPoint = Vec3( gridX, y, z )
			addAroundGridPoint( arounds, gridPoint, 5.87 * self.extrusionWidth, layerExtrusionRadius, paths )
			gridX += period

	def addLine( self, line ):
		"Add a line of text and a newline to the output."
		self.output.write( line + "\n" )

	def addRotatedSlice( self, layerIndex, reverseRotationAroundZAngle, surroundingSlices ):
		"Add a rotated slice to the surrounding slices."
		if layerIndex < 0 or layerIndex >= len( self.rotatedLayers ):
			return
		layer = self.rotatedLayers[ layerIndex ].boundaries
		rotatedSlice = []
		for thread in layer:
			planeRotatedLoop = euclidean.getPathRoundZAxisByPlaneAngle( reverseRotationAroundZAngle, thread )
			rotatedSlice.append( planeRotatedLoop )
		surroundingSlices.append( rotatedSlice )

	def addShutdownToOutput( self ):
		"Add shutdown gcode to the output."
		for line in self.lines[ self.shutdownLineIndex : ]:
			self.addLine( line )

	def addToThread( self, location ):
		"Add a location to thread."
		if self.oldLocation == None:
			return
		if self.surroundingLoop != None:
			if self.isPerimeter:
				if self.surroundingLoop.loop == None:
					self.surroundingLoop.loop = []
				self.surroundingLoop.loop.append( location )
				return
			elif self.thread == None:
				self.thread = [ self.oldLocation ]
				self.surroundingLoop.perimeterPaths.append( self.thread )
		self.thread.append( location )

	def getLayerRoundZ( self, layerIndex ):
		"Get the plane angle around z that the layer is rotated by."
		rotation = self.rotatedLayers[ layerIndex ].rotation
		if rotation != None:
			return rotation
		return euclidean.getPolar( self.infillBeginRotation + float( ( layerIndex % 2 ) * self.infillOddLayerExtraRotation ), 1.0 )

	def getRotatedLayer( self ):
		"Get the rotated layer, making a new one if necessary."
		if self.rotatedLayer == None:
			self.rotatedLayer = RotatedLayer()
			self.rotatedLayers.append( self.rotatedLayer )
		return self.rotatedLayer

	def getRounded( self, number ):
		"Get number rounded to the number of carried decimal places as a string."
		return euclidean.getRoundedToDecimalPlaces( self.decimalPlacesCarried, number )

	def linearMove( self, splitLine ):
		"Add a linear move to the thread."
		location = gcodec.getLocationFromSplitLine( self.oldLocation, splitLine )
		if self.extruderActive:
			self.addToThread( location )
		self.oldLocation = location

	def parseGcode( self, fillPreferences, gcodeText ):
		"Parse gcode text and store the bevel gcode."
		self.fillPreferences = fillPreferences
		self.lines = gcodec.getTextLines( gcodeText )
		self.parseInitialization()
		self.infillDensity = fillPreferences.infillDensity.value
		self.infillBeginRotation = math.radians( fillPreferences.infillBeginRotation.value )
		self.infillOddLayerExtraRotation = math.radians( fillPreferences.infillOddLayerExtraRotation.value )
		self.solidSurfaceThickness = int( round( self.fillPreferences.solidSurfaceThickness.value ) )
		self.doubleSolidSurfaceThickness = self.solidSurfaceThickness + self.solidSurfaceThickness
		for lineIndex in range( self.lineIndex, len( self.lines ) ):
			self.parseLine( lineIndex )
		for layerIndex in range( len( self.rotatedLayers ) ):
			self.addFill( layerIndex )
		self.addShutdownToOutput()

	def parseInitialization( self ):
		"Parse gcode initialization and store the parameters."
		for self.lineIndex in range( len( self.lines ) ):
			line = self.lines[ self.lineIndex ]
			splitLine = line.split()
			firstWord = ''
			if len( splitLine ) > 0:
				firstWord = splitLine[ 0 ]
			if firstWord == '(<bridgeExtrusionWidthOverSolid>':
				self.bridgeExtrusionWidthOverSolid = float( splitLine[ 1 ] )
			elif firstWord == '(<decimalPlacesCarried>':
				self.decimalPlacesCarried = int( splitLine[ 1 ] )
			elif firstWord == '(<extrusionWidth>':
				self.extrusionWidth = float( splitLine[ 1 ] )
			elif firstWord == '(<extrusionStart>':
				self.addLine( '(<procedureDone> fill )' )
				self.addLine( line )
				return
			elif firstWord == '(<fillInset>':
				self.fillInset = float( splitLine[ 1 ] )
			self.addLine( line )

	def parseLine( self, lineIndex ):
		"Parse a gcode line and add it to the fill skein."
		line = self.lines[ lineIndex ]
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
			self.thread = None
			self.isPerimeter = False
		elif firstWord == '(<boundaryPoint>':
			location = gcodec.getLocationFromSplitLine( None, splitLine )
			self.surroundingLoop.boundary.append( location )
		elif firstWord == '(<bridgeDirection>':
			secondWordWithoutBrackets = splitLine[ 1 ].replace( '(', '' ).replace( ')', '' )
			self.getRotatedLayer().rotation = complex( secondWordWithoutBrackets )
		elif firstWord == '(</extrusionStart>':
			self.shutdownLineIndex = lineIndex
		elif firstWord == '(<layerStart>':
			self.rotatedLayer = None
			self.thread = None
		elif firstWord == '(<perimeter>':
			self.isPerimeter = True
		elif firstWord == '(<surroundingLoop>':
			self.surroundingLoop = euclidean.SurroundingLoop()
			rotatedLayer = self.getRotatedLayer()
			rotatedLayer.surroundingLoops.append( self.surroundingLoop )
			rotatedLayer.boundaries.append( self.surroundingLoop.boundary )
		elif firstWord == '(</surroundingLoop>':
			self.surroundingLoop = None


class RotatedLayer:
	"A rotated layer."
	def __init__( self ):
		self.boundaries = []
		self.rotation = None
		self.surroundingLoops = []

	def __repr__( self ):
		"Get the string representation of this RotatedLayer."
		return '%s, %s, %s' % ( self.rotation, self.surroundingLoops, self.boundaries )


class StretchedXSegment:
	"A stretched x segment."
	def __repr__( self ):
		"Get the string representation of this StretchedXSegment."
		return str( self.xMinimum ) + ' ' + str( self.xMaximum ) + ' ' + str( self.y )

	def getFromXYStretch( self, firstX, y, secondX, stretch ):
		"Initialize from x, y, and stretch."
		self.xMaximum = max( firstX, secondX ) + stretch
		self.xMinimum = min( firstX, secondX ) - stretch
		self.y = y
		return self


class YIntersectionPath:
	"A class to hold the y intersection position, the loop which it intersected and the point index of the loop which it intersected."
	def __init__( self, path, pointIndex, y ):
		"Initialize from the path, point index, and y."
		self.path = path
		self.pointIndex = pointIndex
		self.y = y

	def __repr__( self ):
		"Get the string representation of this y intersection."
		return '%s, %s, %s' % ( self.path, self.pointIndex, self.y )


def main( hashtable = None ):
	"Display the fill dialog."
	if len( sys.argv ) > 1:
		writeOutput( ' '.join( sys.argv[ 1 : ] ) )
	else:
		preferences.displayDialog( FillPreferences() )

if __name__ == "__main__":
	main()

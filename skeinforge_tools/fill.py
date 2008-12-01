#! /usr/bin/env python
"""
Fill is a script to fill the slices of a gcode file.

The diaphragm is a solid group of layers, at regular intervals.  It can be used with a sparse infill to give the object watertight, horizontal
compartments and/or a higher shear strength.  The "Diaphragm Period" is the number of layers between diaphrams.  The "Diaphragm
Thickness" is the number of layers the diaphram is composed of.  The default diaphragm is zero, because the diaphragm feature is rarely
used.

The "Extra Shells on Alternating Solid Layers" preference is the number of extra shells, which are interior perimeter loops, on the alternating
solid layers.  The "Extra Shells on Base" preference is the number of extra shells on the bottom, base layer and every even solid layer after
that.  Setting this to a different value than the "Extra Shells on Alternating Solid Layers" means the infill pattern will alternate, creating a
strong interleaved bond even if the perimeter loop shrinks.  The "Extra Shells on Sparse Layer" preference is the number of extra shells on
the sparse layers.  The solid layers are those at the top & bottom, and wherever the object has a plateau or overhang, the sparse layers are
the layers in between.  Adding extra shells makes the object stronger & heavier.

The "Grid Extra Overlap" preference is the amount of extra overlap added when extruding the grid to compensate for the fact that when the
first thread going through a grid point is extruded, since there is nothing there yet for it to connect to it will shrink extra.  The "Grid Square
Half Width over Extrusion Width" preference is the ratio of the amount the grid square is increased in each direction over the extrusion
width, the default is zero.  With a value of one or so the grid pattern will have large squares to go with the octogons.  The "Infill Pattern"
can be set to "Grid" or "Line".  The grid option makes a funky octogon square honeycomb like pattern which gives the object extra strength.
However, the  grid pattern means extra turns for the extruder and therefore extra wear & tear, also it takes longer to generate, so the
default is line.  The grid has extra diagonal lines, so when choosing the grid option, set the infill solidity to 0.2 or less so that there is not
too much plastic and the grid generation time, which increases with the fourth power of solidity, will be reasonable.

The "Infill Begin Rotation" preference is the amount the infill direction of the base and every second layer thereafter is rotated.  The default
value of forty five degrees gives a diagonal infill.  The "Infill Odd Layer Extra Rotation" preference is the extra amount the infill direction of
the odd layers is rotated compared to the base layer.  With the default value of ninety degrees the odd layer infill will be perpendicular to
the base layer.  The "Infill Begin Rotation Repeat" preference is the number of layers that the infill begin rotation will repeat.  With the
default of one, the object will have alternating cross hatching.  With a value higher than one, the infill will go in one direction more often,
giving the object more strength in one direction and less in the other, this is useful for beams and cantilevers.

The most important preference in fill is the "Infill Solidity".  A value of one means the infill lines will be right beside each other, resulting in a
solid, strong, heavy shape which takes a long time to extrude.  A low value means the infill will be sparse, the interior will be mosty empty
space, the object will be weak, light and quick to build.  The default is 0.2.

The "Interior Infill Density over Exterior Density" preference is the ratio of the infill density of the interior over the infill density of the exterior
surfaces, the default is 0.9.  The exterior should have a high infill density, so that the surface will be strong and watertight.  With the
interior infill density a bit lower than the exterior, the plastic will not fill up higher than the extruder nozzle.  If the interior density is too high
that could happen, as Nophead described in the Hydraraptor "Bearing Fruit" post at:
http://hydraraptor.blogspot.com/2008/08/bearing-fruit.html

The "Solid Surface Thickness" preference is the number of solid layers that are at the bottom, top, plateaus and overhang.  With a value of
zero, the entire object will be composed of a sparse infill, and water could flow right through it.  With a value of one, water will leak slowly
through the surface and with a value of three, the object could be watertight.  The higher the solid surface thickness, the stronger and
heavier the object will be.  The default is three.

The following examples fill the files Hollow Square.gcode & Hollow Square.gts.  The examples are run in a terminal in the folder which
contains Hollow Square.gcode, Hollow Square.gts and fill.py.


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

#slice infill density documentation, oozebane to handle minimum start up, add differential flow rates
#multiply
#use slice format, carve & inset, slice aoi xml
#bridge extrusion width
#pyramidal
#change material
#skeinedge
#compartmentalize addOrbit
#distance option?
#document gear script
#email marcus about bridge extrusion width http://reprap.org/bin/view/Main/ExtruderImprovementsAndAlternatives
#mosaic
#gang, maybe from skeinedge?
#transform
#pick and place
#stack
#infill first
#rulers & z on skeinview
#searchable help
#faster, sort intercircle?
#extrude loops I guess make circles? and/or run along sparse infill
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

def addAroundGridPoint( arounds, gridPoint, gridPointInsetX, gridPointInsetY, gridPoints, gridSearchRadius, isBothOrNone, isDoubleJunction, isJunctionWide, paths, pixelTable, width ):
	"Add the path around the grid point."
	closestPathIndex = None
	aroundIntersectionPaths = []
	for aroundIndex in range( len( arounds ) ):
		loop = arounds[ aroundIndex ]
		for pointIndex in xrange( len( loop ) ):
			pointFirst = loop[ pointIndex ]
			pointSecond = loop[ ( pointIndex + 1 ) % len( loop ) ]
			yIntersection = getYIntersectionIfExists( pointFirst, pointSecond, gridPoint.x )
			addYIntersectionPathToList( aroundIndex, pointIndex, gridPoint.y, yIntersection, aroundIntersectionPaths )
	if len( aroundIntersectionPaths ) < 2:
		print( 'This should never happen, aroundIntersectionPaths is less than 2 in fill.' )
		print( aroundIntersectionPaths )
		print( gridPoint )
		print( arounds )
		return
	yCloseToCenterArounds = getClosestOppositeIntersectionPaths( aroundIntersectionPaths )
	if len( yCloseToCenterArounds ) < 2:
		print( 'This should never happen, yCloseToCenterArounds is less than 2 in fill.' )
		print( yCloseToCenterArounds )
		print( gridPoint )
		print( arounds )
		return
	segmentFirstY = min( yCloseToCenterArounds[ 0 ].y, yCloseToCenterArounds[ 1 ].y )
	segmentSecondY = max( yCloseToCenterArounds[ 0 ].y, yCloseToCenterArounds[ 1 ].y )
	yIntersectionPaths = []
	for pathIndex in range( len( paths ) ):
		path = paths[ pathIndex ]
		for pointIndex in xrange( len( path ) - 1 ):
			pointFirst = path[ pointIndex ]
			pointSecond = path[ pointIndex + 1 ]
			yIntersection = getYIntersectionInsideYSegment( segmentFirstY, segmentSecondY, pointFirst, pointSecond, gridPoint.x )
			addYIntersectionPathToList( pathIndex, pointIndex, gridPoint.y, yIntersection, yIntersectionPaths )
	if len( yIntersectionPaths ) < 1:
		return
	yCloseToCenterPaths = []
	if isDoubleJunction:
		yCloseToCenterPaths = getClosestOppositeIntersectionPaths( yIntersectionPaths )
	else:
		yIntersectionPaths.sort( compareDistanceFromCenter )#
		yCloseToCenterPaths = [ yIntersectionPaths[ 0 ] ]#
	for yCloseToCenterPath in yCloseToCenterPaths:
		setIsOutside( yCloseToCenterPath, yIntersectionPaths )
	if len( yCloseToCenterPaths ) < 2:
		yCloseToCenterPaths[ 0 ].gridPoint = gridPoint
		insertGridPointPair( arounds, gridPoint, gridPointInsetX, gridPoints, isJunctionWide, paths, pixelTable, yCloseToCenterPaths[ 0 ], width )
		return
	plusMinusSign = getPlusMinusSign( yCloseToCenterPaths[ 1 ].y - yCloseToCenterPaths[ 0 ].y )
	yCloseToCenterPaths[ 0 ].gridPoint = Vec3( gridPoint.x, gridPoint.y - plusMinusSign * gridPointInsetY, gridPoint.z )
	yCloseToCenterPaths[ 1 ].gridPoint = Vec3( gridPoint.x, gridPoint.y + plusMinusSign * gridPointInsetY, gridPoint.z )
	yCloseToCenterPaths.sort( comparePointIndexDescending )
	insertGridPointPairs( arounds, gridPoint, gridPointInsetX, gridPoints, yCloseToCenterPaths[ 0 ], yCloseToCenterPaths[ 1 ], isBothOrNone, isJunctionWide, paths, pixelTable, width )

def addPath( extrusionWidth, fill, path, rotationPlaneAngle ):
	"Add simplified path to fill."
	planeRotated = euclidean.getPathRoundZAxisByPlaneAngle( rotationPlaneAngle, euclidean.getSimplifiedPath( path, extrusionWidth ) )
	fill.append( planeRotated )

def addPointOnPath( path, pixelTable, point, pointIndex, width ):
	"Add a point to a path and the pixel table."
	pointIndexMinusOne = pointIndex - 1
	pointComplex = point.dropAxis( 2 )
	if pointIndex < len( path ) and pointIndexMinusOne >= 0:
		segmentTable = {}
		beginComplex = path[ pointIndexMinusOne ].dropAxis( 2 )
		endComplex = path[ pointIndex ].dropAxis( 2 )
		euclidean.addSegmentToPixelTable( beginComplex, endComplex, segmentTable, 0.0, 0.0, width )
		euclidean.removePixelTableFromPixelTable( segmentTable, pixelTable )
	if pointIndexMinusOne >= 0:
		beginComplex = path[ pointIndexMinusOne ].dropAxis( 2 )
		euclidean.addSegmentToPixelTable( beginComplex, pointComplex, pixelTable, 0.0, 0.0, width )
	if pointIndex < len( path ):
		endComplex = path[ pointIndex ].dropAxis( 2 )
		euclidean.addSegmentToPixelTable( pointComplex, endComplex, pixelTable, 0.0, 0.0, width )
	path.insert( pointIndex, point )

def addShortenedLineSegment( lineSegment, shortenDistance, shortenedSegments ):
	"Add shortened line segment."
	pointBegin = lineSegment[ 0 ].point
	pointEnd = lineSegment[ 1 ].point
	segment = pointEnd.minus( pointBegin )
	segmentLength = segment.lengthXYPlane()
	if segmentLength < 2.1 * shortenDistance:
		return
	segmentShorten = segment.times( shortenDistance / segmentLength )
	lineSegment[ 0 ].point = pointBegin.plus( segmentShorten )
	lineSegment[ 1 ].point = pointEnd.minus( segmentShorten )
	shortenedSegments.append( lineSegment )

def addSparseEndpoints( doubleExtrusionWidth, endpoints, fillLine, horizontalSegments, infillSolidity, removedEndpoints, solidSurfaceThickness, surroundingXIntersections ):
	"Add sparse endpoints."
	horizontalEndpoints = horizontalSegments[ fillLine ]
	for segment in horizontalEndpoints:
		addSparseEndpointsFromSegment( doubleExtrusionWidth, endpoints, fillLine, horizontalSegments, infillSolidity, removedEndpoints, segment, solidSurfaceThickness, surroundingXIntersections )

def addSparseEndpointsFromSegment( doubleExtrusionWidth, endpoints, fillLine, horizontalSegments, infillSolidity, removedEndpoints, segment, solidSurfaceThickness, surroundingXIntersections ):
	"Add sparse endpoints from a segment."
	endpointFirstPoint = segment[ 0 ].point
	endpointSecondPoint = segment[ 1 ].point
	if fillLine < 1 or fillLine >= len( horizontalSegments ) - 1 or surroundingXIntersections == None:
		endpoints += segment
		return
	if infillSolidity > 0.0:
		if int( round( round( fillLine * infillSolidity ) / infillSolidity ) ) == fillLine:
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
	if isSegmentCompletelyInAnIntersection( segment, surroundingXIntersections ):
		removedEndpoints += segment
		return
	endpoints += segment

def addSurroundingXIntersectionIndexes( surroundingSlices, xIntersectionIndexList, y ):
	"Add x intersection indexes from surrounding layers."
	for surroundingIndex in range( len( surroundingSlices ) ):
		surroundingSlice = surroundingSlices[ surroundingIndex ]
		euclidean.addXIntersectionIndexesFromLoops( surroundingSlice, surroundingIndex, xIntersectionIndexList, y )

def addYIntersectionPathToList( pathIndex, pointIndex, y, yIntersection, yIntersectionPaths ):
	"Add the y intersection path to the y intersection paths."
	if yIntersection == None:
		return
	yIntersectionPath = YIntersectionPath( pathIndex, pointIndex, yIntersection )
	yIntersectionPath.yMinusCenter = yIntersection - y
	yIntersectionPaths.append( yIntersectionPath )

def compareDistanceFromCenter( self, other ):
	"Get comparison in order to sort y intersections in ascending order of distance from the center."
	distanceFromCenter = abs( self.yMinusCenter )
	distanceFromCenterOther = abs( other.yMinusCenter )
	if distanceFromCenter > distanceFromCenterOther:
		return 1
	if distanceFromCenter < distanceFromCenterOther:
		return - 1
	return 0

def comparePointIndexDescending( self, other ):
	"Get comparison in order to sort y intersections in descending order of point index."
	if self.pointIndex > other.pointIndex:
		return - 1
	if self.pointIndex < other.pointIndex:
		return 1
	return 0

def createFillForSurroundings( radius, surroundingLoops ):
	"Create extra fill loops for surrounding loops."
	for surroundingLoop in surroundingLoops:
		createExtraFillLoops( radius, surroundingLoop )

def createExtraFillLoops( radius, surroundingLoop ):
	"Create extra fill loops."
	for innerSurrounding in surroundingLoop.innerSurroundings:
		createFillForSurroundings( radius, innerSurrounding.innerSurroundings )
	outsides = []
	insides = euclidean.getInsidesAddToOutsides( surroundingLoop.getFillLoops(), outsides )
	allFillLoops = []
	for outside in outsides:
		transferredLoops = euclidean.getTransferredPaths( insides, outside )
		allFillLoops += getExtraFillLoops( transferredLoops, outside, radius )
	if len( allFillLoops ) > 0:
		surroundingLoop.lastFillLoops = allFillLoops
	surroundingLoop.extraLoops += allFillLoops

def getClosestOppositeIntersectionPaths( yIntersectionPaths ):
	"Get the close to center paths, starting with the first and an additional opposite if it exists."
	yIntersectionPaths.sort( compareDistanceFromCenter )
	beforeFirst = yIntersectionPaths[ 0 ].yMinusCenter < 0.0
	yCloseToCenterPaths = [ yIntersectionPaths[ 0 ] ]
	for yIntersectionPath in yIntersectionPaths[ 1 : ]:
		beforeSecond = yIntersectionPath.yMinusCenter < 0.0
		if beforeFirst != beforeSecond:
			yCloseToCenterPaths.append( yIntersectionPath )
			return yCloseToCenterPaths
	return yCloseToCenterPaths

def getExtraFillLoops( insideLoops, outsideLoop, radius ):
	"Get extra loops between inside and outside loops."
	greaterThanRadius = 1.4 * radius
	muchGreaterThanRadius = 2.5 * radius
	extraFillLoops = []
	circleNodes = intercircle.getCircleNodesFromLoop( outsideLoop, greaterThanRadius )
	for inside in insideLoops:
		circleNodes += intercircle.getCircleNodesFromLoop( inside, greaterThanRadius )
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

def getHorizontalSegmentsFromLoopLists( fillLoops, alreadyFilledArounds, y ):
	"Get horizontal segments inside loops."
	xIntersectionIndexList = []
	euclidean.addXIntersectionIndexesFromLoops( fillLoops, - 1, xIntersectionIndexList, y )
	euclidean.addXIntersectionIndexesFromLoopLists( alreadyFilledArounds, xIntersectionIndexList, y )
	return euclidean.getSegmentsFromXIntersectionIndexes( xIntersectionIndexList, y, fillLoops[ 0 ][ 0 ].z )

def getIntersectionOfXIntersectionIndexes( totalSolidSurfaceThickness, xIntersectionIndexList ):
	"Get x intersections from surrounding layers."
	xIntersectionList = []
	solidTable = {}
	solid = False
	xIntersectionIndexList.sort()
	for xIntersectionIndex in xIntersectionIndexList:
		euclidean.toggleHashtable( solidTable, xIntersectionIndex.index, "" )
		oldSolid = solid
		solid = len( solidTable ) >= totalSolidSurfaceThickness
		if oldSolid != solid:
			xIntersectionList.append( xIntersectionIndex.x )
	return xIntersectionList

def getNonIntersectingGridPointLine( arounds, gridPointInsetX, isJunctionWide, paths, pixelTable, yIntersectionPath, width ):
	"Get the points around the grid point that is junction wide that do not intersect."
	pointIndexPlusOne = yIntersectionPath.getPointIndexPlusOne()
	path = yIntersectionPath.getPath( paths )
	begin = path[ yIntersectionPath.pointIndex ]
	end = path[ pointIndexPlusOne ]
	plusMinusSign = getPlusMinusSign( end.x - begin.x )
	if isJunctionWide:
		gridPointXFirst = Vec3( yIntersectionPath.gridPoint.x - plusMinusSign * gridPointInsetX, yIntersectionPath.gridPoint.y, yIntersectionPath.gridPoint.z )
		gridPointXSecond = Vec3( yIntersectionPath.gridPoint.x + plusMinusSign * gridPointInsetX, yIntersectionPath.gridPoint.y, yIntersectionPath.gridPoint.z )
		if isAddedPointOnPathFree( path, pixelTable, gridPointXSecond, pointIndexPlusOne, width ):
			if isAddedPointOnPathFree( path, pixelTable, gridPointXFirst, pointIndexPlusOne, width ):
				return [ gridPointXSecond, gridPointXFirst ]
			if isAddedPointOnPathFree( path, pixelTable, yIntersectionPath.gridPoint, pointIndexPlusOne, width ):
				return [ gridPointXSecond, yIntersectionPath.gridPoint ]
			return [ gridPointXSecond ]
	if isAddedPointOnPathFree( path, pixelTable, yIntersectionPath.gridPoint, pointIndexPlusOne, width ):
		return [ yIntersectionPath.gridPoint ]
	return []

def getPlusMinusSign( number ):
	"Get one if the number is zero or positive else negative one."
	if number >= 0.0:
		return 1.0
	return - 1.0

def getSurroundingXIntersections( doubleSolidSurfaceThickness, surroundingSlices, y ):
	"Get x intersections from surrounding layers."
	xIntersectionIndexList = []
	addSurroundingXIntersectionIndexes( surroundingSlices, xIntersectionIndexList, y )
	if len( surroundingSlices ) < doubleSolidSurfaceThickness:
		return None
	return getIntersectionOfXIntersectionIndexes( doubleSolidSurfaceThickness, xIntersectionIndexList )

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

def getYIntersectionIfExists( vector3First, vector3Second, x ):
	"Get the y intersection if it exists."
	isXAboveFirst = x > vector3First.x
	isXAboveSecond = x > vector3Second.x
	if isXAboveFirst == isXAboveSecond:
		return None
	return getYIntersection( vector3First, vector3Second, x )

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

def insertGridPointPair( arounds, gridPoint, gridPointInsetX, gridPoints, isJunctionWide, paths, pixelTable, yIntersectionPath, width ):
	"Insert a pair of points around the grid point is is junction wide, otherwise inset one point."
	linePath = getNonIntersectingGridPointLine( arounds, gridPointInsetX, isJunctionWide, paths, pixelTable, yIntersectionPath, width )
	insertGridPointPairWithLinePath( arounds, gridPoint, gridPointInsetX, gridPoints, isJunctionWide, linePath, paths, pixelTable, yIntersectionPath, width )

def insertGridPointPairs( arounds, gridPoint, gridPointInsetX, gridPoints, intersectionPathFirst, intersectionPathSecond, isBothOrNone, isJunctionWide, paths, pixelTable, width ):
	"Insert a pair of points around a pair of grid points."
	gridPointLineFirst = getNonIntersectingGridPointLine( arounds, gridPointInsetX, isJunctionWide, paths, pixelTable, intersectionPathFirst, width )
	if len( gridPointLineFirst ) < 1:
		if isBothOrNone:
			return
		intersectionPathSecond.gridPoint = gridPoint
		insertGridPointPair( arounds, gridPoint, gridPointInsetX, gridPoints, isJunctionWide, paths, pixelTable, intersectionPathSecond, width )
		return
	gridPointLineSecond = getNonIntersectingGridPointLine( arounds, gridPointInsetX, isJunctionWide, paths, pixelTable, intersectionPathSecond, width )
	if len( gridPointLineSecond ) > 0:
		insertGridPointPairWithLinePath( arounds, gridPoint, gridPointInsetX, gridPoints, isJunctionWide, gridPointLineFirst, paths, pixelTable, intersectionPathFirst, width )
		insertGridPointPairWithLinePath( arounds, gridPoint, gridPointInsetX, gridPoints, isJunctionWide, gridPointLineSecond, paths, pixelTable, intersectionPathSecond, width )
		return
	if isBothOrNone:
		return
	originalGridPointFirst = intersectionPathFirst.gridPoint
	intersectionPathFirst.gridPoint = gridPoint
	gridPointLineFirstCenter = getNonIntersectingGridPointLine( arounds, gridPointInsetX, isJunctionWide, paths, pixelTable, intersectionPathFirst, width )
	if len( gridPointLineFirstCenter ) > 0:
		insertGridPointPairWithLinePath( arounds, gridPoint, gridPointInsetX, gridPoints, isJunctionWide, gridPointLineFirstCenter, paths, pixelTable, intersectionPathFirst, width )
		return
	intersectionPathFirst.gridPoint = originalGridPointFirst
	insertGridPointPairWithLinePath( arounds, gridPoint, gridPointInsetX, gridPoints, isJunctionWide, gridPointLineFirst, paths, pixelTable, intersectionPathFirst, width )

def insertGridPointPairWithLinePath( arounds, gridPoint, gridPointInsetX, gridPoints, isJunctionWide, linePath, paths, pixelTable, yIntersectionPath, width ):
	"Insert a pair of points around the grid point is is junction wide, otherwise inset one point."
	if len( linePath ) < 1:
		return
	if gridPoint in gridPoints:
		gridPoints.remove( gridPoint )
	intersectionBeginPoint = None
	moreThanInset = 2.1 * gridPointInsetX
	path = yIntersectionPath.getPath( paths )
	begin = path[ yIntersectionPath.pointIndex ]
	end = path[ yIntersectionPath.getPointIndexPlusOne() ]
	if yIntersectionPath.isOutside:
		distanceX = end.x - begin.x
		if abs( distanceX ) > 2.1 * moreThanInset:
			intersectionBeginXDistance = yIntersectionPath.gridPoint.x - begin.x
			endIntersectionXDistance = end.x - yIntersectionPath.gridPoint.x
			intersectionPoint = begin.times( endIntersectionXDistance / distanceX ).plus( end.times( intersectionBeginXDistance / distanceX ) )
			distanceYAbsoluteInset = max( abs( yIntersectionPath.gridPoint.y - intersectionPoint.y ), moreThanInset )
			intersectionEndSegment = end.minus( intersectionPoint )
			intersectionEndSegmentLength = intersectionEndSegment.length()
			if intersectionEndSegmentLength > 1.1 * distanceYAbsoluteInset:
				intersectionEndPoint = intersectionPoint.plus( intersectionEndSegment.times( distanceYAbsoluteInset / intersectionEndSegmentLength ) )
				path.insert( yIntersectionPath.getPointIndexPlusOne(), intersectionEndPoint )
			intersectionBeginSegment = begin.minus( intersectionPoint )
			intersectionBeginSegmentLength = intersectionBeginSegment.length()
			if intersectionBeginSegmentLength > 1.1 * distanceYAbsoluteInset:
				intersectionBeginPoint = intersectionPoint.plus( intersectionBeginSegment.times( distanceYAbsoluteInset / intersectionBeginSegmentLength ) )
	for point in linePath:
		addPointOnPath( path, pixelTable, point, yIntersectionPath.getPointIndexPlusOne(), width )
	if intersectionBeginPoint != None:
		addPointOnPath( path, pixelTable, intersectionBeginPoint, yIntersectionPath.getPointIndexPlusOne(), width )

def isAddedPointOnPathFree( path, pixelTable, point, pointIndex, width ):
	"Determine if the point added to a path is intersecting the pixel table."
	pointComplex = point.dropAxis( 2 )
	if pointIndex > 0 and pointIndex < len( path ):
		if isSharpCorner( ( path[ pointIndex - 1 ] ).dropAxis( 2 ), pointComplex, ( path[ pointIndex ] ).dropAxis( 2 ) ):
			return False
	pointIndexMinusOne = pointIndex - 1
	if pointIndexMinusOne >= 0:
		maskTable = {}
		beginComplex = path[ pointIndexMinusOne ].dropAxis( 2 )
		if pointIndex < len( path ):
			endComplex = path[ pointIndex ].dropAxis( 2 )
			euclidean.addSegmentToPixelTable( beginComplex, endComplex, maskTable, 0.0, 0.0, width )
		segmentTable = {}
		euclidean.addSegmentToPixelTable( pointComplex, beginComplex, segmentTable, 0.0, 3.0, width )
		if euclidean.isPixelTableIntersecting( pixelTable, segmentTable, maskTable ):
			return False
	if pointIndex < len( path ):
		maskTable = {}
		beginComplex = path[ pointIndex ].dropAxis( 2 )
		if pointIndexMinusOne >= 0:
			endComplex = path[ pointIndexMinusOne ].dropAxis( 2 )
			euclidean.addSegmentToPixelTable( beginComplex, endComplex, maskTable, 0.0, 0.0, width )
		segmentTable = {}
		euclidean.addSegmentToPixelTable( pointComplex, beginComplex, segmentTable, 0.0, 3.0, width )
		if euclidean.isPixelTableIntersecting( pixelTable, segmentTable, maskTable ):
			return False
	return True

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

def isPointAddedAroundClosest( aroundPixelTable, layerExtrusionWidth, paths, removedEndpointPoint, width ):
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
	if isAddedPointOnPathFree( closestPath, aroundPixelTable, removedEndpointPoint, closestPointIndex, width ):
		addPointOnPath( closestPath, aroundPixelTable, removedEndpointPoint, closestPointIndex, width )
		return True
	return isSidePointAdded( aroundPixelTable, closestPath, closestPointIndex, layerExtrusionWidth, removedEndpointPoint, width )

def isSegmentAround( aroundSegments, segment ):
	"Determine if there is another segment around."
	for aroundSegment in aroundSegments:
		endpoint = aroundSegment[ 0 ]
		if isSegmentInX( segment, endpoint.point.x, endpoint.otherEndpoint.point.x ):
			return True
	return False

def isSegmentCompletelyInAnIntersection( segment, xIntersections ):
	"Add sparse endpoints from a segment."
	for xIntersectionIndex in xrange( 0, len( xIntersections ), 2 ):
		surroundingXFirst = xIntersections[ xIntersectionIndex ]
		surroundingXSecond = xIntersections[ xIntersectionIndex + 1 ]
		if euclidean.isSegmentCompletelyInX( segment, surroundingXFirst, surroundingXSecond ):
			return True
	return False

def isSegmentInX( segment, xFirst, xSecond ):
	"Determine if the segment overlaps within x."
	segmentFirstX = segment[ 0 ].point.x
	segmentSecondX = segment[ 1 ].point.x
	if min( segmentFirstX, segmentSecondX ) > max( xFirst, xSecond ):
		return False
	return max( segmentFirstX, segmentSecondX ) > min( xFirst, xSecond )

def isSharpCorner( beginComplex, centerComplex, endComplex ):
	"Determine if the three complex points form a sharp corner."
	centerBeginComplex = beginComplex - centerComplex
	centerEndComplex = endComplex - centerComplex
	centerBeginLength = abs( centerBeginComplex )
	centerEndLength = abs( centerEndComplex )
	if centerBeginLength <= 0.0 or centerEndLength <= 0.0:
		return False
	centerBeginComplex /= centerBeginLength
	centerEndComplex /= centerEndLength
	return euclidean.getComplexDot( centerBeginComplex, centerEndComplex ) > 0.9

def isSidePointAdded( aroundPixelTable, closestPath, closestPointIndex, layerExtrusionWidth, removedEndpointPoint, width ):
	"Add side point along with the closest removed endpoint to the path, with minimal twisting."
	if closestPointIndex <= 0 or closestPointIndex >= len( closestPath ):
		return False
	pointBeginComplex = closestPath[ closestPointIndex - 1 ].dropAxis( 2 )
	pointEndComplex = closestPath[ closestPointIndex ].dropAxis( 2 )
	removedEndpointPointComplex = removedEndpointPoint.dropAxis( 2 )
	closestComplex = pointBeginComplex
	farthestComplex = pointEndComplex
	removedMinusClosest = removedEndpointPointComplex - pointBeginComplex
	removedMinusClosestLength = abs( removedMinusClosest )
	if removedMinusClosestLength <= 0.0:
		return False
	removedMinusOther = removedEndpointPointComplex - pointEndComplex
	removedMinusOtherLength = abs( removedMinusOther )
	if removedMinusOtherLength <= 0.0:
		return False
	insertPointAfter = None
	insertPointBefore = None
	if removedMinusOtherLength < removedMinusClosestLength:
		closestComplex = pointEndComplex
		farthestComplex = pointBeginComplex
		removedMinusClosest = removedMinusOther
		removedMinusClosestLength = removedMinusOtherLength
		insertPointBefore = removedEndpointPoint
	else:
		insertPointAfter = removedEndpointPoint
	removedMinusClosestNormalized = removedMinusClosest / removedMinusClosestLength
	perpendicularComplex = removedMinusClosestNormalized * complex( 0.0, layerExtrusionWidth )
	sidePointComplex = removedEndpointPointComplex + perpendicularComplex
	#extra check in case the line to the side point somehow slips by the line to the perpendicular
	sidePointOtherComplex = removedEndpointPointComplex - perpendicularComplex
	if abs( sidePointComplex -  farthestComplex ) > abs( sidePointOtherComplex -  farthestComplex ):
		perpendicularComplex = - perpendicularComplex
		sidePointComplex = sidePointOtherComplex
	maskTable = {}
	closestSegmentTable = {}
	toPerpendicularTable = {}
	euclidean.addSegmentToPixelTable( pointBeginComplex, pointEndComplex, maskTable, 1.0, 1.0, width )
	euclidean.addSegmentToPixelTable( closestComplex, removedEndpointPointComplex, closestSegmentTable, 0.0, 0.0, width )
	euclidean.addSegmentToPixelTable( sidePointComplex, farthestComplex, toPerpendicularTable, 0.0, 3.0, width )
	if euclidean.isPixelTableIntersecting( aroundPixelTable, toPerpendicularTable, maskTable ) or euclidean.isPixelTableIntersecting( closestSegmentTable, toPerpendicularTable, maskTable ):
		sidePointComplex = removedEndpointPointComplex - perpendicularComplex
		toPerpendicularTable = {}
		euclidean.addSegmentToPixelTable( sidePointComplex, farthestComplex, toPerpendicularTable, 0.0, 3.0, width )
		if euclidean.isPixelTableIntersecting( aroundPixelTable, toPerpendicularTable, maskTable ) or euclidean.isPixelTableIntersecting( closestSegmentTable, toPerpendicularTable, maskTable ):
			return False
	sidePoint = Vec3( sidePointComplex.real, sidePointComplex.imag, removedEndpointPoint.z )
	if insertPointBefore != None:
		addPointOnPath( closestPath, aroundPixelTable, insertPointBefore, closestPointIndex, width )
	addPointOnPath( closestPath, aroundPixelTable, sidePoint, closestPointIndex, width )
	if insertPointAfter != None:
		addPointOnPath( closestPath, aroundPixelTable, insertPointAfter, closestPointIndex, width )
	return True

def removeEndpoints( aroundPixelTable, layerExtrusionWidth, paths, removedEndpoints, aroundWidth ):
	"Remove endpoints which are added to the path."
	for removedEndpointIndex in xrange( len( removedEndpoints ) - 1, - 1, - 1 ):
		removedEndpoint = removedEndpoints[ removedEndpointIndex ]
		removedEndpointPoint = removedEndpoint.point
		if isPointAddedAroundClosest( aroundPixelTable, layerExtrusionWidth, paths, removedEndpointPoint, aroundWidth ):
			removedEndpoints.remove( removedEndpoint )

def setIsOutside( yCloseToCenterPath, yIntersectionPaths ):
	"Determine if the yCloseToCenterPath is outside."
	beforeClose = yCloseToCenterPath.yMinusCenter < 0.0
	for yIntersectionPath in yIntersectionPaths:
		if yIntersectionPath != yCloseToCenterPath:
			beforePath = yIntersectionPath.yMinusCenter < 0.0
			if beforeClose == beforePath:
				yCloseToCenterPath.isOutside = False
				return
	yCloseToCenterPath.isOutside = True

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
		self.gridExtraOverlap = preferences.FloatPreference().getFromValue( 'Grid Extra Overlap (ratio):', 0.1 )
		self.archive.append( self.gridExtraOverlap )
		self.gridJunctionSeparationOverInnerOctogonRadius = preferences.FloatPreference().getFromValue( 'Grid Junction Separation over Inner Octogon Radius (ratio):', 0.0 )
		self.archive.append( self.gridJunctionSeparationOverInnerOctogonRadius )
		self.filenameInput = preferences.Filename().getFromFilename( import_translator.getGNUTranslatorGcodeFileTypeTuples(), 'Open File to be Filled', '' )
		self.archive.append( self.filenameInput )
		self.infillBeginRotation = preferences.FloatPreference().getFromValue( 'Infill Begin Rotation (degrees):', 45.0 )
		self.archive.append( self.infillBeginRotation )
		self.infillBeginRotationRepeat = preferences.IntPreference().getFromValue( 'Infill Begin Rotation Repeat (layers):', 1 )
		self.archive.append( self.infillBeginRotationRepeat )
		self.infillSolidity = preferences.FloatPreference().getFromValue( 'Infill Solidity (ratio):', 0.2 )
		self.archive.append( self.infillSolidity )
		self.infillOddLayerExtraRotation = preferences.FloatPreference().getFromValue( 'Infill Odd Layer Extra Rotation (degrees):', 90.0 )
		self.archive.append( self.infillOddLayerExtraRotation )
		self.infillPatternLabel = preferences.LabelDisplay().getFromName( 'Infill Pattern:' )
		self.archive.append( self.infillPatternLabel )
		infillPatternRadio = []
		self.infillPatternGridHexagonal = preferences.Radio().getFromRadio( 'Grid Hexagonal', infillPatternRadio, False )
		self.archive.append( self.infillPatternGridHexagonal )
		self.infillPatternGridRectangular = preferences.Radio().getFromRadio( 'Grid Rectangular', infillPatternRadio, False )
		self.archive.append( self.infillPatternGridRectangular )
		self.infillPatternLine = preferences.Radio().getFromRadio( 'Line', infillPatternRadio, True )
		self.archive.append( self.infillPatternLine )
		self.interiorInfillDensityOverExteriorDensity = preferences.FloatPreference().getFromValue( 'Interior Infill Density over Exterior Density (ratio):', 0.9 )
		self.archive.append( self.interiorInfillDensityOverExteriorDensity )
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
#		if layerIndex != 17 and layerIndex != 18:
#			return
		alreadyFilledArounds = []
		arounds = []
		layerExtrusionWidth = self.extrusionWidth
		layerFillInset = self.fillInset
		z = self.rotatedLayers[ layerIndex ].surroundingLoops[ 0 ].boundary[ 0 ].z
		self.addLine( '(<layerStart> %s )' % z ) # Indicate that a new layer is starting.
		if self.rotatedLayers[ layerIndex ].rotation != None:
			layerExtrusionWidth = self.extrusionWidth * self.bridgeExtrusionWidthOverSolid
			layerFillInset = self.fillInset * self.bridgeExtrusionWidthOverSolid
			self.addLine( '(<bridgeLayer> )' ) # Indicate that this is a bridge layer.
		gridPointInsetX = 0.5 * layerFillInset
		doubleExtrusionWidth = 2.0 * layerExtrusionWidth
		muchGreaterThanLayerFillInset = 2.5 * layerFillInset
		endpoints = []
		fill = []
		aroundInset = 0.4 * layerFillInset
		aroundWidth = 0.3 * aroundInset
		layerInfillSolidity = self.infillSolidity
		self.isDoubleJunction = True
		self.isJunctionWide = True
		slightlyGreaterThanFill = 1.01 * layerFillInset
		layerRotationAroundZAngle = self.getLayerRoundZ( layerIndex )
		if self.fillPreferences.infillPatternGridHexagonal.value:
			if abs( euclidean.getComplexDot( layerRotationAroundZAngle, euclidean.getPolar( self.infillBeginRotation, 1.0 ) ) ) < math.sqrt( 0.5 ):
				layerInfillSolidity *= 0.5
				self.isDoubleJunction = False
			else:
				self.isJunctionWide = False
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
			radius = layerExtrusionWidth
			if extraShellIndex == 0:
				radius = 0.5  * ( layerExtrusionWidth + self.extrusionPerimeterWidth )
			createFillForSurroundings( radius, surroundingLoops )
		fillLoops = euclidean.getFillOfSurroundings( surroundingLoops )
		aroundPixelTable = {}
		for loop in fillLoops:
			alreadyFilledLoop = []
			alreadyFilledArounds.append( alreadyFilledLoop )
			planeRotatedPerimeter = euclidean.getPathRoundZAxisByPlaneAngle( reverseRotationAroundZAngle, loop )
			rotatedExtruderLoops.append( planeRotatedPerimeter )
			circleNodes = intercircle.getCircleNodesFromLoop( planeRotatedPerimeter, slightlyGreaterThanFill )
			centers = intercircle.getCentersFromCircleNodes( circleNodes )
			euclidean.addLoopToPixelTable( planeRotatedPerimeter, aroundPixelTable, aroundWidth )
			for center in centers:
				alreadyFilledInset = intercircle.getSimplifiedInsetFromClockwiseLoop( center, layerFillInset )
				if euclidean.getMaximumSpan( alreadyFilledInset ) > muchGreaterThanLayerFillInset:
					alreadyFilledLoop.append( alreadyFilledInset )
					around = intercircle.getSimplifiedInsetFromClockwiseLoop( center, aroundInset )
					if euclidean.isPathInsideLoop( planeRotatedPerimeter, around ) == euclidean.isWiddershins( planeRotatedPerimeter ):
						arounds.append( around )
		if len( arounds ) < 1:
			euclidean.addToThreadsRemoveFromSurroundings( self.oldOrderedLocation, surroundingLoops, self )
			return
		back = euclidean.getBackOfLoops( arounds )
		front = euclidean.getFrontOfLoops( arounds )
		area = self.getSliceArea( layerIndex )
		if area > 0.0:
			areaChange = 1.0
			for surroundingIndex in range( 1, self.solidSurfaceThickness + 1 ):
				areaChange = min( areaChange, self.getAreaChange( area, layerIndex - surroundingIndex ) )
				areaChange = min( areaChange, self.getAreaChange( area, layerIndex + surroundingIndex ) )
			if areaChange > 0.5 or self.solidSurfaceThickness == 0:
				layerExtrusionWidth /= self.fillPreferences.interiorInfillDensityOverExteriorDensity.value
		front = math.ceil( front / layerExtrusionWidth ) * layerExtrusionWidth
		fillWidth = back - front
		numberOfLines = int( math.ceil( fillWidth / layerExtrusionWidth ) )
		horizontalSegments = []
		for fillLine in xrange( numberOfLines ):
			y = front + float( fillLine ) * layerExtrusionWidth
			lineSegments = getHorizontalSegmentsFromLoopLists( rotatedExtruderLoops, alreadyFilledArounds, y )
			horizontalSegments.append( lineSegments )
		removedEndpoints = []
		for fillLine in range( len( horizontalSegments ) ):
			y = front + float( fillLine ) * layerExtrusionWidth
			horizontalEndpoints = horizontalSegments[ fillLine ]
			surroundingXIntersections = getSurroundingXIntersections( self.doubleSolidSurfaceThickness, surroundingSlices, y )
			addSparseEndpoints( doubleExtrusionWidth, endpoints, fillLine, horizontalSegments, layerInfillSolidity, removedEndpoints, self.solidSurfaceThickness, surroundingXIntersections )
		if len( endpoints ) < 1:
			euclidean.addToThreadsRemoveFromSurroundings( self.oldOrderedLocation, surroundingLoops, self )
			return
		paths = euclidean.getPathsFromEndpoints( endpoints, layerFillInset, aroundPixelTable, aroundWidth )
		if not self.fillPreferences.infillPatternLine.value:
			self.addGrid( alreadyFilledArounds, arounds, fillLoops, gridPointInsetX, paths, aroundPixelTable, aroundWidth, reverseRotationAroundZAngle, rotatedExtruderLoops, surroundingSlices, z )
		oldRemovedEndpointLength = len( removedEndpoints ) + 1
		while oldRemovedEndpointLength - len( removedEndpoints ) > 0:
			oldRemovedEndpointLength = len( removedEndpoints )
			removeEndpoints( aroundPixelTable, layerExtrusionWidth, paths, removedEndpoints, aroundWidth )
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

	def addGrid( self, alreadyFilledArounds, arounds, fillLoops, gridPointInsetX, paths, pixelTable, width, reverseRotationAroundZAngle, rotatedExtruderLoops, surroundingSlices, z ):
		gridPoints = self.getGridPoints( alreadyFilledArounds, fillLoops, reverseRotationAroundZAngle, rotatedExtruderLoops, surroundingSlices, z )
		gridPointInsetY = gridPointInsetX * ( 1.0 - self.fillPreferences.gridExtraOverlap.value )
		if self.fillPreferences.infillPatternGridRectangular.value:
			gridPointInsetX += self.gridJunctionSeparation
			gridPointInsetY += self.gridJunctionSeparation
		oldGridPointLength = len( gridPoints ) + 1
		while oldGridPointLength - len( gridPoints ) > 0:
			oldGridPointLength = len( gridPoints )
			self.addRemainingGridPoints( arounds, gridPointInsetX, gridPointInsetY, gridPoints, True, paths, pixelTable, width )
		oldGridPointLength = len( gridPoints ) + 1
		while oldGridPointLength - len( gridPoints ) > 0:
			oldGridPointLength = len( gridPoints )
			self.addRemainingGridPoints( arounds, gridPointInsetX, gridPointInsetY, gridPoints, False, paths, pixelTable, width )

	def addGridLinePoints( self, alreadyFilledArounds, begin, end, gridPoints, gridRotationAngle, offset, rotatedExtruderLoops, surroundingSlices, y, z ):
		"Add the segments of one line of a grid to the infill."
		if self.gridRadius == 0.0:
			return
		gridWidth = self.gridWidthMultiplier * self.gridRadius
		gridXStep = int( math.floor( ( begin ) / gridWidth ) ) - 3
		gridXOffset = offset + gridWidth * float( gridXStep )
		while gridXOffset < begin:
			gridXStep = self.getNextGripXStep( gridXStep )
			gridXOffset = offset + gridWidth * float( gridXStep )
		while gridXOffset < end:
			gridPointComplex = complex( gridXOffset, y ) * gridRotationAngle
			gridPoint = Vec3( gridPointComplex.real, gridPointComplex.imag, z )
			if self.isPointInsideLineSegments( alreadyFilledArounds, gridPoint, rotatedExtruderLoops, surroundingSlices ):
				gridPoints.append( gridPoint )
			gridXStep = self.getNextGripXStep( gridXStep )
			gridXOffset = offset + gridWidth * float( gridXStep )

	def addLine( self, line ):
		"Add a line of text and a newline to the output."
		self.output.write( line + "\n" )

	def addRemainingGridPoints( self, arounds, gridPointInsetX, gridPointInsetY, gridPoints, isBothOrNone, paths, pixelTable, width ):
		for gridPointIndex in xrange( len( gridPoints ) - 1, - 1, - 1 ):
			gridPoint = gridPoints[ gridPointIndex ]
			addAroundGridPoint( arounds, gridPoint, gridPointInsetX, gridPointInsetY, gridPoints, self.gridRadius, isBothOrNone, self.isDoubleJunction, self.isJunctionWide, paths, pixelTable, width )

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

	def getAreaChange( self, area, layerIndex ):
		"Get the difference between the area of the slice at the layer index and the given area."
		layerArea = self.getSliceArea( layerIndex )
		return min( area, layerArea ) / max( area, layerArea )

	def getGridPoints( self, alreadyFilledArounds, fillLoops, reverseRotationAroundZAngle, rotatedExtruderLoops, surroundingSlices, z ):
		"Add a grid to the infill."
		if self.infillSolidity > 0.8:
			return []
		gridPoints = []
		rotationBaseAngle = euclidean.getPolar( self.infillBeginRotation, 1.0 )
		reverseRotationBaseAngle = complex( rotationBaseAngle.real, - rotationBaseAngle.imag )
		gridRotationAngle = reverseRotationAroundZAngle * rotationBaseAngle
		surroundingSlicesLength = len( surroundingSlices )
		if surroundingSlicesLength < self.doubleSolidSurfaceThickness:
			return []
		gridAlreadyFilledArounds = []
		gridRotatedExtruderLoops = []
		back = - 999999999.0
		front = - back
		gridInset = 1.2 * self.interiorExtrusionWidth
		muchGreaterThanLayerFillInset = 1.5 * gridInset
		slightlyGreaterThanFill = 1.01 * gridInset
		for loop in fillLoops:
			gridAlreadyFilledLoop = []
			gridAlreadyFilledArounds.append( gridAlreadyFilledLoop )
			planeRotatedPerimeter = euclidean.getPathRoundZAxisByPlaneAngle( reverseRotationBaseAngle, loop )
			gridRotatedExtruderLoops.append( planeRotatedPerimeter )
			circleNodes = intercircle.getCircleNodesFromLoop( planeRotatedPerimeter, slightlyGreaterThanFill )
			centers = intercircle.getCentersFromCircleNodes( circleNodes )
			for center in centers:
				alreadyFilledInset = intercircle.getSimplifiedInsetFromClockwiseLoop( center, gridInset )
				if euclidean.getMaximumSpan( alreadyFilledInset ) > muchGreaterThanLayerFillInset:
					gridAlreadyFilledLoop.append( alreadyFilledInset )
					if euclidean.isPathInsideLoop( planeRotatedPerimeter, alreadyFilledInset ) == euclidean.isWiddershins( planeRotatedPerimeter ):
						for point in alreadyFilledInset:
							back = max( back, point.y )
							front = min( front, point.y )
		front = ( 0.01 + math.ceil( front / self.gridRadius ) ) * self.gridRadius
		fillWidth = back - front
		numberOfLines = int( math.ceil( fillWidth / self.gridRadius ) )
		horizontalSegments = []
		for fillLine in xrange( numberOfLines ):
			y = front + float( fillLine ) * self.gridRadius
			lineSegments = getHorizontalSegmentsFromLoopLists( gridRotatedExtruderLoops, gridAlreadyFilledArounds, y )
			shortenedSegments = []
			for lineSegment in lineSegments:
				addShortenedLineSegment( lineSegment, self.interiorExtrusionWidth, shortenedSegments )
			horizontalSegments.append( shortenedSegments )
		for horizontalSegment in horizontalSegments:
			for lineSegment in horizontalSegment:
				endpointFirst = lineSegment[ 0 ]
				endpointSecond = lineSegment[ 1 ]
				begin = min( endpointFirst.point.x, endpointSecond.point.x )
				end = max( endpointFirst.point.x, endpointSecond.point.x )
				y = endpointFirst.point.y
				offset = self.offsetMultiplier * self.gridRadius * ( round( y / self.gridRadius ) % 2 )
				self.addGridLinePoints( alreadyFilledArounds, begin, end, gridPoints, gridRotationAngle, offset, rotatedExtruderLoops, surroundingSlices, y, z )
		return gridPoints

	def getLayerRoundZ( self, layerIndex ):
		"Get the plane angle around z that the layer is rotated by."
		rotation = self.rotatedLayers[ layerIndex ].rotation
		if rotation != None:
			return rotation
		infillBeginRotationRepeat = self.fillPreferences.infillBeginRotationRepeat.value
		infillOddLayerRotationMultiplier = float( layerIndex % ( infillBeginRotationRepeat + 1 ) == infillBeginRotationRepeat )
		return euclidean.getPolar( self.infillBeginRotation + infillOddLayerRotationMultiplier * self.infillOddLayerExtraRotation, 1.0 )

	def getNextGripXStep( self, gridXStep ):
		"Get the next grid x step, increment by an extra one every three if hexagonal grid is chosen."
		gridXStep += 1
		if self.fillPreferences.infillPatternGridHexagonal.value:
			if gridXStep % 3 == 0:
				gridXStep += 1
		return gridXStep

	def getRotatedLayer( self ):
		"Get the rotated layer, making a new one if necessary."
		if self.rotatedLayer == None:
			self.rotatedLayer = RotatedLayer()
			self.rotatedLayers.append( self.rotatedLayer )
		return self.rotatedLayer

	def getRounded( self, number ):
		"Get number rounded to the number of carried decimal places as a string."
		return euclidean.getRoundedToDecimalPlaces( self.decimalPlacesCarried, number )

	def getSliceArea( self, layerIndex ):
		"Get the area of the slice."
		if layerIndex < 0 or layerIndex >= len( self.rotatedLayers ):
			return 0.0
		boundaries = self.rotatedLayers[ layerIndex ].boundaries
		area = 0.0
		for boundary in boundaries:
			area += euclidean.getPolygonArea( boundary )
		return area

	def isPointInsideLineSegments( self, alreadyFilledArounds, gridPoint, rotatedExtruderLoops, surroundingSlices ):
		"Is the point inside the line segments of the loops."
		if self.solidSurfaceThickness <= 0:
			return True
		lineSegments = getHorizontalSegmentsFromLoopLists( rotatedExtruderLoops, alreadyFilledArounds, gridPoint.y )
		surroundingXIntersections = getSurroundingXIntersections( self.doubleSolidSurfaceThickness, surroundingSlices, gridPoint.y )
		for lineSegment in lineSegments:
			if isSegmentCompletelyInAnIntersection( lineSegment, surroundingXIntersections ):
				xFirst = lineSegment[ 0 ].point.x
				xSecond = lineSegment[ 1 ].point.x
				if gridPoint.x > min( xFirst, xSecond ) and gridPoint.x < max( xFirst, xSecond ):
					return True
		return False

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
		self.infillSolidity = fillPreferences.infillSolidity.value
		if not fillPreferences.infillPatternLine.value:
			self.setGridVariables( fillPreferences )
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
			elif firstWord == '(<extrusionPerimeterWidth>':
				self.extrusionPerimeterWidth = float( splitLine[ 1 ] )
			elif firstWord == '(<extrusionWidth>':
				self.extrusionWidth = float( splitLine[ 1 ] )
				self.interiorExtrusionWidth = self.extrusionWidth / self.fillPreferences.interiorInfillDensityOverExteriorDensity.value
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

	def setGridVariables( self, fillPreferences ):
		"Set the grid variables."
		self.gridRadius = self.interiorExtrusionWidth / self.infillSolidity
		self.gridWidthMultiplier = 2.0
		self.offsetMultiplier = 1.0
		if self.fillPreferences.infillPatternGridHexagonal.value:
			self.gridWidthMultiplier = 2.0 / math.sqrt( 3.0 )
			self.offsetMultiplier = 2.0 / math.sqrt( 3.0 ) * 1.5
		if self.fillPreferences.infillPatternGridRectangular.value:
			self.gridJunctionSeparation = 0.5 * ( self.gridRadius - self.interiorExtrusionWidth ) * fillPreferences.gridJunctionSeparationOverInnerOctogonRadius.value


class RotatedLayer:
	"A rotated layer."
	def __init__( self ):
		self.boundaries = []
		self.rotation = None
		self.surroundingLoops = []

	def __repr__( self ):
		"Get the string representation of this RotatedLayer."
		return '%s, %s, %s' % ( self.rotation, self.surroundingLoops, self.boundaries )


class YIntersectionPath:
	"A class to hold the y intersection position, the loop which it intersected and the point index of the loop which it intersected."
	def __init__( self, pathIndex, pointIndex, y ):
		"Initialize from the path, point index, and y."
		self.pathIndex = pathIndex
		self.pointIndex = pointIndex
		self.y = y

	def __repr__( self ):
		"Get the string representation of this y intersection."
		return '%s, %s, %s' % ( self.pathIndex, self.pointIndex, self.y )

	def getPath( self, paths ):
		"Get the path from the paths and path index."
		return paths[ self.pathIndex ]

	def getPointIndexPlusOne( self ):
		"Get the point index plus one."
		return self.pointIndex + 1


def main( hashtable = None ):
	"Display the fill dialog."
	if len( sys.argv ) > 1:
		writeOutput( ' '.join( sys.argv[ 1 : ] ) )
	else:
		preferences.displayDialog( FillPreferences() )

if __name__ == "__main__":
	main()

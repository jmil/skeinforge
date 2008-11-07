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
default is line.  The time required to generate the grid increases with the fourth power of the "Infill Solidity", so when choosing the grid
option, set the infill solidity to 0.2 or less so that skeinforge doesn't take a ludicrous amount of time to generate the infill.

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

#use raster collision avoidance
#raft supports overhangs
#use slice format, carve & inset
#slice aoi xml
#bridge extrusion width
#change material
#multiply
#distance option?
#document gear script
#email marcus about bridge extrusion width http://reprap.org/bin/view/Main/ExtruderImprovementsAndAlternatives
#mosaic
#transform
#pick and place
#stack
#infill first
#skeinskin to view isometric surface
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
	otherPaths = getOtherPaths( closestPathIndex, closestPointIndex, paths )
	if isIntersectingLoopsPaths( arounds, otherPaths, removedEndpointPoint, closestPath[ min( closestPointIndex, len( closestPath ) - 1 ) ] ):
		return
	if closestPointIndex == 0 or closestPointIndex == len( closestPath ):
		closestPath.insert( closestPointIndex, removedEndpointPoint )
		return
	if isSharpCornerAdded( closestPath, removedEndpointPoint, closestPointIndex ):
		return
	if not isIntersectingLoopsPaths( arounds, otherPaths, removedEndpointPoint, closestPath[ closestPointIndex - 1 ] ):
		closestPath.insert( closestPointIndex, removedEndpointPoint )

def addAroundGridPoint( arounds, gridPoint, gridPointInsetX, gridPointInsetY, gridSearchRadius, paths ):
	"Add the path around the grid point."
	closestPathIndex = None
	aroundIntersectionPaths = []
	for aroundIndex in range( len( arounds ) ):
		path = arounds[ aroundIndex ]
		for pointIndex in xrange( len( path ) ):
			pointFirst = path[ pointIndex ]
			pointSecond = path[ ( pointIndex + 1 ) % len( path ) ]
			yIntersection = getYIntersectionIfExists( pointFirst, pointSecond, gridPoint.x )
			addYIntersectionPathToList( aroundIndex, pointIndex, gridPoint.y, yIntersection, aroundIntersectionPaths )
	if len( aroundIntersectionPaths ) < 2:
		print( 'This should never happen, aroundIntersectionPaths is less than 2 in fill.' )
		print( aroundIntersectionPaths )
		print( gridPoint )
		print( arounds )
		return
	yCloseToCenterArounds = getClosestOppositeIntersectionPath( aroundIntersectionPaths )
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
	yCloseToCenterPaths = getClosestOppositeIntersectionPath( yIntersectionPaths )
	for yCloseToCenterPath in yCloseToCenterPaths:
		setIsOutside( yCloseToCenterPath, yIntersectionPaths )
	if len( yCloseToCenterPaths ) < 2:
		yCloseToCenterPaths[ 0 ].gridPoint = gridPoint
		isInsertGridPointPair( arounds, gridPointInsetX, paths, yCloseToCenterPaths[ 0 ] )
		return
	plusMinusSign = getPlusMinusSign( yCloseToCenterPaths[ 1 ].y - yCloseToCenterPaths[ 0 ].y )
	yCloseToCenterPaths[ 0 ].gridPoint = Vec3( gridPoint.x, gridPoint.y - plusMinusSign * gridPointInsetY, gridPoint.z )
	yCloseToCenterPaths[ 1 ].gridPoint = Vec3( gridPoint.x, gridPoint.y + plusMinusSign * gridPointInsetY, gridPoint.z )
	yCloseToCenterPaths.sort( comparePointIndexDescending )
	insertGridPointPairs( arounds, gridPoint, gridPointInsetX, yCloseToCenterPaths[ 0 ], yCloseToCenterPaths[ 1 ], paths )

def addHorizontalXIntersectionIndexes( fillLoops, alreadyFilledArounds, xIntersectionIndexList, y ):
	"Add horizontal x intersection indexes inside loops."
	euclidean.addXIntersectionIndexesFromLoops( fillLoops, - 1, xIntersectionIndexList, y )
	euclidean.addXIntersectionIndexesFromLoopLists( alreadyFilledArounds, xIntersectionIndexList, y )

def addPath( extrusionWidth, fill, path, rotationPlaneAngle ):
	"Add simplified path to fill."
	planeRotated = euclidean.getPathRoundZAxisByPlaneAngle( rotationPlaneAngle, euclidean.getSimplifiedPath( path, extrusionWidth ) )
	fill.append( planeRotated )

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

def createFillForSurroundings( surroundingLoops ):
	"Create extra fill loops for surrounding loops."
	for surroundingLoop in surroundingLoops:
		createExtraFillLoops( surroundingLoop )

def createExtraFillLoops( surroundingLoop ):
	"Create extra fill loops."
	for innerSurrounding in surroundingLoop.innerSurroundings:
		createFillForSurroundings( innerSurrounding.innerSurroundings )
	outsides = []
	insides = euclidean.getInsidesAddToOutsides( surroundingLoop.getFillLoops(), outsides )
	allFillLoops = []
	for outside in outsides:
		transferredLoops = euclidean.getTransferredPaths( insides, outside )
		allFillLoops += getExtraFillLoops( transferredLoops, outside, surroundingLoop.extrusionWidth )
	if len( allFillLoops ) > 0:
		surroundingLoop.lastFillLoops = allFillLoops
	surroundingLoop.extraLoops += allFillLoops

def getClosestOppositeIntersectionPath( yIntersectionPaths ):
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

def getHorizontalSegments( fillLoops, alreadyFilledArounds, y ):
	"Get horizontal segments inside loops."
	xIntersectionIndexList = []
	addHorizontalXIntersectionIndexes( fillLoops, alreadyFilledArounds, xIntersectionIndexList, y )
	return euclidean.getSegmentsFromXIntersectionIndexes( xIntersectionIndexList, y, fillLoops[ 0 ][ 0 ].z )

def getOtherPaths( pathIndex, pointIndex, paths ):
	"Get the other paths and the path after and before the point index."
	path = paths[ pathIndex ]
	pathJustAfter = path[ pointIndex + 1 : ]
	pathJustBefore = path[ : pointIndex - 1 ]
	return paths[ : pathIndex ] + paths[ pathIndex + 1 : ] + [ pathJustAfter, pathJustBefore ]

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
	return getSurroundingXIntersectionsFromXIntersectionIndexes( doubleSolidSurfaceThickness, xIntersectionIndexList, y )

def getSurroundingXIntersectionsFromXIntersectionIndexes( totalSolidSurfaceThickness, xIntersectionIndexList, y ):
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

def insertGridPointPairs( arounds, gridPoint, gridPointInsetX, intersectionPathFirst, intersectionPathSecond, paths ):
	"Insert a pair of points around a pair of grid points."
	originalPathFirst = intersectionPathFirst.getPath( paths )[ : ]
	isInsertGridPointFirst = isInsertGridPointPair( arounds, gridPointInsetX, paths, intersectionPathFirst )
	if not isInsertGridPointFirst:
		intersectionPathSecond.gridPoint = gridPoint
	isInsertGridPointSecond = isInsertGridPointPair( arounds, gridPointInsetX, paths, intersectionPathSecond )
	if isInsertGridPointFirst and not isInsertGridPointSecond:
		pathFirstMoved = intersectionPathFirst.getPath( paths )[ : ]
		paths[ intersectionPathFirst.pathIndex ] = originalPathFirst
		intersectionPathSecond.gridPoint = gridPoint
		isInsertGridPointFirstCenter = isInsertGridPointPair( arounds, gridPointInsetX, paths, intersectionPathFirst )
		if not isInsertGridPointFirstCenter:
			paths[ intersectionPathFirst.pathIndex ] = pathFirstMoved

def isInsertGridPointNotIntersecting( arounds, gridPoint, paths, yIntersectionPath ):
	"Insert a grid point if it is not intersecting the other paths."
	otherPaths = getOtherPaths( yIntersectionPath.pathIndex, yIntersectionPath.getPointIndexPlusOne(), paths )
	path = yIntersectionPath.getPath( paths )
	if isIntersectingLoopsPaths( arounds, otherPaths, gridPoint, path[ min( yIntersectionPath.getPointIndexPlusOne(), len( path ) - 1 ) ] ):
		return False
	if isIntersectingLoopsPaths( arounds, otherPaths, gridPoint, path[ yIntersectionPath.pointIndex ] ):
		return False
	if isSharpCornerAdded( path, gridPoint, yIntersectionPath.getPointIndexPlusOne() ):
		return False
	path.insert( yIntersectionPath.getPointIndexPlusOne(), gridPoint )
	return True

def isInsertGridPointPair( arounds, gridPointInsetX, paths, yIntersectionPath ):
	"Insert a pair of points around the grid point."
	intersectionBeginPoint = None
	moreThanInset = 2.1 * gridPointInsetX
	path = yIntersectionPath.getPath( paths )
	begin = path[ yIntersectionPath.pointIndex ]
	end = path[ yIntersectionPath.getPointIndexPlusOne() ]
	plusMinusSign = getPlusMinusSign( end.x - begin.x )
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
	gridPointXFirst = Vec3( yIntersectionPath.gridPoint.x - plusMinusSign * gridPointInsetX, yIntersectionPath.gridPoint.y, yIntersectionPath.gridPoint.z )
	gridPointXSecond = Vec3( yIntersectionPath.gridPoint.x + plusMinusSign * gridPointInsetX, yIntersectionPath.gridPoint.y, yIntersectionPath.gridPoint.z )
	isFirstPointInserted = None
	isSecondPointInserted = isInsertGridPointNotIntersecting( arounds, gridPointXSecond, paths, yIntersectionPath )
	if isSecondPointInserted:
		isFirstPointInserted = isInsertGridPointNotIntersecting( arounds, gridPointXFirst, paths, yIntersectionPath )
		if not isFirstPointInserted:
			isFirstPointInserted = isInsertGridPointNotIntersecting( arounds, yIntersectionPath.gridPoint, paths, yIntersectionPath )
	else:
		isFirstPointInserted = isInsertGridPointNotIntersecting( arounds, yIntersectionPath.gridPoint, paths, yIntersectionPath )
	isInserted = isSecondPointInserted or isFirstPointInserted
	if isInserted:
		if intersectionBeginPoint != None:
			path.insert( yIntersectionPath.getPointIndexPlusOne(), intersectionBeginPoint )
	return isInserted

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

def isSharpCornerAdded( path, point, pointIndexPlusOne ):
	"Determine if the added point would make a sharp corner."
	pointIndex = pointIndexPlusOne - 1
	if pointIndexPlusOne >= len( path ):
		return False
	if isSharpCorner( path[ pointIndex ], point, path[ pointIndexPlusOne ] ):
		return True
	pointIndexPlusTwo = pointIndexPlusOne + 1
	if pointIndexPlusTwo >= len( path ):
		return False
	if isSharpCorner( point, path[ pointIndexPlusOne ], path[ pointIndexPlusTwo ] ):
		return True
	pointIndexMinusOne = pointIndex - 1
	if pointIndexMinusOne < 0:
		return False
	return isSharpCorner( point, path[ pointIndex ], path[ pointIndexMinusOne ] )

def isSharpCorner( begin, center, end ):
	"Determine if the three points form a sharp corner."
	centerPointComplex = center.dropAxis( 2 )
	centerBeginComplex = begin.dropAxis( 2 ) - centerPointComplex
	centerEndComplex = end.dropAxis( 2 ) - centerPointComplex
	centerBeginLength = abs( centerBeginComplex )
	centerEndLength = abs( centerEndComplex )
	if centerBeginLength <= 0.0 or centerEndLength <= 0.0:
		return False
	centerBeginComplex /= centerBeginLength
	centerEndComplex /= centerEndLength
	return euclidean.getComplexDot( centerBeginComplex, centerEndComplex ) > 0.95

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
		self.gridSquareHalfWidthOverExtrusionWidth = preferences.FloatPreference().getFromValue( 'Grid Square Half Width over Extrusion Width (ratio):', 0.0 )
		self.archive.append( self.gridSquareHalfWidthOverExtrusionWidth )
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
		self.infillPatternGrid = preferences.Radio().getFromRadio( 'Grid', infillPatternRadio, False )
		self.archive.append( self.infillPatternGrid )
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
#		if layerIndex != 17:
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
		gridPointInsetX = 0.5 * layerFillInset
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
		if len( arounds ) < 1:
			euclidean.addToThreadsRemoveFromSurroundings( self.oldOrderedLocation, surroundingLoops, self )
			return
		area = self.getSliceArea( layerIndex )
		if area > 0.0:
			areaChange = 1.0
			for surroundingIndex in range( 1, self.solidSurfaceThickness + 1 ):
				areaChange = min( areaChange, self.getAreaChange( area, layerIndex - surroundingIndex ) )
				areaChange = min( areaChange, self.getAreaChange( area, layerIndex + surroundingIndex ) )
			if areaChange > 0.5:
				layerExtrusionWidth /= self.fillPreferences.interiorInfillDensityOverExteriorDensity.value
		front = math.ceil( front / layerExtrusionWidth ) * layerExtrusionWidth
		fillWidth = back - front
		numberOfLines = int( math.ceil( fillWidth / layerExtrusionWidth ) )
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
			addSparseEndpoints( doubleExtrusionWidth, endpoints, fillLine, horizontalSegments, self.infillSolidity, removedEndpoints, self.solidSurfaceThickness, surroundingXIntersections )
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
		if self.fillPreferences.infillPatternGrid.value:
			self.addGrid( alreadyFilledArounds, arounds, fillLoops, gridPointInsetX, paths, reverseRotationAroundZAngle, rotatedExtruderLoops, surroundingSlices, z )
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

	def addGrid( self, alreadyFilledArounds, arounds, fillLoops, gridPointInsetX, paths, reverseRotationAroundZAngle, rotatedExtruderLoops, surroundingSlices, z ):
		"Add a grid to the infill."
		if self.infillSolidity > 0.8:
			return
		rotationBaseAngle = euclidean.getPolar( self.infillBeginRotation, 1.0 )
		reverseRotationBaseAngle = complex( rotationBaseAngle.real, - rotationBaseAngle.imag )
		gridRotationAngle = reverseRotationAroundZAngle * rotationBaseAngle
		surroundingSlicesLength = len( surroundingSlices )
		if surroundingSlicesLength < self.doubleSolidSurfaceThickness:
			return
		gridAlreadyFilledArounds = []
		gridRotatedExtruderLoops = []
		back = - 999999999.0
		front = - back
		gridInset = 1.2 * self.extrusionWidth
#		gridInset = .1 * self.extrusionWidth
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
		front = math.ceil( front / self.gridRadius ) * self.gridRadius
		fillWidth = back - front
		numberOfLines = int( math.ceil( fillWidth / self.gridRadius ) )
		horizontalSegments = []
		for fillLine in xrange( numberOfLines ):
			y = front + float( fillLine ) * self.gridRadius
			lineSegments = getHorizontalSegments( gridRotatedExtruderLoops, gridAlreadyFilledArounds, y )
			shortenedSegments = []
			for lineSegment in lineSegments:
				addShortenedLineSegment( lineSegment, self.extrusionWidth, shortenedSegments )
			horizontalSegments.append( shortenedSegments )
		for horizontalSegment in horizontalSegments:
			for lineSegment in horizontalSegment:
				endpointFirst = lineSegment[ 0 ]
				endpointSecond = lineSegment[ 1 ]
				begin = min( endpointFirst.point.x, endpointSecond.point.x )
				end = max( endpointFirst.point.x, endpointSecond.point.x )
				y = endpointFirst.point.y
				offset = self.gridRadius * ( round( y / self.gridRadius ) % 2 )
				self.addGridLineSegments( alreadyFilledArounds, arounds, begin, end, gridPointInsetX, gridRotationAngle, offset, paths, rotatedExtruderLoops, surroundingSlices, y, z )

	def addGridLineSegments( self, alreadyFilledArounds, arounds, begin, end, gridPointInsetX, gridRotationAngle, offset, paths, rotatedExtruderLoops, surroundingSlices, y, z ):
		"Add the segments of one line of a grid to the infill."
		if self.gridRadius == 0.0:
			return
		gridWidth = 2.0 * self.gridRadius
		gridX = offset - gridWidth * math.floor( ( offset - begin ) / gridWidth )
		gridPointInsetY = gridPointInsetX * ( 1.0 - self.fillPreferences.gridExtraOverlap.value )
		gridPointInsetX += self.gridSquareSize
		gridPointInsetY += self.gridSquareSize
		while gridX < end:
			gridPointComplex = complex( gridX, y ) * gridRotationAngle
			gridPoint = Vec3( gridPointComplex.real, gridPointComplex.imag, z )
			if self.isPointInsideLineSegments( alreadyFilledArounds, gridPoint, rotatedExtruderLoops, surroundingSlices ):
				addAroundGridPoint( arounds, gridPoint, gridPointInsetX, gridPointInsetY, 1.5 * self.gridRadius, paths )
			gridX += gridWidth

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

	def getAreaChange( self, area, layerIndex ):
		"Get the difference between the area of the slice at the layer index and the given area."
		layerArea = self.getSliceArea( layerIndex )
		return min( area, layerArea ) / max( area, layerArea )

	def getLayerRoundZ( self, layerIndex ):
		"Get the plane angle around z that the layer is rotated by."
		rotation = self.rotatedLayers[ layerIndex ].rotation
		if rotation != None:
			return rotation
		infillBeginRotationRepeat = self.fillPreferences.infillBeginRotationRepeat.value
		infillOddLayerRotationMultiplier = float( layerIndex % ( infillBeginRotationRepeat + 1 ) == infillBeginRotationRepeat )
		return euclidean.getPolar( self.infillBeginRotation + infillOddLayerRotationMultiplier * self.infillOddLayerExtraRotation, 1.0 )

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
		lineSegments = getHorizontalSegments( rotatedExtruderLoops, alreadyFilledArounds, gridPoint.y )
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
		if fillPreferences.infillPatternGrid.value:
			self.gridRadius = self.extrusionWidth / self.infillSolidity
			self.gridSquareSize = self.extrusionWidth * self.fillPreferences.gridSquareHalfWidthOverExtrusionWidth.value
			if self.infillSolidity > 0.25:
				print( "The time it takes to generate the grid increases with the fourth power of the infill solidity." )
				print( "Try an infill solidity of 0.2 or less when generating a grid, instead of your current preference of: %s" % self.infillSolidity )
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

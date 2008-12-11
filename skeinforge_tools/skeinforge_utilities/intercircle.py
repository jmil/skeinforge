"""
Intercircle is a collection of utilities for intersecting circles, used to get smooth loops around a collection of points and inset & outset loops.

"""

from __future__ import absolute_import
try:
	import psyco
	psyco.full()
except:
	pass
#Init has to be imported first because it has code to workaround the python bug where relative imports don't work if the module is imported as a main module.
import __init__

from skeinforge_tools.skeinforge_utilities.vec3 import Vec3
from skeinforge_tools.skeinforge_utilities import euclidean
import math


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


def addCircleIntersectionLoop( circleIntersectionPath, circleIntersections ):
	"Add a circle intersection loop."
	firstCircleIntersection = circleIntersectionPath[ 0 ]
	circleIntersectionAhead = firstCircleIntersection
	for circleIntersectionIndex in xrange( len( circleIntersections ) + 1 ):
		circleIntersectionAhead = circleIntersectionAhead.getCircleIntersectionAhead()
		if circleIntersectionAhead.index == firstCircleIntersection.index:
			firstCircleIntersection.steppedOn = True
			return
		if circleIntersectionAhead.steppedOn == True:
			print( 'circleIntersectionAhead.steppedOn == True in intercircle.' )
			print( circleIntersectionAhead )
		circleIntersectionAhead.addToList( circleIntersectionPath )
	firstCircleIntersection.steppedOn = True
	print( "addCircleIntersectionLoop would have gone into an endless loop, this should never happen." )
	print( "circleIntersectionPath" )
	for circleIntersection in circleIntersectionPath:
		print( circleIntersection )
		print( circleIntersection.circleNodeAhead )
		print( circleIntersection.circleNodeBehind )
	print( "firstCircleIntersection" )
	print( firstCircleIntersection )
	print( "circleIntersections" )
	for circleIntersection in circleIntersections:
		print( circleIntersection )

def addCircleIntersectionLoopComplex( circleIntersectionPathComplexes, circleIntersectionComplexes ):
	"Add a circle intersection loop."
	firstCircleIntersection = circleIntersectionPathComplexes[ 0 ]
	circleIntersectionAhead = firstCircleIntersection
	for circleIntersectionIndex in xrange( len( circleIntersectionComplexes ) + 1 ):
		circleIntersectionAhead = circleIntersectionAhead.getCircleIntersectionAhead()
		if circleIntersectionAhead.index == firstCircleIntersection.index:
			firstCircleIntersection.steppedOn = True
			return
		if circleIntersectionAhead.steppedOn == True:
			print( 'circleIntersectionAhead.steppedOn == True in intercircle.' )
			print( circleIntersectionAhead )
		circleIntersectionAhead.addToList( circleIntersectionPathComplexes )
	firstCircleIntersection.steppedOn = True
	print( "addCircleIntersectionLoop would have gone into an endless loop, this should never happen." )
	print( "circleIntersectionPathComplexes" )
	for circleIntersectionComplex in circleIntersectionPathComplexes:
		print( circleIntersectionComplex )
		print( circleIntersectionComplex.circleNodeComplexAhead )
		print( circleIntersectionComplex.circleNodeComplexBehind )
	print( "firstCircleIntersection" )
	print( firstCircleIntersection )
	print( "circleIntersectionComplexes" )
	for circleIntersectionComplex in circleIntersectionComplexes:
		print( circleIntersectionComplex )

def addOperatingOrbits( boundaryLoops, operatingJump, skein, temperatureChangeTime ):
	"Add the orbits before the operating layers."
	if len( boundaryLoops ) < 1:
		return
	largestLength = - 999999999.0
	largestLoop = None
	perimeterOutset = 0.4 * skein.extrusionPerimeterWidth
	greaterThanPerimeterOutset = 1.1 * perimeterOutset
	for boundaryLoop in boundaryLoops:
		centers = getCentersFromLoopDirection( True, boundaryLoop, greaterThanPerimeterOutset )
		for center in centers:
			outset = getSimplifiedInsetFromClockwiseLoop( center, perimeterOutset )
			if euclidean.isLargeSameDirection( outset, center, perimeterOutset ):
				loopLength = euclidean.getPolygonLength( outset )
				if loopLength > largestLength:
					largestLength = loopLength
					largestLoop = outset
	if largestLoop == None:
		return
	setZAccordingToOperatingJump( largestLoop, operatingJump )
	addOrbits( largestLoop, skein, temperatureChangeTime )

def addOrbits( loop, skein, temperatureChangeTime ):
	"Add orbits with the extruder off."
	if len( loop ) < 1:
		print( 'Zero length loop which was skipped over, this should never happen.' )
	if temperatureChangeTime < 1.5:
		return
	timeInOrbit = 0.0
	while timeInOrbit < temperatureChangeTime:
		for point in loop:
			skein.addGcodeFromFeedrateMovement( 60.0 * skein.orbitalFeedratePerSecond, point )
		timeInOrbit += euclidean.getPolygonLength( loop ) / skein.orbitalFeedratePerSecond

def addPointComplexesFromSegment( pointComplexes, radius, pointBeginComplex, pointEndComplex ):
	"Add point complexes between the endpoints of a segment."
	if radius <= 0.0:
		print( 'This should never happen, radius should never be zero or less in addPointsFromSegment in intercircle.' )
	thresholdRadius = radius * 0.9 # a higher number would be faster but would leave bigger dangling loops.
	thresholdDiameter = thresholdRadius * 2.0
	segmentComplex = pointEndComplex - pointBeginComplex
	segmentComplexLength = abs( segmentComplex )
	extraCircles = int( math.floor( segmentComplexLength / thresholdDiameter ) )
	lengthIncrement = segmentComplexLength / ( float( extraCircles ) + 1.0 )
	if segmentComplexLength == 0.0:
		print( 'This should never happen, segmentComplexLength = 0.0 in intercircle.' )
		print( 'pointBeginComplex' )
		print( pointBeginComplex )
		print( pointEndComplex )
		return
	segmentComplex *= lengthIncrement / segmentComplexLength
	nextCircleCenterComplex = pointBeginComplex + segmentComplex
	for circleIndex in range( extraCircles ):
		pointComplexes.append( nextCircleCenterComplex )
		nextCircleCenterComplex += segmentComplex

def addPointsFromSegment( points, radius, pointBegin, pointEnd ):
	"Add points between the endpoints of a segment."
	if radius <= 0.0:
		print( 'This should never happen, radius should never be zero or less in addPointsFromSegment in intercircle.' )
	thresholdRadius = radius * 0.9 # a higher number would be faster but would leave bigger dangling loops.
	thresholdDiameter = thresholdRadius * 2.0
	segment = pointEnd.minus( pointBegin )
	segmentLength = segment.lengthXYPlane()
	extraCircles = int( math.floor( segmentLength / thresholdDiameter ) )
	lengthIncrement = segmentLength / ( float( extraCircles ) + 1.0 )
	if segmentLength == 0.0:
		print( 'This should never happen, segmentLength = 0.0 in intercircle.' )
		print( 'pointBegin' )
		print( pointBegin )
		print( pointEnd )
		return
	segment.scale( lengthIncrement / segmentLength )
	nextCircleCenter = pointBegin.plus( segment )
	for circleIndex in range( extraCircles ):
		points.append( nextCircleCenter )
		nextCircleCenter = nextCircleCenter.plus( segment )

def getCenterComplexesFromCircleNodeComplexes( circleNodeComplexes ):
	"Get the complex centers of the circle intersection loops from circle nodes."
	circleIntersectionComplexes = getCircleIntersectionComplexesFromCircleNodeComplexes( circleNodeComplexes )
	circleIntersectionLoopComplexes = getCircleIntersectionLoopComplexes( circleIntersectionComplexes )
	return getCenterComplexesFromIntersectionLoopComplexes( circleIntersectionLoopComplexes )

def getCenterComplexesFromIntersectionLoopComplex( circleIntersectionLoopComplex ):
	"Get the centers from the intersection loop."
	loop = []
	for circleIntersectionComplex in circleIntersectionLoopComplex:
		loop.append( circleIntersectionComplex.circleNodeComplexAhead.circleComplex )
	return loop

def getCenterComplexesFromIntersectionLoopComplexes( circleIntersectionLoopComplexes ):
	"Get the centers from the intersection loops."
	centers = []
	for circleIntersectionLoopComplex in circleIntersectionLoopComplexes:
		centers.append( getCenterComplexesFromIntersectionLoopComplex( circleIntersectionLoopComplex ) )
	return centers

def getCentersFromCircleNodes( circleNodes ):
	"Get the centers of the circle intersection loops from circle nodes."
	circleIntersections = getCircleIntersectionsFromCircleNodes( circleNodes )
	circleIntersectionLoops = getCircleIntersectionLoops( circleIntersections )
	return getCentersFromIntersectionLoops( circleIntersectionLoops )

def getCentersFromIntersectionLoop( circleIntersectionLoop ):
	"Get the centers from the intersection loop."
	loop = []
	for circleIntersection in circleIntersectionLoop:
		loop.append( circleIntersection.circleNodeAhead.circle )
	return loop

def getCentersFromIntersectionLoops( circleIntersectionLoops ):
	"Get the centers from the intersection loops."
	centers = []
	for circleIntersectionLoop in circleIntersectionLoops:
		centers.append( getCentersFromIntersectionLoop( circleIntersectionLoop ) )
	return centers

def getCentersFromLoopComplexDirection( isWiddershins, loop, radius ):
	"Get the centers of the circle intersection loops which go around in the given direction."
	circleNodes = getCircleNodeComplexesFromLoopComplex( loop, radius )
	centers = getCenterComplexesFromCircleNodeComplexes( circleNodes )
	return getLoopComplexesFromLoopComplexesDirection( isWiddershins, centers )

def getCentersFromLoopDirection( isWiddershins, loop, radius ):
	"Get the centers of the circle intersection loops which go around in the given direction."
	circleNodes = getCircleNodesFromLoop( loop, radius )
	centers = getCentersFromCircleNodes( circleNodes )
	return getLoopsFromLoopsDirection( isWiddershins, centers )

def getCentersFromOutside( isOutside, loop, radius ):
	"Get the centers of the circle intersection loops which are outside if isOutside is true, otherwise get the ones inside."
	circleNodes = getCircleNodesFromLoop( loop, radius )
	centers = getCentersFromCircleNodes( circleNodes )
	outsideCenters = []
	halfRadius = 0.5 * radius
	for center in centers:
		inset = getSimplifiedInsetFromClockwiseLoop( center, halfRadius )
		if euclidean.isPathInsideLoop( loop, inset ) != isOutside:
			outsideCenters.append( center )
	return outsideCenters

def getCircleIntersectionComplexesFromCircleNodeComplexes( circleNodeComplexes ):
	"Get all the circle intersections which exist between all the circle nodes."
	if len( circleNodeComplexes ) < 1:
		return
	circleIntersections = []
	index = 0
	pixelTable = {}
	slightlyGreaterThanRadius = 1.01 * circleNodeComplexes[ 0 ].radius
	for circleNodeComplex in circleNodeComplexes:
		circleOverWidth = circleNodeComplex.circleComplex / slightlyGreaterThanRadius
		x = int( round( circleOverWidth.real ) )
		y = int( round( circleOverWidth.imag ) )
		euclidean.addElementToPixelList( circleNodeComplex, pixelTable, x, y )
	slightlyGreaterThanDiameter = slightlyGreaterThanRadius + slightlyGreaterThanRadius
	accumulatedCircleNodeTable = {}
	for circleNodeComplexIndex in xrange( len( circleNodeComplexes ) ):
		circleNodeComplexBehind = circleNodeComplexes[ circleNodeComplexIndex ]
		circleNodeComplexIndexMinusOne = circleNodeComplexIndex - 1
		if circleNodeComplexIndexMinusOne >= 0:
			circleNodeComplexAdditional = circleNodeComplexes[ circleNodeComplexIndexMinusOne ]
			circleOverSlightlyGreaterThanDiameter = circleNodeComplexAdditional.circleComplex / slightlyGreaterThanDiameter
			x = int( round( circleOverSlightlyGreaterThanDiameter.real ) )
			y = int( round( circleOverSlightlyGreaterThanDiameter.imag ) )
			euclidean.addElementToPixelList( circleNodeComplexAdditional, accumulatedCircleNodeTable, x, y )
		withinNodes = circleNodeComplexBehind.getWithinNodes( accumulatedCircleNodeTable, slightlyGreaterThanDiameter )
		for circleNodeComplexAhead in withinNodes:
			circleIntersectionForward = CircleIntersectionComplex( circleNodeComplexAhead, index, circleNodeComplexBehind )
			if not circleIntersectionForward.isWithinCircles( pixelTable, slightlyGreaterThanRadius ):
				circleIntersections.append( circleIntersectionForward )
				circleNodeComplexBehind.circleIntersectionComplexes.append( circleIntersectionForward )
				index += 1
			circleIntersectionBackward = CircleIntersectionComplex( circleNodeComplexBehind, index, circleNodeComplexAhead )
			if not circleIntersectionBackward.isWithinCircles( pixelTable, slightlyGreaterThanRadius ):
				circleIntersections.append( circleIntersectionBackward )
				circleNodeComplexAhead.circleIntersectionComplexes.append( circleIntersectionBackward )
				index += 1
	return circleIntersections

def getCircleIntersectionsFromCircleNodes( circleNodes ):
	"Get all the circle intersections which exist between all the circle nodes."
	if len( circleNodes ) < 1:
		return
	circleIntersections = []
	index = 0
	pixelTable = {}
	slightlyGreaterThanRadius = 1.01 * circleNodes[ 0 ].radius
	for circleNode in circleNodes:
		circleOverWidth = circleNode.circleComplex / slightlyGreaterThanRadius
		x = int( round( circleOverWidth.real ) )
		y = int( round( circleOverWidth.imag ) )
		euclidean.addElementToPixelList( circleNode, pixelTable, x, y )
	slightlyGreaterThanDiameter = slightlyGreaterThanRadius + slightlyGreaterThanRadius
	accumulatedCircleNodeTable = {}
	for circleNodeIndex in xrange( len( circleNodes ) ):
		circleNodeBehind = circleNodes[ circleNodeIndex ]
		circleNodeIndexMinusOne = circleNodeIndex - 1
		if circleNodeIndexMinusOne >= 0:
			circleNodeAdditional = circleNodes[ circleNodeIndexMinusOne ]
			circleOverSlightlyGreaterThanDiameter = circleNodeAdditional.circleComplex / slightlyGreaterThanDiameter
			x = int( round( circleOverSlightlyGreaterThanDiameter.real ) )
			y = int( round( circleOverSlightlyGreaterThanDiameter.imag ) )
			euclidean.addElementToPixelList( circleNodeAdditional, accumulatedCircleNodeTable, x, y )
		withinNodes = circleNodeBehind.getWithinNodes( accumulatedCircleNodeTable, slightlyGreaterThanDiameter )
		for circleNodeAhead in withinNodes:
			circleIntersectionForward = CircleIntersection().getFromCircleNodes( circleNodeAhead, index, circleNodeBehind )
			if not circleIntersectionForward.isWithinCircles( pixelTable, slightlyGreaterThanRadius ):
				circleIntersections.append( circleIntersectionForward )
				circleNodeBehind.circleIntersections.append( circleIntersectionForward )
				index += 1
			circleIntersectionBackward = CircleIntersection().getFromCircleNodes( circleNodeBehind, index, circleNodeAhead )
			if not circleIntersectionBackward.isWithinCircles( pixelTable, slightlyGreaterThanRadius ):
				circleIntersections.append( circleIntersectionBackward )
				circleNodeAhead.circleIntersections.append( circleIntersectionBackward )
				index += 1
	return circleIntersections

def getCircleIntersectionLoopComplexes( circleIntersectionComplexes ):
	"Get all the loops going through the circle intersections."
	circleIntersectionLoopComplexes = []
	for circleIntersectionComplex in circleIntersectionComplexes:
		if not circleIntersectionComplex.steppedOn:
			circleIntersectionLoopComplex = [ circleIntersectionComplex ]
			circleIntersectionLoopComplexes.append( circleIntersectionLoopComplex )
			addCircleIntersectionLoopComplex( circleIntersectionLoopComplex, circleIntersectionComplexes )
	return circleIntersectionLoopComplexes

def getCircleIntersectionLoops( circleIntersections ):
	"Get all the loops going through the circle intersections."
	circleIntersectionLoops = []
	for circleIntersection in circleIntersections:
		if not circleIntersection.steppedOn:
			circleIntersectionLoop = [ circleIntersection ]
			circleIntersectionLoops.append( circleIntersectionLoop )
			addCircleIntersectionLoop( circleIntersectionLoop, circleIntersections )
	return circleIntersectionLoops

def getCircleNodeComplexesFromLoopComplex( loop, radius ):
	"Get the circle nodes from every point on a loop and between points."
	pointComplexes = []
	for pointComplexIndex in range( len( loop ) ):
		pointComplex = loop[ pointComplexIndex ]
		pointComplexSecond = loop[ ( pointComplexIndex + 1 ) % len( loop ) ]
		pointComplexes.append( pointComplex )
		addPointComplexesFromSegment( pointComplexes, radius, pointComplex, pointComplexSecond )
	return getCircleNodeComplexesFromPointComplexes( pointComplexes, radius )

def getCircleNodesFromLoop( loop, radius ):
	"Get the circle nodes from every point on a loop and between points."
	points = []
	for pointIndex in range( len( loop ) ):
		point = loop[ pointIndex ]
		pointSecond = loop[ ( pointIndex + 1 ) % len( loop ) ]
		points.append( point )
		addPointsFromSegment( points, radius, point, pointSecond )
	return getCircleNodesFromPath( points, radius )

def getCircleNodeComplexesFromPointComplexes( pointComplexes, radius ):
	"Get the circle nodes from a path."
	circleNodeComplexes = []
	pointComplexes = euclidean.getAwayPointComplexes( pointComplexes, 0.001 * radius )
	for pointComplex in pointComplexes:
		circleNodeComplexes.append( CircleNodeComplex( pointComplex, len( circleNodeComplexes ), radius ) )
	return circleNodeComplexes

def getCircleNodesFromPath( path, radius ):
	"Get the circle nodes from a path."
	circleNodes = []
	path = euclidean.getAwayPath( path, 0.001 * radius )
	for point in path:
		circleNodes.append( CircleNode().getFromCircleRadius( point, len( circleNodes ), radius ) )
	return circleNodes

def getInsetComplexFromClockwiseTriple( aheadAbsoluteComplex, behindAbsoluteComplex, centerComplex, radius ):
	"Get loop inset from clockwise triple, out from widdershins loop."
	originalCenterMinusBehindComplex = euclidean.getNormalized( centerComplex - behindAbsoluteComplex )
	reverseRoundZAngle = complex( originalCenterMinusBehindComplex.real, - originalCenterMinusBehindComplex.imag )
	aheadAbsoluteComplex *= reverseRoundZAngle
	behindAbsoluteComplex *= reverseRoundZAngle
	centerComplex *= reverseRoundZAngle
	aheadIntersectionComplex = getIntersectionComplexAtInset( aheadAbsoluteComplex, centerComplex, radius )
	behindIntersectionComplex = getIntersectionComplexAtInset( centerComplex, behindAbsoluteComplex, radius )
	centerComplexMinusAhead = centerComplex - aheadAbsoluteComplex
	if abs( centerComplexMinusAhead.imag ) < abs( 0.000001 * centerComplexMinusAhead.real ):
		between = 0.5 * ( aheadIntersectionComplex + behindIntersectionComplex )
		return originalCenterMinusBehindComplex * between
	yMinusAhead = behindIntersectionComplex.imag - aheadIntersectionComplex.imag
	x = aheadIntersectionComplex.real + yMinusAhead * centerComplexMinusAhead.real / centerComplexMinusAhead.imag
	return originalCenterMinusBehindComplex * complex( x, behindIntersectionComplex.imag )

def getInsetFromClockwiseTriple( aheadAbsolute, behindAbsolute, center, radius ):
	"Get loop inset from clockwise triple, out from widdershins loop."
	originalCenterMinusBehind = center.minus( behindAbsolute )
	originalCenterMinusBehind.normalize()
	centerRoundZAngle = originalCenterMinusBehind.dropAxis( 2 )
	reverseRoundZAngle = complex( centerRoundZAngle.real, - centerRoundZAngle.imag )
	aheadAbsolute = euclidean.getRoundZAxisByPlaneAngle( reverseRoundZAngle, aheadAbsolute )
	behindAbsolute = euclidean.getRoundZAxisByPlaneAngle( reverseRoundZAngle, behindAbsolute )
	center = euclidean.getRoundZAxisByPlaneAngle( reverseRoundZAngle, center )
	aheadIntersection = getIntersectionAtInset( aheadAbsolute, center, radius )
	behindIntersection = getIntersectionAtInset( center, behindAbsolute, radius )
	centerMinusAhead = center.minus( aheadAbsolute )
	if abs( centerMinusAhead.y ) < abs( 0.000001 * centerMinusAhead.x ):
		between = aheadIntersection.plus( behindIntersection )
		between.scale( 0.5 )
		return euclidean.getRoundZAxisByPlaneAngle( centerRoundZAngle, between )
	yMinusAhead = behindIntersection.y - aheadIntersection.y
	x = aheadIntersection.x + yMinusAhead * centerMinusAhead.x / centerMinusAhead.y
	between = Vec3( x, behindIntersection.y, behindIntersection.z )
	return euclidean.getRoundZAxisByPlaneAngle( centerRoundZAngle, between )

def getInsetFromClockwiseLoop( loop, radius ):
	"Get loop inset from clockwise loop, out from widdershins loop."
	insetLoop = []
	for pointIndex in range( len( loop ) ):
		behindAbsolute = loop[ ( pointIndex + len( loop ) - 1 ) % len( loop ) ]
		center = loop[ pointIndex ]
		aheadAbsolute = loop[ ( pointIndex + 1 ) % len( loop ) ]
		insetLoop.append( getInsetFromClockwiseTriple( aheadAbsolute, behindAbsolute, center, radius ) )
	return insetLoop

def getInsetFromClockwiseLoopComplex( loopComplex, radius ):
	"Get loop inset from clockwise loop, out from widdershins loop."
	insetLoopComplex = []
	for pointComplexIndex in range( len( loopComplex ) ):
		behindAbsoluteComplex = loopComplex[ ( pointComplexIndex + len( loopComplex ) - 1 ) % len( loopComplex ) ]
		centerComplex = loopComplex[ pointComplexIndex ]
		aheadAbsoluteComplex = loopComplex[ ( pointComplexIndex + 1 ) % len( loopComplex ) ]
		insetLoopComplex.append( getInsetComplexFromClockwiseTriple( aheadAbsoluteComplex, behindAbsoluteComplex, centerComplex, radius ) )
	return insetLoopComplex

def getInsetLoops( inset, loops ):
	"Get the inset loops."
	absoluteInset = abs( inset )
	insetLoops = []
	slightlyGreaterThanInset = 1.1 * absoluteInset
	muchGreaterThanLayerInset = 2.5 * absoluteInset
	for loop in loops:
		isInInsetDirection = euclidean.isWiddershins( loop )
		if inset < 0.0:
			isInInsetDirection = not isInInsetDirection
		centers = getCentersFromLoopDirection( not isInInsetDirection, loop, slightlyGreaterThanInset )
		for center in centers:
			insetLoop = getSimplifiedInsetFromClockwiseLoop( center, absoluteInset )
			if euclidean.isLargeSameDirection( insetLoop, center, muchGreaterThanLayerInset ):
				if euclidean.isPathInsideLoop( loop, insetLoop ) == isInInsetDirection:
					insetLoops.append( insetLoop )
	return insetLoops

def getIntersectionAtInset( ahead, behind, inset ):
	"Get circle intersection loop at inset from segment."
	aheadMinusBehind = ahead.minus( behind )
	aheadMinusBehind.scale( 0.5 )
	rotatedClockwiseQuarter = euclidean.getRotatedClockwiseQuarterAroundZAxis( aheadMinusBehind )
	rotatedClockwiseQuarter.scale( inset / rotatedClockwiseQuarter.lengthXYPlane() )
	aheadMinusBehind.add( rotatedClockwiseQuarter )
	aheadMinusBehind.add( behind )
	return aheadMinusBehind

def getIntersectionComplexAtInset( aheadComplex, behindComplex, inset ):
	"Get circle intersection loop at inset from segment."
	aheadComplexMinusBehindComplex = 0.5 * ( aheadComplex - behindComplex )
	rotatedClockwiseQuarter = complex( aheadComplexMinusBehindComplex.imag, - aheadComplexMinusBehindComplex.real )
	rotatedClockwiseQuarter *= inset / abs( rotatedClockwiseQuarter )
	return aheadComplexMinusBehindComplex + behindComplex + rotatedClockwiseQuarter

def getLoopComplexesFromLoopComplexesDirection( isWiddershins, loopComplexes ):
	"Get the loops going round in a given direction."
	directionalLoopComplexes = []
	for loopComplex in loopComplexes:
		if euclidean.isPolygonComplexWiddershins( loopComplex ) == isWiddershins:
			directionalLoopComplexes.append( loopComplex )
	return directionalLoopComplexes

def getLoopsFromLoopsDirection( isWiddershins, loops ):
	"Get the loops going round in a given direction."
	directionalLoops = []
	for loop in loops:
		if euclidean.isWiddershins( loop ) == isWiddershins:
			directionalLoops.append( loop )
	return directionalLoops

def getSimplifiedInsetFromClockwiseLoop( loop, radius ):
	"Get loop inset from clockwise loop, out from widdershins loop."
	return getWithoutIntersections( euclidean.getSimplifiedLoopAtFirstZ( getInsetFromClockwiseLoop( loop, radius ), radius ) )

def getSimplifiedInsetFromClockwiseLoopComplex( loopComplex, radius ):
	"Get loop inset from clockwise loop, out from widdershins loop."
	return getWithoutIntersectionComplexes( euclidean.getSimplifiedLoopComplex( getInsetFromClockwiseLoopComplex( loopComplex, radius ), radius ) )

def getWithoutIntersectionComplexes( loopComplex ):
	"Get loop without intersections."
	lastLoopLength = len( loopComplex )
	while lastLoopLength > 3:
		removeIntersectionComplex( loopComplex )
		if len( loopComplex ) == lastLoopLength:
			return loopComplex
		lastLoopLength = len( loopComplex )
	return loopComplex

def getWithoutIntersections( loop ):
	"Get loop without intersections."
	lastLoopLength = len( loop )
	while lastLoopLength > 3:
		removeIntersection( loop )
		if len( loop ) == lastLoopLength:
			return loop
		lastLoopLength = len( loop )
	return loop

def isLoopIntersectingLoop( anotherLoop, loop ):
	"Determine if the a loop is intersecting another loop."
	for pointIndex in range( len( loop ) ):
		pointFirst = loop[ pointIndex ]
		pointSecond = loop[ ( pointIndex + 1 ) % len( loop ) ]
		segment = pointFirst.minus( pointSecond )
		normalizedSegment = segment.dropAxis( 2 )
		normalizedSegment /= abs( normalizedSegment )
		segmentYMirror = complex( normalizedSegment.real, - normalizedSegment.imag )
		segmentFirstPoint = euclidean.getRoundZAxisByPlaneAngle( segmentYMirror, pointFirst )
		segmentSecondPoint = euclidean.getRoundZAxisByPlaneAngle( segmentYMirror, pointSecond )
		if euclidean.isLoopIntersectingInsideXSegment( anotherLoop, segmentFirstPoint.x, segmentSecondPoint.x, segmentYMirror, segmentFirstPoint.y ):
			return True
	return False

def removeIntersection( loop ):
	"Get loop without the first intersection."
	withoutIntersection = []
	for pointIndex in range( len( loop ) ):
		behind = loop[ ( pointIndex + len( loop ) - 1 ) % len( loop ) ]
		behindComplex = behind.dropAxis( 2 )
		behindEndComplex = loop[ ( pointIndex + len( loop ) - 2 ) % len( loop ) ].dropAxis( 2 )
		behindMidpointComplex = 0.5 * ( behindComplex + behindEndComplex )
		aheadComplex = loop[ pointIndex ].dropAxis( 2 )
		aheadEndComplex = loop[ ( pointIndex + 1 ) % len( loop ) ].dropAxis( 2 )
		aheadMidpointComplex = 0.5 * ( aheadComplex + aheadEndComplex )
		normalizedSegment = behindComplex - behindMidpointComplex
		normalizedSegmentLength = abs( normalizedSegment )
		if normalizedSegmentLength > 0.0:
			normalizedSegment /= normalizedSegmentLength
			segmentYMirror = complex( normalizedSegment.real, - normalizedSegment.imag )
			behindRotated = segmentYMirror * behindComplex
			behindMidpointRotated = segmentYMirror * behindMidpointComplex
			aheadRotated = segmentYMirror * aheadComplex
			aheadMidpointRotated = segmentYMirror * aheadMidpointComplex
			y = behindRotated.imag
			isYAboveFirst = y > aheadRotated.imag
			isYAboveSecond = y > aheadMidpointRotated.imag
			if isYAboveFirst != isYAboveSecond:
				xIntersection = euclidean.getXIntersectionFromComplex( aheadRotated, aheadMidpointRotated, y )
				if xIntersection > min( behindMidpointRotated.real, behindRotated.real ) and xIntersection < max( behindMidpointRotated.real, behindRotated.real ):
					intersectionPointRotated = Vec3( xIntersection, y, behind.z )
					intersectionPoint = euclidean.getRoundZAxisByPlaneAngle( normalizedSegment, intersectionPointRotated )
					loop[ ( pointIndex + len( loop ) - 1 ) % len( loop ) ] = intersectionPoint
					del loop[ pointIndex ]
					return

def removeIntersectionComplex( loopComplex ):
	"Get loop without the first intersection."
	withoutIntersection = []
	for pointIndex in range( len( loopComplex ) ):
		behindComplex = loopComplex[ ( pointIndex + len( loopComplex ) - 1 ) % len( loopComplex ) ]
		behindEndComplex = loopComplex[ ( pointIndex + len( loopComplex ) - 2 ) % len( loopComplex ) ]
		behindMidpointComplex = 0.5 * ( behindComplex + behindEndComplex )
		aheadComplex = loopComplex[ pointIndex ]
		aheadEndComplex = loopComplex[ ( pointIndex + 1 ) % len( loopComplex ) ]
		aheadMidpointComplex = 0.5 * ( aheadComplex + aheadEndComplex )
		normalizedSegment = behindComplex - behindMidpointComplex
		normalizedSegmentLength = abs( normalizedSegment )
		if normalizedSegmentLength > 0.0:
			normalizedSegment /= normalizedSegmentLength
			segmentYMirror = complex( normalizedSegment.real, - normalizedSegment.imag )
			behindRotated = segmentYMirror * behindComplex
			behindMidpointRotated = segmentYMirror * behindMidpointComplex
			aheadRotated = segmentYMirror * aheadComplex
			aheadMidpointRotated = segmentYMirror * aheadMidpointComplex
			y = behindRotated.imag
			isYAboveFirst = y > aheadRotated.imag
			isYAboveSecond = y > aheadMidpointRotated.imag
			if isYAboveFirst != isYAboveSecond:
				xIntersection = euclidean.getXIntersectionFromComplex( aheadRotated, aheadMidpointRotated, y )
				if xIntersection > min( behindMidpointRotated.real, behindRotated.real ) and xIntersection < max( behindMidpointRotated.real, behindRotated.real ):
					intersectionPoint = normalizedSegment * complex( xIntersection, y )
					loopComplex[ ( pointIndex + len( loopComplex ) - 1 ) % len( loopComplex ) ] = intersectionPoint
					del loopComplex[ pointIndex ]
					return

def setZAccordingToOperatingJump( loop, operatingJump ):
	"Set of the loop to the first point, increasing by the operating jump if it exists."
	if len( loop ) < 1:
		return
	z = loop[ 0 ].z
	if operatingJump != None:
		z += operatingJump
	for point in loop:
		point.z = z


class BoundingLoop:
	"A class to hold a bounding loop composed of a minimum complex, a maximum complex and an outset loop."
	def __cmp__( self, other ):
		"Get comparison in order to sort bounding loops in descending order of area."
		if self.area < other.area:
			return 1
		if self.area > other.area:
			return - 1
		return 0

	def __repr__( self ):
		"Get the string representation of this bounding loop."
		return '%s, %s, %s' % ( self.minimum, self.maximum, self.loop )

	def getFromLoop( self, loop ):
		"Get the bounding loop from a path."
		self.loop = loop
		self.maximum = euclidean.getComplexMaximumFromVec3List( loop )
		self.minimum = euclidean.getComplexMinimumFromVec3List( loop )
		return self

	def getOutsetBoundingLoop( self, outsetDistance ):
		"Outset the bounding rectangle and loop by a distance."
		outsetBoundingLoop = BoundingLoop()
		outsetBoundingLoop.maximum = self.maximum + complex( outsetDistance, outsetDistance )
		outsetBoundingLoop.minimum = self.minimum - complex( outsetDistance, outsetDistance )
		greaterThanOutsetDistance = 1.1 * outsetDistance
		centers = getCentersFromLoopDirection( True, self.loop, greaterThanOutsetDistance )
		outsetBoundingLoop.loop = getSimplifiedInsetFromClockwiseLoop( centers[ 0 ], outsetDistance )
		return outsetBoundingLoop

	def isEntirelyInsideAnother( self, anotherBoundingLoop ):
		"Determine if this bounding loop is entirely inside another bounding loop."
		if self.minimum.imag < anotherBoundingLoop.minimum.imag or self.minimum.real < anotherBoundingLoop.minimum.real:
			return False
		if self.maximum.imag > anotherBoundingLoop.maximum.imag or self.maximum.real > anotherBoundingLoop.maximum.real:
			return False
		for point in self.loop:
			if euclidean.getNumberOfIntersectionsToLeft( point, anotherBoundingLoop.loop ) % 2 == 0:
				return False
		return not isLoopIntersectingLoop( anotherBoundingLoop.loop, self.loop ) #later check for intersection on only acute angles

#	def isIntersectingList( self, boundingLoops ):
#		"Determine if this bounding loop is any of a list of bounding loops."
#		for boundingLoop in boundingLoops:
#			if not self.isRectangleMissingAnother( boundingLoop ):
#				if isLoopIntersectingLoop( boundingLoop.loop, self.loop ):
#					return True
#		return False
#
	def isOverlappingAnother( self, anotherBoundingLoop ):
		"Determine if this bounding loop is intersecting another bounding loop."
		if self.isRectangleMissingAnother( anotherBoundingLoop ):
			return False
		for point in self.loop:
			if euclidean.getNumberOfIntersectionsToLeft( point, anotherBoundingLoop.loop ) % 2 == 1:
				return True
		for point in anotherBoundingLoop.loop:
			if euclidean.getNumberOfIntersectionsToLeft( point, self.loop ) % 2 == 1:
				return True
		return isLoopIntersectingLoop( anotherBoundingLoop.loop, self.loop ) #later check for intersection on only acute angles

	def isRectangleMissingAnother( self, anotherBoundingLoop ):
		"Determine if the rectangle of this bounding loop is missing the rectangle of another bounding loop."
		if self.maximum.imag < anotherBoundingLoop.minimum.imag or self.maximum.real < anotherBoundingLoop.minimum.real:
			return True
		return self.minimum.imag > anotherBoundingLoop.maximum.imag or self.minimum.real > anotherBoundingLoop.maximum.real


class CircleIntersection:
	"An intersection of two circles."
	def __init__( self ):
		self.circleNodeAhead = None
		self.circleNodeBehind = None
		self.index = 0
		self.steppedOn = False

	def __repr__( self ):
		"Get the string representation of this CircleIntersection."
		return str( self.index ) + " " + str( self.getAbsolutePosition() ) + " " + str( self.circleNodeBehind.index ) + ' ' + str( self.circleNodeAhead.index ) + " " + str( self.getCircleIntersectionAhead().index )

	def addToList( self, circleIntersectionPath ):
		self.steppedOn = True
		circleIntersectionPath.append( self )

	def getAbsolutePosition( self ):
		return self.getPositionRelativeToBehind() + self.circleNodeBehind.circleComplex

	def getCircleIntersectionAhead( self ):
		circleIntersections = self.circleNodeAhead.circleIntersections
		circleIntersectionAhead = None
		smallestWiddershinsDot = 999999999.0
		positionRelativeToAhead = self.getAbsolutePosition() - self.circleNodeAhead.circleComplex
		positionRelativeToAhead = euclidean.getNormalized( positionRelativeToAhead )
		for circleIntersection in circleIntersections:
			if not circleIntersection.steppedOn:
				circleIntersectionRelative = circleIntersection.getPositionRelativeToBehind()
				circleIntersectionRelative = euclidean.getNormalized( circleIntersectionRelative )
				widdershinsDot = euclidean.getWiddershinsDotGivenComplex( positionRelativeToAhead, circleIntersectionRelative )
				if widdershinsDot < smallestWiddershinsDot:
					smallestWiddershinsDot = widdershinsDot
					circleIntersectionAhead = circleIntersection
		if circleIntersectionAhead == None:
			print( 'this should never happen, circleIntersectionAhead in intercircle is None' )
			print( self.circleNodeAhead.circle )
			for circleIntersection in circleIntersections:
				print( circleIntersection.circleNodeAhead.circle )
		return circleIntersectionAhead

	def getFromCircleNodes( self, circleNodeAhead, index, circleNodeBehind ):
		self.index = index
		self.circleNodeAhead = circleNodeAhead
		self.circleNodeBehind = circleNodeBehind
		return self

	def getPositionRelativeToBehind( self ):
		aheadMinusBehind = 0.5 * ( self.circleNodeAhead.circleComplex - self.circleNodeBehind.circleComplex )
		radius = self.circleNodeAhead.radius
		halfChordWidth = math.sqrt( radius * radius - aheadMinusBehind.real * aheadMinusBehind.real - aheadMinusBehind.imag * aheadMinusBehind.imag )
		rotatedClockwiseQuarter = complex( aheadMinusBehind.imag, - aheadMinusBehind.real )
		if abs( rotatedClockwiseQuarter ) == 0:
			print( self.circleNodeAhead.circle )
			print( self.circleNodeBehind.circle )
		return aheadMinusBehind + rotatedClockwiseQuarter * ( halfChordWidth / abs( rotatedClockwiseQuarter ) )

	def isWithinCircles( self, pixelTable, width ):
		absolutePosition = self.getAbsolutePosition()
		absolutePositionOverWidth = absolutePosition / width
		x = int( round( absolutePositionOverWidth.real ) )
		y = int( round( absolutePositionOverWidth.imag ) )
		squareValues = euclidean.getSquareValues( pixelTable, x, y )
		for squareValue in squareValues:
			if abs( squareValue.circleComplex - absolutePosition ) < self.circleNodeAhead.radius:
				if squareValue != self.circleNodeAhead and squareValue != self.circleNodeBehind:
					return True
		return False


class CircleIntersectionComplex:
	"An intersection of two complex circles."
	def __init__( self, circleNodeComplexAhead, index, circleNodeComplexBehind ):
		self.circleNodeComplexAhead = circleNodeComplexAhead
		self.circleNodeComplexBehind = circleNodeComplexBehind
		self.index = index
		self.steppedOn = False

	def __repr__( self ):
		"Get the string representation of this CircleIntersection."
		return '%s, %s, %s, %s, %s' % ( self.index, self.getAbsolutePosition(), self.circleNodeComplexBehind.index, self.circleNodeComplexAhead.index, self.getCircleIntersectionAhead().index )

	def addToList( self, circleIntersectionPath ):
		self.steppedOn = True
		circleIntersectionPath.append( self )

	def getAbsolutePosition( self ):
		return self.getPositionRelativeToBehind() + self.circleNodeComplexBehind.circleComplex

	def getCircleIntersectionAhead( self ):
		circleIntersections = self.circleNodeComplexAhead.circleIntersectionComplexes
		circleIntersectionAhead = None
		smallestWiddershinsDot = 999999999.0
		positionRelativeToAhead = self.getAbsolutePosition() - self.circleNodeComplexAhead.circleComplex
		positionRelativeToAhead = euclidean.getNormalized( positionRelativeToAhead )
		for circleIntersection in circleIntersections:
			if not circleIntersection.steppedOn:
				circleIntersectionRelative = circleIntersection.getPositionRelativeToBehind()
				circleIntersectionRelative = euclidean.getNormalized( circleIntersectionRelative )
				widdershinsDot = euclidean.getWiddershinsDotGivenComplex( positionRelativeToAhead, circleIntersectionRelative )
				if widdershinsDot < smallestWiddershinsDot:
					smallestWiddershinsDot = widdershinsDot
					circleIntersectionAhead = circleIntersection
		if circleIntersectionAhead == None:
			print( 'this should never happen, circleIntersectionAhead in intercircle is None' )
			print( self.circleNodeComplexAhead.circle )
			for circleIntersection in circleIntersections:
				print( circleIntersection.circleNodeComplexAhead.circle )
		return circleIntersectionAhead

	def getPositionRelativeToBehind( self ):
		aheadMinusBehind = 0.5 * ( self.circleNodeComplexAhead.circleComplex - self.circleNodeComplexBehind.circleComplex )
		radius = self.circleNodeComplexAhead.radius
		halfChordWidth = math.sqrt( radius * radius - aheadMinusBehind.real * aheadMinusBehind.real - aheadMinusBehind.imag * aheadMinusBehind.imag )
		rotatedClockwiseQuarter = complex( aheadMinusBehind.imag, - aheadMinusBehind.real )
		if abs( rotatedClockwiseQuarter ) == 0:
			print( self.circleNodeComplexAhead.circle )
			print( self.circleNodeComplexBehind.circle )
		return aheadMinusBehind + rotatedClockwiseQuarter * ( halfChordWidth / abs( rotatedClockwiseQuarter ) )

	def isWithinCircles( self, pixelTable, width ):
		absolutePosition = self.getAbsolutePosition()
		absolutePositionOverWidth = absolutePosition / width
		x = int( round( absolutePositionOverWidth.real ) )
		y = int( round( absolutePositionOverWidth.imag ) )
		squareValues = euclidean.getSquareValues( pixelTable, x, y )
		for squareValue in squareValues:
			if abs( squareValue.circleComplex - absolutePosition ) < self.circleNodeComplexAhead.radius:
				if squareValue != self.circleNodeComplexAhead and squareValue != self.circleNodeComplexBehind:
					return True
		return False


class CircleNode:
	"A node of circle intersections."
	def __init__( self ):
		self.circleIntersections = []
		self.circleComplex = None
		self.index = 0
		self.radius = 0.0

	def __repr__( self ):
		"Get the string representation of this CircleNode."
		return str( self.index ) + " " + str( self.circleComplex )

	def getFromCircleRadius( self, circle, index, radius ):
		self.circle = circle
		self.circleComplex = circle.dropAxis( 2 )
		self.diameter = radius + radius
		self.index = index
		self.radius = radius
		return self

	def getWithinNodes( self, pixelTable, width ):
		circleComplexOverWidth = self.circleComplex / width
		x = int( round( circleComplexOverWidth.real ) )
		y = int( round( circleComplexOverWidth.imag ) )
		withinNodes = []
		squareValues = euclidean.getSquareValues( pixelTable, x, y )
		for squareValue in squareValues:
			if abs( self.circleComplex - squareValue.circleComplex ) < self.diameter:
				withinNodes.append( squareValue )
		return withinNodes


class CircleNodeComplex:
	"A complex node of complex circle intersections."
	def __init__( self, circleComplex, index, radius ):
		self.circleComplex = circleComplex
		self.circleIntersectionComplexes = []
		self.diameter = radius + radius
		self.index = index
		self.radius = radius

	def __repr__( self ):
		"Get the string representation of this CircleNodeComplex."
		return '%s, %s' % ( self.index, self.circleComplex )

	def getWithinNodes( self, pixelTable, width ):
		circleComplexOverWidth = self.circleComplex / width
		x = int( round( circleComplexOverWidth.real ) )
		y = int( round( circleComplexOverWidth.imag ) )
		withinNodes = []
		squareValues = euclidean.getSquareValues( pixelTable, x, y )
		for squareValue in squareValues:
			if abs( self.circleComplex - squareValue.circleComplex ) < self.diameter:
				withinNodes.append( squareValue )
		return withinNodes

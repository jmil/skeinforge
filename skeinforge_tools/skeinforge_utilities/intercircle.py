"""
Intercircle is a collection of utilities for intersecting circles, used to get smooth loops around a collection of points and inset & outset loops.

"""

try:
	import psyco
	psyco.full()
except:
	pass
from vec3 import Vec3
import euclidean
import math


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


def addCircleIntersectionLoop( circleIntersectionPath, circleIntersections ):
	"Add a circle intersection loop."
	firstCircleIntersection = circleIntersectionPath[ 0 ]
	firstCircleIntersection.steppedOn = False
	circleIntersectionAhead = firstCircleIntersection
	for circleIntersectionIndex in range( len( circleIntersections ) + 1 ):
		circleIntersectionAhead = circleIntersectionAhead.getCircleIntersectionAhead()
		if circleIntersectionAhead.index == firstCircleIntersection.index:
			firstCircleIntersection.steppedOn = True
			return
		if circleIntersectionAhead.steppedOn == True:
			print( 'circleIntersectionAhead.steppedOn == True' )
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

def addPointsFromSegment( points, radius, pointBegin, pointEnd ):
	"Add points between the endpoints of a segment."
	thresholdRadius = radius * 0.9 # a higher number would be faster but would leave bigger dangling loops
	thresholdDiameter = thresholdRadius * 2.0
	segment = pointEnd.minus( pointBegin )
	segmentLength = segment.length()
	extraCircles = int( math.floor( segmentLength / thresholdDiameter ) )
	lengthIncrement = segmentLength / ( float( extraCircles ) + 1.0 )
	if segmentLength == 0.0:
		print( 'This should never happen, segmentLength = 0.0' )
		print( 'pointBegin' )
		print( pointBegin )
		print( pointEnd )
		return
	segment.scale( lengthIncrement / segmentLength )
	nextCircleCenter = pointBegin.plus( segment )
	for circleIndex in range( extraCircles ):
		points.append( nextCircleCenter )
		nextCircleCenter = nextCircleCenter.plus( segment )

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
		inset = getInsetFromClockwiseLoop( center, halfRadius )
		if euclidean.isPathInsideLoop( loop, inset ) != isOutside:
			outsideCenters.append( center )
	return outsideCenters

def getCircleIntersectionsFromCircleNodes( circleNodes ):
	"Get all the circle intersections with exist between all the circle nodes."
	circleIntersections = []
	index = 0
	for circleNodeIndex in range( len( circleNodes ) ):
		circleNodeBehind = circleNodes[ circleNodeIndex ]
		for aheadIndex in range( circleNodeIndex + 1, len( circleNodes ) ):
			circleNodeAhead = circleNodes[ aheadIndex ]
			if circleNodeBehind.isWithin( circleNodeAhead.circle ):
				circleIntersectionForward = CircleIntersection().getFromCircleNodes( circleNodeAhead, index, circleNodeBehind )
				if not circleIntersectionForward.isWithinCircles( circleNodes ):
					circleIntersections.append( circleIntersectionForward )
					circleNodeBehind.circleIntersections.append( circleIntersectionForward )
					index += 1
				circleIntersectionBackward = CircleIntersection().getFromCircleNodes( circleNodeBehind, index, circleNodeAhead )
				if not circleIntersectionBackward.isWithinCircles( circleNodes ):
					circleIntersections.append( circleIntersectionBackward )
					circleNodeAhead.circleIntersections.append( circleIntersectionBackward )
					index += 1
	return circleIntersections

def getCircleIntersectionLoops( circleIntersections ):
	"Get all the loops going through the circle intersections."
	circleIntersectionLoops = []
	for circleIntersection in circleIntersections:
		if not circleIntersection.steppedOn:
			circleIntersectionLoop = []
			circleIntersectionLoops.append( circleIntersectionLoop )
			circleIntersection.addToList( circleIntersectionLoop )
			addCircleIntersectionLoop( circleIntersectionLoop, circleIntersections )
	return circleIntersectionLoops

def getCircleNodesFromLoop( loop, radius ):
	"Get the circle nodes from every point on a loop and between points."
	points = []
	for pointIndex in range( len( loop ) ):
		point = loop[ pointIndex ]
		pointSecond = loop[ ( pointIndex + 1 ) % len( loop ) ]
		points.append( point )
		addPointsFromSegment( points, radius, point, pointSecond )
	return getCircleNodesFromPath( points, radius )

def getCircleNodesFromPath( path, radius ):
	"Get the circle nodes from a path."
	circleNodes = []
	for point in path:
		circleNodes.append( CircleNode().getFromCircleRadius( point, len( circleNodes ), radius ) )
	return circleNodes

def getInsetFromClockwiseLoop( loop, radius ):
	"Get loop inset from clockwise loop, out from widdershins loop."
	insetLoop = []
	for pointIndex in range( len( loop ) ):
		behindAbsolute = loop[ ( pointIndex + len( loop ) - 1 ) % len( loop ) ]
		center = loop[ pointIndex ]
		aheadAbsolute = loop[ ( pointIndex + 1 ) % len( loop ) ]
		insetLoop.append( getInsetFromClockwiseTriple( aheadAbsolute, behindAbsolute, center, radius ) )
	return getWithoutIntersections( euclidean.getSimplifiedLoop( insetLoop, radius ) )

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

def getIntersectionAtInset( ahead, behind, inset ):
	"Get circle intersection loop at inset from segment."
	aheadMinusBehind = ahead.minus( behind )
	aheadMinusBehind.scale( 0.5 )
	rotatedClockwiseQuarter = euclidean.getRotatedClockwiseQuarterAroundZAxis( aheadMinusBehind )
	rotatedClockwiseQuarter.scale( inset / rotatedClockwiseQuarter.length() )
	aheadMinusBehind.add( rotatedClockwiseQuarter )
	aheadMinusBehind.add( behind )
	return aheadMinusBehind

def getLoopsFromLoopsDirection( isWiddershins, loops ):
	"Get the loops going round in a given direction."
	directionalLoops = []
	for loop in loops:
		if euclidean.isWiddershins( loop ) == isWiddershins:
			directionalLoops.append( loop )
	return directionalLoops

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
		behindEnd = loop[ ( pointIndex + len( loop ) - 2 ) % len( loop ) ]
		behindMidpoint = ( behind.plus( behindEnd ) ).times( 0.5 )
		ahead = loop[ pointIndex ]
		aheadEnd = loop[ ( pointIndex + 1 ) % len( loop ) ]
		aheadMidpoint = ( ahead.plus( aheadEnd ) ).times( 0.5 )
		normalizedSegment = behind.dropAxis( 2 ) - behindMidpoint.dropAxis( 2 )
		normalizedSegmentLength = abs( normalizedSegment )
		if normalizedSegmentLength > 0.0:
			normalizedSegment /= normalizedSegmentLength
			segmentYMirror = complex( normalizedSegment.real, - normalizedSegment.imag )
			behindRotated = euclidean.getRoundZAxisByPlaneAngle( segmentYMirror, behind )
			behindMidpointRotated = euclidean.getRoundZAxisByPlaneAngle( segmentYMirror, behindMidpoint )
			aheadRotated = euclidean.getRoundZAxisByPlaneAngle( segmentYMirror, ahead )
			aheadMidpointRotated = euclidean.getRoundZAxisByPlaneAngle( segmentYMirror, aheadMidpoint )
			y = behindRotated.y
			isYAboveFirst = y > aheadRotated.y
			isYAboveSecond = y > aheadMidpointRotated.y
			if isYAboveFirst != isYAboveSecond:
				xIntersection = euclidean.getXIntersection( aheadRotated, aheadMidpointRotated, y )
				if xIntersection > min( behindMidpointRotated.x, behindRotated.x ) and xIntersection < max( behindMidpointRotated.x, behindRotated.x ):
					intersectionPointRotated = Vec3( xIntersection, y, behindRotated.z )
					intersectionPoint = euclidean.getRoundZAxisByPlaneAngle( normalizedSegment, intersectionPointRotated )
					loop[ ( pointIndex + len( loop ) - 1 ) % len( loop ) ] = intersectionPoint
					del loop[ pointIndex ]
					return


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
		outsetBoundingLoop.loop = getInsetFromClockwiseLoop( centers[ 0 ], outsetDistance )
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
		return self.getPositionRelativeToBehind().plus( self.circleNodeBehind.circle )

	def getCircleIntersectionAhead( self ):
		circleIntersections = self.circleNodeAhead.circleIntersections
		circleIntersectionAhead = None
		smallestWiddershinsDot = 999999999.0
		positionRelativeToAhead = self.getAbsolutePosition().minus( self.circleNodeAhead.circle )
		for circleIntersection in circleIntersections:
			if not circleIntersection.steppedOn:
				circleIntersectionRelative = circleIntersection.getPositionRelativeToBehind()
				circleIntersectionRelative.normalize()
				widdershinsDot = euclidean.getWiddershinsDot( positionRelativeToAhead, circleIntersectionRelative )
				if widdershinsDot < smallestWiddershinsDot:
					smallestWiddershinsDot = widdershinsDot
					circleIntersectionAhead = circleIntersection
		return circleIntersectionAhead

	def getFromCircleNodes( self, circleNodeAhead, index, circleNodeBehind ):
		self.index = index
		self.circleNodeAhead = circleNodeAhead
		self.circleNodeBehind = circleNodeBehind
		return self

	def getPositionRelativeToBehind( self ):
		aheadMinusBehind = self.circleNodeAhead.circle.minus( self.circleNodeBehind.circle )
		aheadMinusBehind.scale( 0.5 )
		halfChordWidth = math.sqrt( self.circleNodeAhead.radiusSquared - aheadMinusBehind.length2() )
		rotatedClockwiseQuarter = euclidean.getRotatedClockwiseQuarterAroundZAxis( aheadMinusBehind )
		rotatedClockwiseQuarter.scale( halfChordWidth / rotatedClockwiseQuarter.length() )
		aheadMinusBehind.add( rotatedClockwiseQuarter )
		return aheadMinusBehind

	def isWithinCircles( self, circleNodes ):
		absolutePosition = self.getAbsolutePosition()
		radiusSquared = self.circleNodeAhead.radiusSquared
		for circleNode in circleNodes:
			if circleNode.circle.distance2( absolutePosition ) < radiusSquared:
				if circleNode != self.circleNodeAhead and circleNode != self.circleNodeBehind:
					return True
		return False


class CircleNode:
	"A node of circle intersections."
	def __init__( self ):
		self.circleIntersections = []
		self.circle = None
		self.diameterSquared = 0.0
		self.index = 0
		self.radius = 0.0
		self.radiusSquared = 0.0

	def __repr__( self ):
		"Get the string representation of this CircleNode."
		return str( self.index ) + " " + str( self.circle )

	def getFromCircleRadius( self, circle, index, radius ):
		self.circle = circle
		self.index = index
		self.radius = radius
		self.radiusSquared = radius * radius
		self.diameterSquared = 4.0 * self.radiusSquared
		return self

	def isWithin( self, circle ):
		return self.circle.distance2( circle ) < self.diameterSquared

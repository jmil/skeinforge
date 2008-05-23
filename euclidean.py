"""
Euclidean is a collection of python utilities for complex numbers, paths, polygons & Vec3s.

To use euclidean, install python 2.x on your machine, which is avaliable from http://www.python.org/download/

Then in the folder which euclidean is in, type 'python' in a shell to run the python interpreter.  Finally type
'import euclidean' to import these utilities and 'from vec3 import Vec3' to import the Vec3 class.


Below are examples of euclidean use.

>>> from euclidean import *
>>> from vec3 import Vec3
>>> origin=Vec3()
>>> right=Vec3(1.0,0.0,0.0)
>>> back=Vec3(0.0,1.0,0.0)
>>> getAngleAroundZAxisDifference(back, right)
1.5707963267948966
>>> getPointMaximum(right,back)
1.0, 1.0, 0.0
>>> polygon=[origin, right, back]
>>> getPolygonLength(polygon)
3.4142135623730949
>>> getPolygonArea(polygon)
0.5
"""

try:
	import psyco
	psyco.full()
except:
	pass
from vec3 import Vec3
import math


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


def addXIntersections( loop, solidIndex, xIntersectionList, y ):
	"Add the x intersections for a loop."
	for pointIndex in range( len( loop ) ):
		pointFirst = loop[ pointIndex ]
		pointSecond = loop[ ( pointIndex + 1 ) % len( loop ) ]
		isYAboveFirst = y > pointFirst.y
		isYAboveSecond = y > pointSecond.y
		if isYAboveFirst != isYAboveSecond:
			xIntersection = getXIntersection( pointFirst, pointSecond, y )
			xIntersectionList.append( complex( xIntersection, float( solidIndex ) ) )

def addXIntersectionsFromLoops( loops, solidIndex, xIntersectionList, y ):
	"Add the x intersections for the loops."
	for loop in loops:
		addXIntersections( loop, solidIndex, xIntersectionList, y )

def compareSolidXByX( solidXFirst, solidXSecond ):
	if solidXFirst.real > solidXSecond.real:
		return 1
	if solidXFirst.real < solidXSecond.real:
		return - 1
	return 0

def getAngleAroundZAxisDifference( subtractFromVec3, subtractVec3 ):
	"""Get the angle around the Z axis difference between a pair of Vec3s.

	Keyword arguments:
	subtractFromVec3 -- Vec3 whose angle will be subtracted from
	subtractVec3 -- Vec3 whose angle will be subtracted"""
	subtractVectorMirror = complex( subtractVec3.x , - subtractVec3.y )
	differenceVector = getRoundZAxisByPlaneAngle( subtractVectorMirror, subtractFromVec3 )
	return math.atan2( differenceVector.y, differenceVector.x )

def getAroundLoop( begin, end, loop ):
	"Get an arc around a loop."
	aroundLoop = []
	if end <= begin:
		end += len( loop )
	for pointIndex in range( begin, end ):
		aroundLoop.append( loop[ pointIndex % len( loop ) ] )
	return aroundLoop

def getAwayPath( path, radius ):
	"Get a loop with only the points that are far enough away from each other."
	away = []
	overlapDistanceSquared = 0.0001 * radius * radius
	for pointIndex in range( len( path ) ):
		if not isClose( overlapDistanceSquared, path, pointIndex ):
			point = path[ pointIndex ]
			away.append( point )
	return away

def getDistanceSquaredToPlaneSegment( segmentBegin, segmentEnd, point ):
	"Get the distance squared from a point to the x & y components of a segment."
	segmentDifference = segmentEnd.minus( segmentBegin )
	pointMinusSegmentBegin = point.minus( segmentBegin )
	beginPlaneDot = getPlaneDot( pointMinusSegmentBegin, segmentDifference )
	if beginPlaneDot <= 0.0:
		return point.distance2( segmentBegin )
	differencePlaneDot = getPlaneDot( segmentDifference, segmentDifference )
	if differencePlaneDot <= beginPlaneDot:
		return point.distance2( segmentEnd )
	intercept = beginPlaneDot / differencePlaneDot
	segmentDifference.scale( intercept )
	interceptPerpendicular = segmentBegin.plus( segmentDifference )
	return point.distance2( interceptPerpendicular )

def getHalfSimplifiedLoop( loop, radius, remainder ):
	"Get the loop with half of the points inside the channel removed."
	if len( loop ) < 2:
		return loop
	channelRadius = radius * .01
	simplified = []
	for pointIndex in range( len( loop ) ):
		point = loop[ pointIndex ]
		if pointIndex % 2 == remainder:
			simplified.append( point )
		else:
			if not isWithinChannel( channelRadius, pointIndex, loop ):
				simplified.append( point )
	return simplified

def getLeftPoint( path ):
	"Get the leftmost point in the path."
	left = 999999999.0
	leftPoint = None
	for point in path:
		if point.x < left:
			left = point.x
			leftPoint = point
	return leftPoint

def getMaximumSpan( loop ):
	"Get the maximum span in the xy plane."
	front = 999999999.0
	left = front
	right = - left
	back = right
	for point in loop:
		back = max( back, point.y )
		front = min( front, point.y )
		left = min( left, point.x )
		right = max( right, point.x )
		xSpan = right - left
		ySpan = back - front
	return max( xSpan, ySpan )

def getNearestDistanceSquaredIndex( point, loop ):
	"Get the distance squared to the nearest segment of the loop and index of that segment."
	smallestDistanceSquared = 999999999999999999.0
	nearestDistanceSquaredIndex = None
	for pointIndex in range( len( loop ) ):
		segmentBegin = loop[ pointIndex ]
		segmentEnd = loop[ ( pointIndex + 1 ) % len( loop ) ]
		distanceSquared = getDistanceSquaredToPlaneSegment( segmentBegin, segmentEnd, point )
		if distanceSquared < smallestDistanceSquared:
			smallestDistanceSquared = distanceSquared
			nearestDistanceSquaredIndex = complex( distanceSquared, float( pointIndex ) )
	return nearestDistanceSquaredIndex

def getNearestPointOnSegment( segmentBegin, segmentEnd, point ):
	segmentDifference = segmentEnd.minus( segmentBegin )
	pointMinusSegmentBegin = point.minus( segmentBegin )
	beginPlaneDot = getPlaneDot( pointMinusSegmentBegin, segmentDifference )
	differencePlaneDot = getPlaneDot( segmentDifference, segmentDifference )
	intercept = beginPlaneDot / differencePlaneDot
	intercept = max( intercept, 0.0 )
	intercept = min( intercept, 1.0 )
	segmentDifference.scale( intercept )
	return segmentBegin.plus( segmentDifference )

def getNumberOfIntersectionsToLeft( leftPoint, loop ):
	"Get the number of intersections through the loop for the line starting from the left point and going left."
	numberOfIntersectionsToLeft = 0
	for pointIndex in range( len( loop ) ):
		firstPoint = loop[ pointIndex ]
		secondPoint = loop[ ( pointIndex + 1 ) % len( loop ) ]
		isLeftAboveFirst = leftPoint.y > firstPoint.y
		isLeftAboveSecond = leftPoint.y > secondPoint.y
		if isLeftAboveFirst != isLeftAboveSecond:
			if getXIntersection( firstPoint, secondPoint, leftPoint.y ) < leftPoint.x:
				numberOfIntersectionsToLeft += 1
	return numberOfIntersectionsToLeft

def getPathLength( path ):
	"Get the length of a path ( an open polyline )."
	pathLength = 0.0
	for pointIndex in range( len( path ) - 1 ):
		firstPoint = path[ pointIndex ]
		secondPoint  = path[ pointIndex + 1 ]
		pathLength += firstPoint.distance( secondPoint )
	return pathLength

def getPathRoundZAxisByPlaneAngle( planeAngle, path ):
	"""Get Vec3 array rotated by a plane angle.

	Keyword arguments:
	planeAngle - plane angle of the rotation
	path - Vec3 array whose rotation will be returned"""
	planeArray = []
	for point in path:
		planeArray.append( getRoundZAxisByPlaneAngle( planeAngle, point ) )
	return planeArray

def getPlaneDot( vec3First, vec3Second ):
	"Get the dot product of the x and y components of a pair of Vec3s."
	return vec3First.x * vec3Second.x + vec3First.y * vec3Second.y

def getPlaneDotPlusOne( vec3First, vec3Second ):
	"Get the dot product plus one of the x and y components of a pair of Vec3s."
	return 1.0 + getPlaneDot( vec3First, vec3Second )

def getPointMaximum( firstPoint, secondPoint ):
	"Get a point with each component the maximum of the respective components of a pair of Vec3s."
	return Vec3( max( firstPoint.x, secondPoint.x ), max( firstPoint.y, secondPoint.y ), max( firstPoint.z, secondPoint.z ) )

def getPointMinimum( firstPoint, secondPoint ):
	"Get a point with each component the minimum of the respective components of a pair of Vec3s."
	return Vec3( min( firstPoint.x, secondPoint.x ), min( firstPoint.y, secondPoint.y ), min( firstPoint.z, secondPoint.z ) )

def getPointPlusSegmentWithLength( length, point, segment ):
	"Get point plus a segment scaled to a given length."
	return segment.times( length / segment.length() ).plus( point )

def getPolar( angle, radius ):
	"""Get polar complex from counterclockwise angle from 1, 0 and radius.

	Keyword arguments:
	angle -- counterclockwise angle from 1, 0
	radius -- radius of complex"""
	return complex( radius * math.cos( angle ), radius * math.sin( angle ) )

def getPolygonArea( polygon ):
	"Get the xy plane area of a polygon."
	polygonArea = 0.0
	for pointIndex in range( len( polygon ) ):
		point = polygon[ pointIndex ]
		secondPoint  = polygon[ ( pointIndex + 1 ) % len( polygon ) ]
		area  = point.x * secondPoint.y - secondPoint.x * point.y
		polygonArea += area
	return 0.5 * polygonArea

def getPolygonLength( polygon ):
	"Get the length of a polygon perimeter."
	polygonLength = 0.0
	for pointIndex in range( len( polygon ) ):
		point = polygon[ pointIndex ]
		secondPoint  = polygon[ ( pointIndex + 1 ) % len( polygon ) ]
		polygonLength += point.distance( secondPoint )
	return polygonLength

def getRotatedClockwiseQuarterAroundZAxis( vector3 ):
	"Get vector3 rotated a quarter clockwise turn around Z axis."
	return Vec3( vector3.y, - vector3.x, vector3.z )

def getRotatedWiddershinsQuarterAroundZAxis( vector3 ):
	"Get Vec3 rotated a quarter widdershins turn around Z axis."
	return Vec3( - vector3.y, vector3.x, vector3.z )

def getRoundedPoint( point ):
	"Get point with each component rounded."
	return Vec3( round( point.x ), round( point.y ), round( point.z ) )

def getRoundedToThreePlaces( number ):
	"Get value rounded to three places as string."
	return str( 0.001 * math.floor( number * 1000.0 + 0.5 ) )

def getRoundXAxis( angle, vector3 ):
	"""Get Vec3 rotated around X axis from widdershins angle and Vec3.

	Keyword arguments:
	angle - widdershins angle from 1, 0
	vector3 - Vec3 whose rotation will be returned"""
	x = math.cos( angle );
	y = math.sin( angle );
	return Vec3( vector3.x, vector3.y * x - vector3.z * y, vector3.y * y + vector3.z * x )

def getRoundYAxis( angle, vector3 ):
	"""Get Vec3 rotated around Y axis from widdershins angle and Vec3.

	Keyword arguments:
	angle - widdershins angle from 1, 0
	vector3 - Vec3 whose rotation will be returned"""
	x = math.cos( angle );
	y = math.sin( angle );
	return Vec3( vector3.x * x - vector3.z * y, vector3.y, vector3.x * y + vector3.z * x )

def getRoundZAxis( angle, vector3 ):
	"""Get Vec3 rotated around Z axis from widdershins angle and Vec3.

	Keyword arguments:
	angle - widdershins angle from 1, 0
	vector3 - Vec3 whose rotation will be returned"""
	x = math.cos( angle );
	y = math.sin( angle );
	return Vec3( vector3.x * x - vector3.y * y, vector3.x * y + vector3.y * x, vector3.z )

def getRoundZAxisByPlaneAngle( planeAngle, vector3 ):
	"""Get Vec3 rotated by a plane angle.

	Keyword arguments:
	planeAngle - plane angle of the rotation
	vector3 - Vec3 whose rotation will be returned"""
	return Vec3( vector3.x * planeAngle.real - vector3.y * planeAngle.imag, vector3.x * planeAngle.imag + vector3.y * planeAngle.real, vector3.z )

def getSimplifiedLoop( loop, radius ):
	"Get loop with points inside the channel removed."
	if len( loop ) < 2:
		return loop
	simplificationMultiplication = 256
	simplificationRadius = radius / float( simplificationMultiplication )
	maximumIndex = len( loop ) * simplificationMultiplication
	pointIndex = 1
	while pointIndex < maximumIndex:
		loop = getHalfSimplifiedLoop( loop, simplificationRadius, 0 )
		loop = getHalfSimplifiedLoop( loop, simplificationRadius, 1 )
		simplificationRadius += simplificationRadius
		simplificationRadius = min( simplificationRadius, radius )
		pointIndex += pointIndex
	return getAwayPath( loop, radius )

def getXIntersection( firstPoint, secondPoint, y ):
	"Get where the line crosses y."
	secondMinusFirst = secondPoint.minus( firstPoint )
	yMinusFirst = y - firstPoint.y
	return yMinusFirst / secondMinusFirst.y * secondMinusFirst.x + firstPoint.x

def getWiddershinsDot( vec3First, vec3Second ):
	"Get the magintude of the positive dot product plus one of the x and y components of a pair of Vec3s, with the reversed sign of the cross product."
	dot = getPlaneDotPlusOne( vec3First, vec3Second )
	zCross = getZComponentCrossProduct( vec3First, vec3Second )
	if zCross >= 0.0:
		return - dot
	return dot

def getZComponentCrossProduct( vec3First, vec3Second ):
	"Get z component cross product of a pair of Vec3s."
	return vec3First.x * vec3Second.y - vec3First.y * vec3Second.x

def isClose( overlapDistanceSquared, loop, pointIndex ):
	"Determine if the the point close to another point on the loop."
	point = loop[ pointIndex ]
	for overlapPoint in loop[ : pointIndex ]:
		if overlapPoint.distance2( point ) < overlapDistanceSquared:
			return True
	return False

def isLineCrossingInsideXSegment( segmentFirstX, segmentSecondX, vector3First, vector3Second, y ):
	"Determine if the line is crossing inside the x segment."
	isYAboveFirst = y > vector3First.y
	isYAboveSecond = y > vector3Second.y
	if isYAboveFirst == isYAboveSecond:
		return False
	xIntersection = getXIntersection( vector3First, vector3Second, y )
	if xIntersection <= min( segmentFirstX, segmentSecondX ):
		return False
	return xIntersection < max( segmentFirstX, segmentSecondX )

def isSegmentCompletelyInX( segment, xFirst, xSecond ):
	"Determine if the segment overlaps within x."
	segmentFirstX = segment[ 0 ].point.x
	segmentSecondX = segment[ 1 ].point.x
	if max( segmentFirstX, segmentSecondX ) > max( xFirst, xSecond ):
		return False
	return min( segmentFirstX, segmentSecondX ) >= min( xFirst, xSecond )

def isWiddershins( polygon ):
	"Determines if the polygon goes round in the widdershins direction."
	return getPolygonArea( polygon ) > 0.0

def isWithinChannel( channelRadius, pointIndex, loop ):
	"Determine if the the point is within the channel between two adjacent points."
	point = loop[ pointIndex ]
	behindPosition = loop[ ( pointIndex + len( loop ) - 1 ) % len( loop ) ]
	behindSegment = behindPosition.minus( point )
	behindSegmentLength = behindSegment.length()
	if behindSegmentLength < channelRadius:
		return True
	aheadPosition = loop[ ( pointIndex + 1 ) % len( loop ) ]
	aheadSegment = aheadPosition.minus( point )
	aheadSegmentLength = aheadSegment.length()
	if aheadSegmentLength < channelRadius:
		return True
	behindSegment.scale( 1.0 / behindSegmentLength )
	aheadSegment.scale( 1.0 / aheadSegmentLength )
	absoluteZ = getPlaneDotPlusOne( aheadSegment, behindSegment )
	if behindSegmentLength * absoluteZ < channelRadius:
		return True
	if aheadSegmentLength * absoluteZ < channelRadius:
		return True
	return False

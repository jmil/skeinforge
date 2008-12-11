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

from __future__ import absolute_import
try:
	import psyco
	psyco.full()
except:
	pass
#Init has to be imported first because it has code to workaround the python bug where relative imports don't work if the module is imported as a main module.
import __init__

from skeinforge_tools.skeinforge_utilities.vec3 import Vec3
import math


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


def addCircleToPixelTable( pixelTable, pointComplex ):
	"Add pixel to the pixel table."
	xStep = int( round( pointComplex.real ) )
	yStep = int( round( pointComplex.imag ) )
	for xCircleStep in xrange( xStep - 2, xStep + 3 ):
		for yCircleStep in xrange( yStep - 2, yStep + 3 ):
			stepKey = ( xCircleStep, yCircleStep )
			pixelTable[ stepKey ] = None

def addElementToPixelList( element, pixelTable, x, y ):
	"Add an element to the pixel list."
	stepKey = getStepKey( x, y )
	if stepKey in pixelTable:
		pixelTable[ stepKey ].append( element )
	else:
		pixelTable[ stepKey ] = [ element ]

def addLoopToPixelTable( loop, pixelTable, width ):
	"Add loop to the pixel table."
	for pointIndex in xrange( len( loop ) ):
		pointBegin = loop[ pointIndex ]
		pointEnd = loop[ ( pointIndex + 1 ) % len( loop ) ]
		addSegmentToPixelTable( pointBegin.dropAxis( 2 ), pointEnd.dropAxis( 2 ), pixelTable, 0, 0, width )

def addPathToPixelTable( path, pixelTable, width ):
	"Add path to the pixel table."
	for pointIndex in xrange( len( path ) - 1 ):
		pointBegin = path[ pointIndex ]
		pointEnd = path[ pointIndex + 1 ]
		addSegmentToPixelTable( pointBegin.dropAxis( 2 ), pointEnd.dropAxis( 2 ), pixelTable, 0, 0, width )

def addPixelToPixelTable( pixelTable, value, x, y ):
	"Add pixel to the pixel table."
	pixelTable[ getStepKey( x, y ) ] = value

def addPixelToPixelTableWithSteepness( isSteep, pixelTable, x, y ):
	"Add pixels to the pixel table with steepness."
	if isSteep:
		addPixelToPixelTable( pixelTable, None, y, x )
	else:
		addPixelToPixelTable( pixelTable, None, x, y )

def addPointToPath( path, pixelTable, point, width ):
	"Add a point to a path and the pixel table."
	path.append( point )
	if len( path ) < 2:
		return
	pointComplex = point.dropAxis( 2 )
	beginComplex = path[ - 2 ].dropAxis( 2 )
	addSegmentToPixelTable( beginComplex, pointComplex, pixelTable, 0, 0, width )

def addSegmentToPixelTable( beginComplex, endComplex, pixelTable, shortenDistanceBegin, shortenDistanceEnd, width ):
	"Add line segment to the pixel table."
	if abs( beginComplex - endComplex ) <= 0.0:
		return
	beginComplex /= width
	endComplex /= width
	if shortenDistanceBegin > 0.0:
		endMinusBeginComplex = endComplex - beginComplex
		endMinusBeginComplexLength = abs( endMinusBeginComplex )
		if endMinusBeginComplexLength < shortenDistanceBegin:
			return
		beginComplex = beginComplex + endMinusBeginComplex * shortenDistanceBegin / endMinusBeginComplexLength
	if shortenDistanceEnd > 0.0:
		beginMinusEndComplex = beginComplex - endComplex
		beginMinusEndComplexLength = abs( beginMinusEndComplex )
		if beginMinusEndComplexLength < shortenDistanceEnd:
			return
		endComplex = endComplex + beginMinusEndComplex * shortenDistanceEnd / beginMinusEndComplexLength
	deltaX = endComplex.real - beginComplex.real
	deltaY = endComplex.imag - beginComplex.imag
	isSteep = abs( deltaY ) > abs( deltaX )
	if isSteep:
		beginComplex = complex( beginComplex.imag, beginComplex.real )
		endComplex = complex( endComplex.imag, endComplex.real )
	if beginComplex.real > endComplex.real:
		newBeginComplex = endComplex
		endComplex = beginComplex
		beginComplex = newBeginComplex
	deltaX = endComplex.real - beginComplex.real
	deltaY = endComplex.imag - beginComplex.imag
	gradient = deltaY / deltaX
	xEnd = int( round( beginComplex.real ) )
	yEnd = beginComplex.imag + gradient * ( xEnd - beginComplex.real )
	xGap = getReverseFloatPart( beginComplex.real + 0.5 )
	beginStep = xEnd
	addPixelToPixelTableWithSteepness( isSteep, pixelTable, xEnd, int( math.floor( yEnd ) ) )
	addPixelToPixelTableWithSteepness( isSteep, pixelTable, xEnd, int( math.floor( yEnd ) ) + 1 )
	intersectionY = yEnd + gradient
	xEnd = int( round( endComplex.real ) )
	yEnd = endComplex.imag + gradient * ( xEnd - endComplex.real )
	xGap = getReverseFloatPart( endComplex.real + 0.5 )
	addPixelToPixelTableWithSteepness( isSteep, pixelTable,  xEnd, int( math.floor( yEnd ) ) )
	addPixelToPixelTableWithSteepness( isSteep, pixelTable, xEnd, int( math.floor( yEnd ) ) + 1 )
	for x in xrange( beginStep + 1, xEnd ):
		addPixelToPixelTableWithSteepness( isSteep, pixelTable, x, int( math.floor( intersectionY ) ) )
		addPixelToPixelTableWithSteepness( isSteep, pixelTable, x, int( math.floor( intersectionY ) ) + 1 )
		intersectionY += gradient

def addSurroundingLoopBeginning( loop, skein ):
	"Add surrounding loop beginning to gcode output."
	skein.addLine( '(<surroundingLoop> )' )
	for point in loop:
		skein.addLine( '(<boundaryPoint> X%s Y%s Z%s )' % ( skein.getRounded( point.x ), skein.getRounded( point.y ), skein.getRounded( point.z ) ) )

def addSurroundingLoopComplexBeginning( loop, skein, z ):
	"Add surrounding loop beginning to gcode output."
	skein.addLine( '(<surroundingLoop> )' )
	for point in loop:
		skein.addLine( '(<boundaryPoint> X%s Y%s Z%s )' % ( skein.getRounded( point.real ), skein.getRounded( point.imag ), skein.getRounded( z ) ) )

def addToThreadsFromLoop( extrusionHalfWidthSquared, gcodeType, loop, oldOrderedLocation, skein ):
	"Add to threads from the last location from loop."
	loop = getLoopStartingNearest( extrusionHalfWidthSquared, oldOrderedLocation, loop )
	oldOrderedLocation.setToVec3( loop[ 0 ] )
	skein.addLine( gcodeType )
	skein.addGcodeFromThread( loop + [ loop[ 0 ] ] ) # Turn extruder on and indicate that a loop is beginning.

def addToThreadsRemoveFromSurroundings( oldOrderedLocation, surroundingLoops, skein ):
	"Add to threads from the last location from surrounding loops."
	while len( surroundingLoops ) > 0:
		getTransferClosestSurroundingLoop( oldOrderedLocation, surroundingLoops, skein )

def addXIntersectionIndexes( loop, solidIndex, xIntersectionIndexList, y ):
	"Add the x intersections for a loop."
	for pointIndex in range( len( loop ) ):
		pointFirst = loop[ pointIndex ]
		pointSecond = loop[ ( pointIndex + 1 ) % len( loop ) ]
		isYAboveFirst = y > pointFirst.y
		isYAboveSecond = y > pointSecond.y
		if isYAboveFirst != isYAboveSecond:
			xIntersection = getXIntersection( pointFirst, pointSecond, y )
			xIntersectionIndexList.append( XIntersectionIndex( solidIndex, xIntersection ) )

def addXIntersectionIndexesFromComplexes( loop, solidIndex, xIntersectionIndexList, y ):
	"Add the x intersections for a loop."
	for pointIndex in range( len( loop ) ):
		pointFirst = loop[ pointIndex ]
		pointSecond = loop[ ( pointIndex + 1 ) % len( loop ) ]
		isYAboveFirst = y > pointFirst.imag
		isYAboveSecond = y > pointSecond.imag
		if isYAboveFirst != isYAboveSecond:
			xIntersection = getXIntersectionFromComplex( pointFirst, pointSecond, y )
			xIntersectionIndexList.append( XIntersectionIndex( solidIndex, xIntersection ) )

def addXIntersectionIndexesFromLoopListComplexes( loopLists, xIntersectionIndexList, y ):
	"Add the x intersections for the loop lists."
	for loopListIndex in range( len( loopLists ) ):
		loopList = loopLists[ loopListIndex ]
		for loop in loopList:
			addXIntersectionIndexesFromComplexes( loop, loopListIndex, xIntersectionIndexList, y )

def addXIntersectionIndexesFromLoopLists( loopLists, xIntersectionIndexList, y ):
	"Add the x intersections for the loop lists."
	for loopListIndex in range( len( loopLists ) ):
		loopList = loopLists[ loopListIndex ]
		for loop in loopList:
			addXIntersectionIndexes( loop, loopListIndex, xIntersectionIndexList, y )

def addXIntersectionIndexesFromLoops( loops, solidIndex, xIntersectionIndexList, y ):
	"Add the x intersections for the loops."
	for loop in loops:
		addXIntersectionIndexes( loop, solidIndex, xIntersectionIndexList, y )

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
	pixelTable = {}
	width = 1.01 * radius
	for point in path:
		x = int( round( point.x / width ) )
		y = int( round( point.y / width ) )
		if not isCloseXYPlane( overlapDistanceSquared, pixelTable, point, x, y ):
			away.append( point )
			addElementToPixelList( point, pixelTable, x, y )
	return away

def getAwayPointComplexes( pointComplexes, radius ):
	"Get a path with only the points that are far enough away from each other."
	away = []
	overlapDistance = 0.01 * radius
	pixelTable = {}
	width = 1.01 * radius
	for pointComplex in pointComplexes:
		pointComplexOverWidth = pointComplex / width
		x = int( round( pointComplexOverWidth.real ) )
		y = int( round( pointComplexOverWidth.imag ) )
		if not isCloseXYPlaneComplex( overlapDistance, pixelTable, pointComplex, x, y ):
			away.append( pointComplex )
			addElementToPixelList( pointComplex, pixelTable, x, y )
	return away

def getBackOfLoops( loops ):
	"Get the back of the loops."
	negativeFloat = - 999999999.75342341
	back = negativeFloat
	for loop in loops:
		for point in loop:
			back = max( back, point.y )
	if back == negativeFloat:
		print( "This should never happen, there are no loops for getBackOfLoops in euclidean." )
	return back

def getClippedAtEndLoopPath( clip, loopPath ):
	"Get a clipped loop path."
	if clip <= 0.0:
		return loopPath
	loopPathLength = getPathLength( loopPath )
	clip = min( clip, 0.3 * loopPathLength )
	lastLength = 0.0
	pointIndex = 0
	totalLength = 0.0
	clippedLength = loopPathLength - clip
	while totalLength < clippedLength and pointIndex < len( loopPath ) - 1:
		firstPoint = loopPath[ pointIndex ]
		secondPoint  = loopPath[ pointIndex + 1 ]
		pointIndex += 1
		lastLength = totalLength
		totalLength += firstPoint.distance( secondPoint )
	remainingLength = clippedLength - lastLength
	clippedLoopPath = loopPath[ : pointIndex ]
	ultimateClippedPoint = loopPath[ pointIndex ]
	penultimateClippedPoint = clippedLoopPath[ - 1 ]
	segment = ultimateClippedPoint.minus( penultimateClippedPoint )
	segmentLength = segment.length()
	if segmentLength <= 0.0:
		return clippedLoopPath
	newUltimatePoint = penultimateClippedPoint.plus( segment.times( remainingLength / segmentLength ) )
	return clippedLoopPath + [ newUltimatePoint ]

def getClippedLoopPath( clip, loopPath ):
	"Get a clipped loop path."
	if clip <= 0.0:
		return loopPath
	loopPathLength = getPathLength( loopPath )
	clip = min( clip, 0.3 * loopPathLength )
	lastLength = 0.0
	pointIndex = 0
	totalLength = 0.0
	while totalLength < clip and pointIndex < len( loopPath ) - 1:
		firstPoint = loopPath[ pointIndex ]
		secondPoint  = loopPath[ pointIndex + 1 ]
		pointIndex += 1
		lastLength = totalLength
		totalLength += firstPoint.distance( secondPoint )
	remainingLength = clip - lastLength
	clippedLoopPath = loopPath[ pointIndex : ]
	ultimateClippedPoint = clippedLoopPath[ 0 ]
	penultimateClippedPoint = loopPath[ pointIndex - 1 ]
	segment = ultimateClippedPoint.minus( penultimateClippedPoint )
	segmentLength = segment.length()
	loopPath = clippedLoopPath
	if segmentLength > 0.0:
		newUltimatePoint = penultimateClippedPoint.plus( segment.times( remainingLength / segmentLength ) )
		loopPath = [ newUltimatePoint ] + loopPath
	return getClippedAtEndLoopPath( clip, loopPath )

def getComplexCrossProduct( firstComplex, secondComplex ):
	"Get z component cross product of a pair of complexes."
	return firstComplex.real * secondComplex.imag - firstComplex.imag * secondComplex.real

def getComplexDot( firstComplex, secondComplex ):
	"Get the dot product of a pair of complexes."
	return firstComplex.real * secondComplex.real + firstComplex.imag * secondComplex.imag

def getComplexDotPlusOne( firstComplex, secondComplex ):
	"Get the dot product plus one of the x and y components of a pair of Vec3s."
	return 1.0 + getComplexDot( firstComplex, secondComplex )

def getComplexMaximum( firstComplex, secondComplex ):
	"Get a complex with each component the maximum of the respective components of a pair of complexes."
	return complex( max( firstComplex.real, secondComplex.real ), max( firstComplex.imag, secondComplex.imag ) )

def getComplexMaximumFromPointComplexes( pointComplexes ):
	"Get a complex with each component the maximum of the respective components of a list of complex points."
	maximum = complex( - 999999999.0, - 999999999.0 )
	for pointComplex in pointComplexes:
		maximum = getComplexMaximum( maximum, pointComplex )
	return maximum

def getComplexMaximumFromVec3List( vec3List ):
	"Get a complex with each component the maximum of the respective components of a list of Vec3s."
	maximum = complex( - 999999999.0, - 999999999.0 )
	for point in vec3List:
		maximum = getComplexMaximum( maximum, point.dropAxis( 2 ) )
	return maximum

def getComplexMinimum( firstComplex, secondComplex ):
	"Get a complex with each component the minimum of the respective components of a pair of complexes."
	return complex( min( firstComplex.real, secondComplex.real ), min( firstComplex.imag, secondComplex.imag ) )

def getComplexMinimumFromPointComplexes( pointComplexes ):
	"Get a complex with each component the minimum of the respective components of a list of complex points."
	minimum = complex( 999999999.0, 999999999.0 )
	for pointComplex in pointComplexes:
		minimum = getComplexMinimum( minimum, pointComplex )
	return minimum

def getComplexMinimumFromVec3List( vec3List ):
	"Get a complex with each component the minimum of the respective components of a list of Vec3s."
	minimum = complex( 999999999.0, 999999999.0 )
	for point in vec3List:
		minimum = getComplexMinimum( minimum, point.dropAxis( 2 ) )
	return minimum

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

def getFillOfSurroundings( surroundingLoops ):
	"Get extra fill loops of surrounding loops."
	fillSurroundings = []
	for surroundingLoop in surroundingLoops:
		fillSurroundings += surroundingLoop.getFillLoops()
	return fillSurroundings

def getFloatPart( number ):
	"Get the float part of the number."
	return number - math.floor( number )

def getFrontOfLoops( loops ):
	"Get the front of the loops."
	bigFloat = 999999999.196854654
	front = bigFloat
	for loop in loops:
		for point in loop:
			front = min( front, point.y )
	if front == bigFloat:
		print( "This should never happen, there are no loops for getFrontOfLoops in euclidean." )
	return front

def getHalfSimplifiedLoop( loop, radius, remainder ):
	"Get the loop with half of the points inside the channel removed."
	if len( loop ) < 2:
		return loop
	channelRadius = radius * .01
	simplified = []
	addIndex = 0
	if remainder == 1:
		addIndex = len( loop ) - 1
	for pointIndex in range( len( loop ) ):
		point = loop[ pointIndex ]
		if pointIndex % 2 == remainder or pointIndex == addIndex:
			simplified.append( point )
		elif not isWithinChannel( channelRadius, pointIndex, loop ):
			simplified.append( point )
	return simplified

def getHalfSimplifiedLoopComplex( loopComplex, radius, remainder ):
	"Get the loop with half of the points inside the channel removed."
	if len( loopComplex ) < 2:
		return loopComplex
	channelRadius = radius * .01
	simplified = []
	addIndex = 0
	if remainder == 1:
		addIndex = len( loopComplex ) - 1
	for pointIndex in range( len( loopComplex ) ):
		point = loopComplex[ pointIndex ]
		if pointIndex % 2 == remainder or pointIndex == addIndex:
			simplified.append( point )
		elif not isWithinChannelComplex( channelRadius, pointIndex, loopComplex ):
			simplified.append( point )
	return simplified

def getHalfSimplifiedPath( path, radius, remainder ):
	"Get the path with half of the points inside the channel removed."
	if len( path ) < 2:
		return path
	channelRadius = radius * .01
	simplified = []
	addIndex = len( path ) - 1
	for pointIndex in range( len( path ) ):
		point = path[ pointIndex ]
		if pointIndex % 2 == remainder or pointIndex == 0 or pointIndex == addIndex:
			simplified.append( point )
		elif not isWithinChannel( channelRadius, pointIndex, path ):
			simplified.append( point )
	return simplified

def getInsidesAddToOutsides( loops, outsides ):
	"Add loops to either the insides or outsides."
	insides = []
	for loopIndex in range( len( loops ) ):
		loop = loops[ loopIndex ]
		if isInsideOtherLoops( loopIndex, loops ):
			insides.append( loop )
		else:
			outsides.append( loop )
	return insides

def getIntermediateLocation( alongWay, begin, end ):
	"Get the intermediate location between begin and end."
	return ( begin.times( 1.0 - alongWay ) ).plus( end.times( alongWay ) )

def getIntermediateLocationComplex( alongWay, begin, end ):
	"Get the intermediate location between begin and end."
	return begin * ( 1.0 - alongWay ) + end * alongWay

def getLargestLoop( loops ):
	"Get largest loop from loops."
	largestArea = - 999999999.0
	largestLoop = None
	for loop in loops:
		loopArea = abs( getPolygonArea( loop ) )
		if loopArea > largestArea:
			largestArea = loopArea
			largestLoop = loop
	return largestLoop

def getLeftPoint( path ):
	"Get the leftmost point in the path."
	left = 999999999.0
	leftPoint = None
	for point in path:
		if point.x < left:
			left = point.x
			leftPoint = point
	return leftPoint

def getLeftPointComplex( pointComplexes ):
	"Get the leftmost complex point in the points."
	leftmost = 999999999.0
	leftPointComplex = None
	for pointComplex in pointComplexes:
		if pointComplex.real < leftmost:
			leftmost = pointComplex.real
			leftPointComplex = pointComplex
	return leftPointComplex

def getLoopComplexMaximumSpan( loop ):
	"Get the maximum span of the loop."
	extent = getComplexMaximumFromPointComplexes( loop ) - getComplexMinimumFromPointComplexes( loop )
	return max( extent.real, extent.imag )

def getLoopStartingNearest( extrusionHalfWidthSquared, location, loop ):
	"Add to threads from the last location from loop."
	nearestIndex = int( round( getNearestDistanceSquaredIndex( location, loop ).imag ) )
	loop = getAroundLoop( nearestIndex, nearestIndex, loop )
	nearestPoint = getNearestPointOnSegment( loop[ 0 ], loop[ 1 ], location )
	if nearestPoint.distance2( loop[ 0 ] ) > extrusionHalfWidthSquared and nearestPoint.distance2( loop[ 1 ] ) > extrusionHalfWidthSquared:
		loop = [ nearestPoint ] + loop[ 1 : ] + [ loop[ 0 ] ]
	elif nearestPoint.distance2( loop[ 0 ] ) > nearestPoint.distance2( loop[ 1 ] ):
		loop = loop[ 1 : ] + [ loop[ 0 ] ]
	return loop

def getMaximumSpan( loop ):
	"Get the maximum span in the xy plane."
	extent = getComplexMaximumFromVec3List( loop ) - getComplexMinimumFromVec3List( loop )
	return max( extent.real, extent.imag )

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

def getNearestPathDistanceSquaredIndex( point, path ):
	"Get the distance squared to the nearest segment of the path and index of that segment."
	smallestDistanceSquared = 999999999999999999.0
	nearestDistanceSquaredIndex = None
	for pointIndex in range( len( path ) - 1 ):
		segmentBegin = path[ pointIndex ]
		segmentEnd = path[ pointIndex + 1 ]
		distanceSquared = getDistanceSquaredToPlaneSegment( segmentBegin, segmentEnd, point )
		if distanceSquared < smallestDistanceSquared:
			smallestDistanceSquared = distanceSquared
			nearestDistanceSquaredIndex = complex( distanceSquared, float( pointIndex ) )
	return nearestDistanceSquaredIndex

def getNearestPointOnSegment( segmentBegin, segmentEnd, point ):
	"Get the nearest point on the segment."
	segmentDifference = segmentEnd.minus( segmentBegin )
	pointMinusSegmentBegin = point.minus( segmentBegin )
	beginPlaneDot = getPlaneDot( pointMinusSegmentBegin, segmentDifference )
	differencePlaneDot = getPlaneDot( segmentDifference, segmentDifference )
	intercept = beginPlaneDot / differencePlaneDot
	intercept = max( intercept, 0.0 )
	intercept = min( intercept, 1.0 )
	segmentDifference.scale( intercept )
	return segmentBegin.plus( segmentDifference )

def getNormalized( complexNumber ):
	"Get the normalized complex."
	complexNumberLength = abs( complexNumber )
	if complexNumberLength > 0.0:
		return complexNumber / complexNumberLength
	return complexNumber

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

def getNumberOfIntersectionsToLeftComplex( leftPointComplex, loopComplex ):
	"Get the number of intersections through the loop for the line starting from the left point and going left."
	numberOfIntersectionsToLeft = 0
	for pointIndex in range( len( loopComplex ) ):
		firstPointComplex = loopComplex[ pointIndex ]
		secondPointComplex = loopComplex[ ( pointIndex + 1 ) % len( loopComplex ) ]
		isLeftAboveFirst = leftPointComplex.imag > firstPointComplex.imag
		isLeftAboveSecond = leftPointComplex.imag > secondPointComplex.imag
		if isLeftAboveFirst != isLeftAboveSecond:
			if getXIntersectionFromComplex( firstPointComplex, secondPointComplex, leftPointComplex.imag ) < leftPointComplex.real:
				numberOfIntersectionsToLeft += 1
	return numberOfIntersectionsToLeft

def getOrderedSurroundingLoops( extrusionWidth, surroundingLoops ):
	"Get ordered surrounding loops from surrounding loops."
	insides = []
	orderedSurroundingLoops = []
	for loopIndex in range( len( surroundingLoops ) ):
		surroundingLoop = surroundingLoops[ loopIndex ]
		otherLoops = []
		for beforeIndex in range( loopIndex ):
			otherLoops.append( surroundingLoops[ beforeIndex ].boundary )
		for afterIndex in range( loopIndex + 1, len( surroundingLoops ) ):
			otherLoops.append( surroundingLoops[ afterIndex ].boundary )
		if isPathInsideLoops( otherLoops, surroundingLoop.boundary ):
			insides.append( surroundingLoop )
		else:
			orderedSurroundingLoops.append( surroundingLoop )
	for outside in orderedSurroundingLoops:
		outside.getFromInsideSurroundings( extrusionWidth, insides )
	return orderedSurroundingLoops

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

#def getPathWithoutCloseSequentials( path, radius ):
#	"Get a path without points in a row which are too close too each other."
#	pathWithoutCloseSequentials = []
#	closeDistanceSquared = 0.0001 * radius * radius
#	lastPoint = None
#	for point in path:
#		if lastPoint == None:
#			pathWithoutCloseSequentials.append( point )
#		elif lastPoint.distance2( point ) > closeDistanceSquared:
#			pathWithoutCloseSequentials.append( point )
#		lastPoint = point
#	return pathWithoutCloseSequentials
#

def getPathsFromEndpoints( endpoints, fillInset, pixelTable, width ):
	"Get paths from endpoints."
#	segmentTable = {}
	for beginningEndpoint in endpoints[ : : 2 ]:
		beginningPoint = beginningEndpoint.point
		addSegmentToPixelTable( beginningPoint.dropAxis( 2 ), beginningEndpoint.otherEndpoint.point.dropAxis( 2 ), pixelTable, 0, 0, width )
#		addSegmentToPixelTable( beginningPoint.dropAxis( 2 ), beginningEndpoint.otherEndpoint.point.dropAxis( 2 ), segmentTable, 0, 0, width )
	endpointFirst = endpoints[ 0 ]
	endpoints.remove( endpointFirst )
	otherEndpoint = endpointFirst.otherEndpoint
	endpoints.remove( otherEndpoint )
	nextEndpoint = None
	path = []
	paths = [ path ]
	if len( endpoints ) > 1:
		nextEndpoint = otherEndpoint.getNearestMiss( endpoints, path, pixelTable, width )
		if nextEndpoint != None:
			if nextEndpoint.point.distance2( endpointFirst.point ) < nextEndpoint.point.distance2( otherEndpoint.point ):
				endpointFirst = endpointFirst.otherEndpoint
				otherEndpoint = endpointFirst.otherEndpoint
	addPointToPath( path, pixelTable, endpointFirst.point, width )
	addPointToPath( path, pixelTable, otherEndpoint.point, width )
	while len( endpoints ) > 1:
		nextEndpoint = otherEndpoint.getNearestMiss( endpoints, path, pixelTable, width )
		if nextEndpoint == None:
			path = []
			paths.append( path )
			nextEndpoint = otherEndpoint.getNearestEndpoint( endpoints )
		addPointToPath( path, pixelTable, nextEndpoint.point, width )
		endpoints.remove( nextEndpoint )
		otherEndpoint = nextEndpoint.otherEndpoint
		hop = nextEndpoint.getHop( fillInset, path )
		if hop != None:
			path = [ hop ]
			paths.append( path )
		addPointToPath( path, pixelTable, otherEndpoint.point, width )
		endpoints.remove( otherEndpoint )
#	removePixelTableFromPixelTable( segmentTable, pixelTable )
	return paths

def getPlaneDot( vec3First, vec3Second ):
	"Get the dot product of the x and y components of a pair of Vec3s."
	return vec3First.x * vec3Second.x + vec3First.y * vec3Second.y

def getPlaneDotPlusOne( vec3First, vec3Second ):
	"Get the dot product plus one of the x and y components of a pair of Vec3s."
	return 1.0 + getPlaneDot( vec3First, vec3Second )

def getPointComplexesFromPoints( points ):
	"Get complex path from a Vec3 path."
	pointComplexes = []
	for point in points:
		pointComplexes.append( point.dropAxis( 2 ) )
	return pointComplexes

def getPointComplexesRoundZAxisByComplex( planeAngle, points ):
	"Get points rotated by the plane angle"
	planeArray = []
	for point in points:
		planeArray.append( planeAngle * point )
	return planeArray

def getPointMaximum( firstPoint, secondPoint ):
	"Get a point with each component the maximum of the respective components of a pair of Vec3s."
	return Vec3( max( firstPoint.x, secondPoint.x ), max( firstPoint.y, secondPoint.y ), max( firstPoint.z, secondPoint.z ) )

def getPointMinimum( firstPoint, secondPoint ):
	"Get a point with each component the minimum of the respective components of a pair of Vec3s."
	return Vec3( min( firstPoint.x, secondPoint.x ), min( firstPoint.y, secondPoint.y ), min( firstPoint.z, secondPoint.z ) )

def getPointPlusSegmentWithLength( length, point, segment ):
	"Get point plus a segment scaled to a given length."
	return segment.times( length / segment.length() ).plus( point )

def getPointsFromPointComplexesZ( pointComplexes, z ):
	"Get Vec3 points from a complex points and z."
	points = []
	for pointComplex in pointComplexes:
		points.append( Vec3( pointComplex.real, pointComplex.imag, z ) )
	return points

def getPointsListFromPointComplexesListZ( pointComplexesList, z ):
	"Get Vec3 points list from a complex points list and z."
	pointsList = []
	for pointComplexes in pointComplexesList:
		pointsList.append( getPointsFromPointComplexesZ( pointComplexes, z ) )
	return pointsList

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

def getPolygonComplexArea( polygonComplex ):
	"Get the area of a complex polygon."
	polygonComplexArea = 0.0
	for pointIndex in range( len( polygonComplex ) ):
		pointComplex = polygonComplex[ pointIndex ]
		secondPointComplex  = polygonComplex[ ( pointIndex + 1 ) % len( polygonComplex ) ]
		area  = pointComplex.real * secondPointComplex.imag - secondPointComplex.real * pointComplex.imag
		polygonComplexArea += area
	return 0.5 * polygonComplexArea

def getPolygonLength( polygon ):
	"Get the length of a polygon perimeter."
	polygonLength = 0.0
	for pointIndex in range( len( polygon ) ):
		point = polygon[ pointIndex ]
		secondPoint  = polygon[ ( pointIndex + 1 ) % len( polygon ) ]
		polygonLength += point.distance( secondPoint )
	return polygonLength

def getReverseFloatPart( number ):
	"Get the reverse float part of the number."
	return 1.0 - getFloatPart( number )

def getRotatedClockwiseQuarterAroundZAxis( vector3 ):
	"Get vector3 rotated a quarter clockwise turn around Z axis."
	return Vec3( vector3.y, - vector3.x, vector3.z )

def getRotatedWiddershinsQuarterAroundZAxis( vector3 ):
	"Get Vec3 rotated a quarter widdershins turn around Z axis."
	return Vec3( - vector3.y, vector3.x, vector3.z )

def getRoundedPoint( point ):
	"Get point with each component rounded."
	return Vec3( round( point.x ), round( point.y ), round( point.z ) )

def getRoundedToDecimalPlaces( decimalPlaces, number ):
	"Get number rounded to a number of decimal places as a string."
	decimalPlacesRounded = max( 1.0, round( decimalPlaces ) )
	tenPowerInteger = round( math.pow( 10.0, decimalPlacesRounded ) )
	return str( round( number * tenPowerInteger ) / tenPowerInteger )

def getRoundedToThreePlaces( number ):
	"Get number rounded to three places as a string."
	return str( 0.001 * round( number * 1000.0 ) )

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

def getSegmentComplexesFromXIntersectionIndexes( xIntersectionIndexList, y ):
	"Get endpoint segments from the x intersection indexes."
	xIntersections = getXIntersectionsFromIntersections( xIntersectionIndexList )
	return getSegmentComplexesFromXIntersections( xIntersections, y )

def getSegmentComplexesFromXIntersections( xIntersections, y ):
	"Get endpoint segments from the x intersections."
	segments = []
	for xIntersectionIndex in range( 0, len( xIntersections ), 2 ):
		firstX = xIntersections[ xIntersectionIndex ]
		secondX = xIntersections[ xIntersectionIndex + 1 ]
		if firstX != secondX:
			segments.append( getSegmentComplexFromPoints( complex( firstX, y ), complex( secondX, y ) ) )
	return segments

def getSegmentComplexFromPoints( begin, end ):
	"Get endpoint segment from a pair of points."
	endpointFirst = EndpointComplex()
	endpointSecond = EndpointComplex().getFromOtherPoint( endpointFirst, end )
	endpointFirst.getFromOtherPoint( endpointSecond, begin )
	return ( endpointFirst, endpointSecond )

def getSegmentFromPoints( begin, end ):
	"Get endpoint segment from a pair of points."
	endpointFirst = Endpoint()
	endpointSecond = Endpoint().getFromOtherPoint( endpointFirst, end )
	endpointFirst.getFromOtherPoint( endpointSecond, begin )
	return ( endpointFirst, endpointSecond )

def getSegmentsFromXIntersections( xIntersections, y, z ):
	"Get endpoint segments from the x intersections."
	segments = []
	for xIntersectionIndex in range( 0, len( xIntersections ), 2 ):
		firstX = xIntersections[ xIntersectionIndex ]
		secondX = xIntersections[ xIntersectionIndex + 1 ]
		if firstX != secondX:
			segments.append( getSegmentFromPoints( Vec3( firstX, y, z ), Vec3( secondX, y, z ) ) )
	return segments

def getSegmentsFromXIntersectionIndexes( xIntersectionIndexList, y, z ):
	"Get endpoint segments from the x intersection indexes."
	xIntersections = getXIntersectionsFromIntersections( xIntersectionIndexList )
	return getSegmentsFromXIntersections( xIntersections, y, z )

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

def getSimplifiedLoopAtFirstZ( loop, radius ):
	"Get loop at the first z with points inside the channel removed."
	loopComplex = getPointComplexesFromPoints( loop )
	loopComplex = getSimplifiedLoopComplex( loopComplex, radius )
	return getPointsFromPointComplexesZ( loopComplex, loop[ 0 ].z )

def getSimplifiedLoopComplex( loopComplex, radius ):
	"Get loop with points inside the channel removed."
	if len( loopComplex ) < 2:
		return loopComplex
	simplificationMultiplication = 256
	simplificationRadius = radius / float( simplificationMultiplication )
	maximumIndex = len( loopComplex ) * simplificationMultiplication
	pointIndex = 1
	while pointIndex < maximumIndex:
		loopComplex = getHalfSimplifiedLoopComplex( loopComplex, simplificationRadius, 0 )
		loopComplex = getHalfSimplifiedLoopComplex( loopComplex, simplificationRadius, 1 )
		simplificationRadius += simplificationRadius
		simplificationRadius = min( simplificationRadius, radius )
		pointIndex += pointIndex
	return getAwayPointComplexes( loopComplex, radius )

def getSimplifiedPath( path, radius ):
	"Get path with points inside the channel removed."
	if len( path ) < 2:
		return path
	simplificationMultiplication = 256
	simplificationRadius = radius / float( simplificationMultiplication )
	maximumIndex = len( path ) * simplificationMultiplication
	pointIndex = 1
	while pointIndex < maximumIndex:
		path = getHalfSimplifiedPath( path, simplificationRadius, 0 )
		path = getHalfSimplifiedPath( path, simplificationRadius, 1 )
		simplificationRadius += simplificationRadius
		simplificationRadius = min( simplificationRadius, radius )
		pointIndex += pointIndex
	return getAwayPath( path, radius )

def getSquareValues( pixelTable, x, y ):
	"Get a list of the values in a square around the x and y pixel coordinates."
	squareValues = []
	for xStep in xrange( x - 1, x + 2 ):
		for yStep in xrange( y - 1, y + 2 ):
			stepKey = getStepKey( xStep, yStep )
			if stepKey in pixelTable:
				squareValues += pixelTable[ stepKey ]
	return squareValues

def getStepKey( x, y ):
	"Get step key for x and y."
	return ( x, y )

def getTransferClosestSurroundingLoop( oldOrderedLocation, remainingSurroundingLoops, skein ):
	"Get and transfer the closest remaining surrounding loop."
	closestDistanceSquared = 999999999999999999.0
	closestSurroundingLoop = None
	for remainingSurroundingLoop in remainingSurroundingLoops:
		distanceSquared = getNearestDistanceSquaredIndex( oldOrderedLocation, remainingSurroundingLoop.boundary ).real
		if distanceSquared < closestDistanceSquared:
			closestDistanceSquared = distanceSquared
			closestSurroundingLoop = remainingSurroundingLoop
	remainingSurroundingLoops.remove( closestSurroundingLoop )
	closestSurroundingLoop.addToThreads( oldOrderedLocation, skein )
	return closestSurroundingLoop

def getTransferredPaths( insides, loop ):
	"Get transferred paths from inside paths."
	transferredPaths = []
	for insideIndex in range( len( insides ) - 1, - 1, - 1 ):
		inside = insides[ insideIndex ]
		if isPathInsideLoop( loop, inside ):
			transferredPaths.append( inside )
			del insides[ insideIndex ]
	return transferredPaths

def getTransferredSurroundingLoops( insides, loop ):
	"Get transferred paths from inside surrounding loops."
	transferredSurroundings = []
	for insideIndex in range( len( insides ) - 1, - 1, - 1 ):
		insideSurrounding = insides[ insideIndex ]
		if isPathInsideLoop( loop, insideSurrounding.boundary ):
			transferredSurroundings.append( insideSurrounding )
			del insides[ insideIndex ]
	return transferredSurroundings

def getXIntersection( firstPoint, secondPoint, y ):
	"Get where the line crosses y."
	secondMinusFirst = secondPoint.minus( firstPoint )
	yMinusFirst = y - firstPoint.y
	return yMinusFirst / secondMinusFirst.y * secondMinusFirst.x + firstPoint.x

def getXIntersectionFromComplex( firstComplex, secondComplex, y ):
	"Get where the line crosses y."
	secondMinusFirstComplex = secondComplex - firstComplex
	yMinusFirst = y - firstComplex.imag
	return yMinusFirst / secondMinusFirstComplex.imag * secondMinusFirstComplex.real + firstComplex.real

def getXIntersectionsFromIntersections( xIntersectionIndexList ):
	"Get x intersections from the x intersection index list, in other words subtract non negative intersections from negatives."
	xIntersections = []
	fill = False
	solid = False
	solidTable = {}
	xIntersectionIndexList.sort()
	for solidX in xIntersectionIndexList:
		if solidX.index >= 0:
			toggleHashtable( solidTable, solidX.index, "" )
		else:
			fill = not fill
		oldSolid = solid
		solid = ( len( solidTable ) == 0 and fill )
		if oldSolid != solid:
			xIntersections.append( solidX.x )
	return xIntersections

def getWiddershinsDot( vec3First, vec3Second ):
	"Get the magintude of the positive dot product plus one of the x and y components of a pair of Vec3s, with the reversed sign of the cross product."
	dot = getPlaneDotPlusOne( vec3First, vec3Second )
	zCross = getZComponentCrossProduct( vec3First, vec3Second )
	if zCross >= 0.0:
		return - dot
	return dot

def getWiddershinsDotGivenComplex( complexFirst, complexSecond ):
	"Get the magintude of the positive dot product plus one of the x and y components of a pair of complexes, with the reversed sign of the cross product."
	dot = getComplexDotPlusOne( complexFirst, complexSecond )
	if complexFirst.real * complexSecond.imag - complexFirst.imag * complexSecond.real >= 0.0:
		return - dot
	return dot

def getZComponentCrossProduct( vec3First, vec3Second ):
	"Get z component cross product of a pair of Vec3s."
	return vec3First.x * vec3Second.y - vec3First.y * vec3Second.x

def isCloseXYPlane( overlapDistanceSquared, pixelTable, point, x, y ):
	"Determine if the point is close to another point on the loop in the xy plane."
	squareValues = getSquareValues( pixelTable, x, y )
	for squareValue in squareValues:
		if squareValue.distance2XYPlane( point ) < overlapDistanceSquared:
			return True
	return False

def isCloseXYPlaneComplex( overlapDistance, pixelTable, pointComplex, x, y ):
	"Determine if the point is close to another point on the loop."
	squareValues = getSquareValues( pixelTable, x, y )
	for squareValue in squareValues:
		if abs( squareValue - pointComplex ) < overlapDistance:
			return True
	return False

def isInsideOtherLoops( loopIndex, loops ):
	"Determine if a loop in a list is inside another loop in that list."
	return isPathInsideLoops( loops[ : loopIndex ] + loops[ loopIndex + 1 : ], loops[ loopIndex ] )

def isLargeSameDirection( inset, loop, requiredSize ):
	"Determine if the inset is in the same direction as the loop and if the inset is as large as the required size."
	if isWiddershins( inset ) != isWiddershins( loop ):
		return False
	return getMaximumSpan( inset ) > requiredSize

def isLineComplexIntersectingInsideXSegment( segmentFirstX, segmentSecondX, vector3First, vector3Second, y ):
	"Determine if the line is crossing inside the x segment."
	isYAboveFirst = y > vector3First.imag
	isYAboveSecond = y > vector3Second.imag
	if isYAboveFirst == isYAboveSecond:
		return False
	xIntersection = getXIntersectionFromComplex( vector3First, vector3Second, y )
	if xIntersection <= min( segmentFirstX, segmentSecondX ):
		return False
	return xIntersection < max( segmentFirstX, segmentSecondX )

def isLineIntersectingInsideXSegment( segmentFirstX, segmentSecondX, vector3First, vector3Second, y ):
	"Determine if the line is crossing inside the x segment."
	isYAboveFirst = y > vector3First.y
	isYAboveSecond = y > vector3Second.y
	if isYAboveFirst == isYAboveSecond:
		return False
	xIntersection = getXIntersection( vector3First, vector3Second, y )
	if xIntersection <= min( segmentFirstX, segmentSecondX ):
		return False
	return xIntersection < max( segmentFirstX, segmentSecondX )

def isLineIntersectingLoopComplexes( loops, pointBegin, pointEnd ):
	"Determine if the line is intersecting loops."
	normalizedSegment = pointEnd - pointBegin
	normalizedSegmentLength = abs( normalizedSegment )
	if normalizedSegmentLength > 0.0:
		normalizedSegment /= normalizedSegmentLength
		segmentYMirror = complex( normalizedSegment.real, - normalizedSegment.imag )
		pointBeginRotated = segmentYMirror * pointBegin
		pointEndRotated = segmentYMirror * pointEnd
		if isLoopListComplexIntersectingInsideXSegment( loops, pointBeginRotated.real, pointEndRotated.real, segmentYMirror, pointBeginRotated.imag ):
			return True
	return False

def isLineIntersectingLoops( loops, pointBegin, pointEnd ):
	"Determine if the line is intersecting loops."
	normalizedSegment = pointEnd.dropAxis( 2 ) - pointBegin.dropAxis( 2 )
	normalizedSegmentLength = abs( normalizedSegment )
	if normalizedSegmentLength > 0.0:
		normalizedSegment /= normalizedSegmentLength
		segmentYMirror = complex( normalizedSegment.real, - normalizedSegment.imag )
		pointBeginRotated = getRoundZAxisByPlaneAngle( segmentYMirror, pointBegin )
		pointEndRotated = getRoundZAxisByPlaneAngle( segmentYMirror, pointEnd )
		if isLoopListIntersectingInsideXSegment( loops, pointBeginRotated.x, pointEndRotated.x, segmentYMirror, pointBeginRotated.y ):
			return True
	return False

def isLoopComplexIntersectingInsideXSegment( loop, segmentFirstX, segmentSecondX, segmentYMirror, y ):
	"Determine if the loop is intersecting inside the x segment."
	rotatedLoop = getPointComplexesRoundZAxisByComplex( segmentYMirror, loop )
	for pointIndex in range( len( rotatedLoop ) ):
		pointFirst = rotatedLoop[ pointIndex ]
		pointSecond = rotatedLoop[ ( pointIndex + 1 ) % len( rotatedLoop ) ]
		if isLineComplexIntersectingInsideXSegment( segmentFirstX, segmentSecondX, pointFirst, pointSecond, y ):
			return True
	return False

def isLoopComplexLargeSameDirection( inset, loop, requiredSize ):
	"Determine if the inset is in the same direction as the loop and if the inset is as large as the required size."
	if isPolygonComplexWiddershins( inset ) != isPolygonComplexWiddershins( loop ):
		return False
	return getLoopComplexMaximumSpan( inset ) > requiredSize

def isLoopIntersectingInsideXSegment( loop, segmentFirstX, segmentSecondX, segmentYMirror, y ):
	"Determine if the loop is intersecting inside the x segment."
	rotatedLoop = getPathRoundZAxisByPlaneAngle( segmentYMirror, loop )
	for pointIndex in range( len( rotatedLoop ) ):
		pointFirst = rotatedLoop[ pointIndex ]
		pointSecond = rotatedLoop[ ( pointIndex + 1 ) % len( rotatedLoop ) ]
		if isLineIntersectingInsideXSegment( segmentFirstX, segmentSecondX, pointFirst, pointSecond, y ):
			return True
	return False

def isLoopIntersectingLoops( loop, otherLoops ):
	"Determine if the loop is intersecting other loops."
	for pointIndex in range( len( loop ) ):
		pointBegin = loop[ pointIndex ]
		pointEnd = loop[ ( pointIndex + 1 ) % len( loop ) ]
		if isLineIntersectingLoops( otherLoops, pointBegin, pointEnd ):
			return True
	return False

def isLoopIntersectingLoopComplexes( loop, otherLoops ):
	"Determine if the loop is intersecting other loops."
	for pointIndex in range( len( loop ) ):
		pointBegin = loop[ pointIndex ]
		pointEnd = loop[ ( pointIndex + 1 ) % len( loop ) ]
		if isLineIntersectingLoopComplexes( otherLoops, pointBegin, pointEnd ):
			return True
	return False

def isLoopListComplexIntersectingInsideXSegment( loopList, segmentFirstX, segmentSecondX, segmentYMirror, y ):
	"Determine if the loop list is crossing inside the x segment."
	for alreadyFilledLoop in loopList:
		if isLoopComplexIntersectingInsideXSegment( alreadyFilledLoop, segmentFirstX, segmentSecondX, segmentYMirror, y ):
			return True
	return False

def isLoopListIntersectingInsideXSegment( loopList, segmentFirstX, segmentSecondX, segmentYMirror, y ):
	"Determine if the loop list is crossing inside the x segment."
	for alreadyFilledLoop in loopList:
		if isLoopIntersectingInsideXSegment( alreadyFilledLoop, segmentFirstX, segmentSecondX, segmentYMirror, y ):
			return True
	return False

def isPathInsideLoop( loop, path ):
	"Determine if a path is inside another loop."
	leftPoint = getLeftPoint( path )
	return getNumberOfIntersectionsToLeft( leftPoint, loop ) % 2 == 1

def isPathInsideLoopComplex( loop, path ):
	"Determine if a path is inside another loop."
	leftPoint = getLeftPointComplex( path )
	return getNumberOfIntersectionsToLeftComplex( leftPoint, loop ) % 2 == 1

def isPathInsideLoops( loops, path ):
	"Determine if a path is inside another loop in a list."
	for loop in loops:
		if isPathInsideLoop( loop, path ):
			return True
	return False

def isPixelTableIntersecting( bigTable, littleTable, maskTable = {} ):
	"Add path to the pixel table."
	littleTableKeys = littleTable.keys()
	for littleTableKey in littleTableKeys:
		if littleTableKey not in maskTable:
			if littleTableKey in bigTable:
				return True
	return False

def isPolygonComplexWiddershins( polygonComplex ):
	"Determine if the complex polygon goes round in the widdershins direction."
	return getPolygonComplexArea( polygonComplex ) > 0.0

"""
#later see if this version of isPathInsideLoops should be used
def isPathInsideLoops( loops, path ):
	"Determine if a path is inside another loop in a list."
	for loop in loops:
		if not isPathInsideLoop( loop, path ):
			return False
	return True
"""

def isSegmentCompletelyInX( segment, xFirst, xSecond ):
	"Determine if the segment overlaps within x."
	segmentFirstX = segment[ 0 ].point.x
	segmentSecondX = segment[ 1 ].point.x
	if max( segmentFirstX, segmentSecondX ) > max( xFirst, xSecond ):
		return False
	return min( segmentFirstX, segmentSecondX ) >= min( xFirst, xSecond )

def isWiddershins( polygon ):
	"Determine if the polygon goes round in the widdershins direction."
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

def isWithinChannelComplex( channelRadius, pointIndex, loopComplex ):
	"Determine if the the point is within the channel between two adjacent points."
	pointComplex = loopComplex[ pointIndex ]
	behindSegmentComplex = loopComplex[ ( pointIndex + len( loopComplex ) - 1 ) % len( loopComplex ) ] - pointComplex
	behindSegmentComplexLength = abs( behindSegmentComplex )
	if behindSegmentComplexLength < channelRadius:
		return True
	aheadSegmentComplex = loopComplex[ ( pointIndex + 1 ) % len( loopComplex ) ] - pointComplex
	aheadSegmentComplexLength = abs( aheadSegmentComplex )
	if aheadSegmentComplexLength < channelRadius:
		return True
	behindSegmentComplex /= behindSegmentComplexLength
	aheadSegmentComplex /= aheadSegmentComplexLength
	absoluteZ = getComplexDotPlusOne( aheadSegmentComplex, behindSegmentComplex )
	if behindSegmentComplexLength * absoluteZ < channelRadius:
		return True
	if aheadSegmentComplexLength * absoluteZ < channelRadius:
		return True
	return False

def isXSegmentIntersectingPaths( paths, segmentFirstX, segmentSecondX, segmentYMirror, y ):
	"Determine if a path list is crossing inside the x segment."
	for path in paths:
		rotatedPath = getPathRoundZAxisByPlaneAngle( segmentYMirror, path )
		for pointIndex in range( len( rotatedPath ) - 1 ):
			pointFirst = rotatedPath[ pointIndex ]
			pointSecond = rotatedPath[ pointIndex + 1 ]
			if isLineIntersectingInsideXSegment( segmentFirstX, segmentSecondX, pointFirst, pointSecond, y ):
				return True
	return False

def removePixelTableFromPixelTable( pixelTableToBeRemoved, pixelTableToBeRemovedFrom ):
	"Remove pixel from the pixel table."
	pixelTableToBeRemovedKeys = pixelTableToBeRemoved.keys()
	for pixelTableToBeRemovedKey in pixelTableToBeRemovedKeys:
		if pixelTableToBeRemovedKey in pixelTableToBeRemovedFrom:
			del pixelTableToBeRemovedFrom[ pixelTableToBeRemovedKey ]

def toggleHashtable( hashtable, key, value ):
	"Toggle a hashtable between having and not having a key."
	if key in hashtable:
		del hashtable[ key ]
	else:
		hashtable[ key ] = value

def transferClosestFillLoop( extrusionHalfWidthSquared, oldOrderedLocation, remainingFillLoops, skein ):
	"Transfer the closest remaining fill loop."
	closestDistanceSquared = 999999999999999999.0
	closestFillLoop = None
	for remainingFillLoop in remainingFillLoops:
		distanceSquared = getNearestDistanceSquaredIndex( oldOrderedLocation, remainingFillLoop ).real
		if distanceSquared < closestDistanceSquared:
			closestDistanceSquared = distanceSquared
			closestFillLoop = remainingFillLoop
	remainingFillLoops.remove( closestFillLoop )
	addToThreadsFromLoop( extrusionHalfWidthSquared, '(<loop> )', closestFillLoop[ : ], oldOrderedLocation, skein )

def transferClosestPath( oldOrderedLocation, remainingPaths, skein ):
	"Transfer the closest remaining path."
	closestDistanceSquared = 999999999999999999.0
	closestPath = None
	for remainingPath in remainingPaths:
		distanceSquared = min( oldOrderedLocation.distance2( remainingPath[ 0 ] ), oldOrderedLocation.distance2( remainingPath[ - 1 ] ) )
		if distanceSquared < closestDistanceSquared:
			closestDistanceSquared = distanceSquared
			closestPath = remainingPath
	remainingPaths.remove( closestPath )
	skein.addGcodeFromThread( closestPath )
	oldOrderedLocation.setToVec3( closestPath[ - 1 ] )

def transferClosestPaths( oldOrderedLocation, remainingPaths, skein ):
	"Transfer the closest remaining paths."
	while len( remainingPaths ) > 0:
		transferClosestPath( oldOrderedLocation, remainingPaths, skein )

def transferPathsToSurroundingLoops( paths, surroundingLoops ):
	"Transfer paths to surrounding loops."
	for surroundingLoop in surroundingLoops:
		surroundingLoop.transferPaths( paths )


class Endpoint:
	"The endpoint of a segment."
	def __repr__( self ):
		"Get the string representation of this Endpoint."
		return 'Endpoint ' + str( self.point ) + ' ' + str( self.otherEndpoint.point )

	def getFromOtherPoint( self, otherEndpoint, point ):
		"Initialize from other endpoint."
		self.otherEndpoint = otherEndpoint
		self.point = point
		return self

	def getHop( self, fillInset, path ):
		"Get a hop away from the endpoint if the other endpoint is doubling back."
		if len( path ) < 2:
			return None
		pointComplex = self.point.dropAxis( 2 )
		penultimateMinusPoint = path[ - 2 ].dropAxis( 2 ) - pointComplex
		if abs( penultimateMinusPoint ) == 0.0:
			return None
		penultimateMinusPoint /= abs( penultimateMinusPoint )
		normalizedComplexSegment = self.otherEndpoint.point.dropAxis( 2 ) - pointComplex
		normalizedComplexSegmentLength = abs( normalizedComplexSegment )
		if normalizedComplexSegmentLength == 0.0:
			return None
		normalizedComplexSegment /= normalizedComplexSegmentLength
		if getComplexDot( penultimateMinusPoint, normalizedComplexSegment ) < 0.9:
			return None
		alongRatio = 0.8
		hop = self.point.times( alongRatio ).plus( self.otherEndpoint.point.times( 1.0 - alongRatio ) )
		normalizedSegment = self.otherEndpoint.point.minus( self.point )
		normalizedSegmentLength = normalizedSegment.length()
		absoluteCross = abs( getComplexCrossProduct( penultimateMinusPoint, normalizedComplexSegment ) )
		reciprocalCross = 1.0 / max( absoluteCross, 0.01 )
		alongWay = min( fillInset * reciprocalCross, normalizedSegmentLength )
		return self.point.plus( normalizedSegment.times( alongWay / normalizedSegmentLength ) )

	def getNearestEndpoint( self, endpoints ):
		"Get nearest endpoint."
		smallestDistanceSquared = 999999999999999999.0
		nearestEndpoint = None
		for endpoint in endpoints:
			distanceSquared = self.point.distance2( endpoint.point )
			if distanceSquared < smallestDistanceSquared:
				smallestDistanceSquared = distanceSquared
				nearestEndpoint = endpoint
		return nearestEndpoint

	def getNearestMiss( self, endpoints, path, pixelTable, width ):
		"Get the nearest endpoint which the segment to that endpoint misses the other extrusions."
		smallestDistance = 9999999999.0
		nearestMiss = None
		penultimateMinusPoint = complex( 0.0, 0.0 )
		pointComplex = self.point.dropAxis( 2 )
		if len( path ) > 1:
			penultimateMinusPoint = path[ - 2 ].dropAxis( 2 ) - pointComplex
			if abs( penultimateMinusPoint ) > 0.0:
				penultimateMinusPoint /= abs( penultimateMinusPoint )
		for endpoint in endpoints:
			endpointPointComplex = endpoint.point.dropAxis( 2 )
			normalizedSegment = endpointPointComplex - pointComplex
			normalizedSegmentLength = abs( normalizedSegment )
			if normalizedSegmentLength > 0.0:
				if normalizedSegmentLength < smallestDistance:
					normalizedSegment /= normalizedSegmentLength
					if getComplexDot( penultimateMinusPoint, normalizedSegment ) < 0.9:
						segmentTable = {}
						addSegmentToPixelTable( endpointPointComplex, pointComplex, segmentTable, 2, 2, width )
						if not isPixelTableIntersecting( pixelTable, segmentTable ):
							smallestDistance = normalizedSegmentLength
							nearestMiss = endpoint
			else:
				print( 'This should never happen, the endpoints are touching' )
				print( endpoint )
				print( path )
		return nearestMiss


class EndpointComplex:
	"The endpoint of a segment."
	def __repr__( self ):
		"Get the string representation of this Endpoint."
		return 'Endpoint %s, %s' % ( self.point, self.otherEndpoint.point )

	def getFromOtherPoint( self, otherEndpoint, point ):
		"Initialize from other endpoint."
		self.otherEndpoint = otherEndpoint
		self.point = point
		return self

	def getHop( self, fillInset, path ):
		"Get a hop away from the endpoint if the other endpoint is doubling back."
		if len( path ) < 2:
			return None
		penultimateMinusPoint = path[ - 2 ] - self.point
		if abs( penultimateMinusPoint ) == 0.0:
			return None
		penultimateMinusPoint /= abs( penultimateMinusPoint )
		normalizedComplexSegment = self.otherEndpoint.point - self.point
		normalizedComplexSegmentLength = abs( normalizedComplexSegment )
		if normalizedComplexSegmentLength == 0.0:
			return None
		normalizedComplexSegment /= normalizedComplexSegmentLength
		if getComplexDot( penultimateMinusPoint, normalizedComplexSegment ) < 0.9:
			return None
		alongRatio = 0.8
		hop = self.point * alongRatio + self.otherEndpoint.point * ( 1.0 - alongRatio )
		normalizedSegment = self.otherEndpoint.point - self.point
		normalizedSegmentLength = normalizedSegment.length()
		absoluteCross = abs( getComplexCrossProduct( penultimateMinusPoint, normalizedComplexSegment ) )
		reciprocalCross = 1.0 / max( absoluteCross, 0.01 )
		alongWay = min( fillInset * reciprocalCross, normalizedSegmentLength )
		return self.point + normalizedSegment * alongWay / normalizedSegmentLength

	def getNearestEndpoint( self, endpoints ):
		"Get nearest endpoint."
		smallestDistance = 999999999999999999.0
		nearestEndpoint = None
		for endpoint in endpoints:
			distance = abs( self.point - endpoint.point )
			if distance < smallestDistance:
				smallestDistance = distance
				nearestEndpoint = endpoint
		return nearestEndpoint

	def getNearestMiss( self, endpoints, path, pixelTable, width ):
		"Get the nearest endpoint which the segment to that endpoint misses the other extrusions."
		smallestDistance = 9999999999.0
		nearestMiss = None
		penultimateMinusPoint = complex( 0.0, 0.0 )
		if len( path ) > 1:
			penultimateMinusPoint = path[ - 2 ] - self.point
			if abs( penultimateMinusPoint ) > 0.0:
				penultimateMinusPoint /= abs( penultimateMinusPoint )
		for endpoint in endpoints:
			normalizedSegment = endpoint.point - self.point
			normalizedSegmentLength = abs( normalizedSegment )
			if normalizedSegmentLength > 0.0:
				if normalizedSegmentLength < smallestDistance:
					normalizedSegment /= normalizedSegmentLength
					if getComplexDot( penultimateMinusPoint, normalizedSegment ) < 0.9:
						segmentTable = {}
						addSegmentToPixelTable( endpoint.point, self.point, segmentTable, 2, 2, width )
						if not isPixelTableIntersecting( pixelTable, segmentTable ):
							smallestDistance = normalizedSegmentLength
							nearestMiss = endpoint
			else:
				print( 'This should never happen, the endpoints are touching' )
				print( endpoint )
				print( path )
		return nearestMiss


class PathZ:
	"Complex path with a z."
	def __init__( self, path, z ):
		self.path = path
		self.z = z

	def __repr__( self ):
		"Get the string representation of this flat path."
		return '%s, %s' % ( self.path, self.z )

	def getPath( self ):
		"Get the Vec3 path."
		return getPointsFromPointComplexesZ( self.path, self.z )


class SurroundingLoop:
	"A loop that surrounds paths."
	def __init__( self ):
		self.boundary = []
		self.extraLoops = []
		self.innerSurroundings = None
		self.lastFillLoops = None
		self.loop = None
		self.paths = []
		self.perimeterPaths = []

	def __repr__( self ):
		"Get the string representation of this surrounding loop."
		return '%s, %s, %s, %s' % ( self.boundary, self.innerSurroundings, self.paths, self.perimeterPaths )

	def addToThreads( self, oldOrderedLocation, skein ):
		"Add to paths from the last location."
		addSurroundingLoopBeginning( self.boundary, skein )
		if self.loop == None:
			transferClosestPaths( oldOrderedLocation, self.perimeterPaths[ : ], skein )
		else:
			addToThreadsFromLoop( self.extrusionHalfWidthSquared, '(<perimeter> )', self.loop[ : ], oldOrderedLocation, skein )#later when comb is updated replace perimeter with loop
		skein.addLine( '(</surroundingLoop> )' )
		addToThreadsRemoveFromSurroundings( oldOrderedLocation, self.innerSurroundings[ : ], skein )
		if len( self.extraLoops ) > 0:
			remainingFillLoops = self.extraLoops[ : ]
			while len( remainingFillLoops ) > 0:
				transferClosestFillLoop( self.extrusionHalfWidthSquared, oldOrderedLocation, remainingFillLoops, skein )
		transferClosestPaths( oldOrderedLocation, self.paths[ : ], skein )

	def getFillLoops( self ):
		"Get last fill loops from the outside loop and the loops inside the inside loops."
		fillLoops = self.getLoopsToBeFilled()[ : ]
		for surroundingLoop in self.innerSurroundings:
			fillLoops += getFillOfSurroundings( surroundingLoop.innerSurroundings )
		return fillLoops

	def getFromInsideSurroundings( self, extrusionWidth, inputSurroundingInsides ):
		"Initialize from inside surrounding loops."
		self.extrusionHalfWidthSquared = 0.25 * extrusionWidth * extrusionWidth
		self.extrusionWidth = extrusionWidth
		transferredSurroundings = getTransferredSurroundingLoops( inputSurroundingInsides, self.boundary )
		self.innerSurroundings = getOrderedSurroundingLoops( extrusionWidth, transferredSurroundings )
		return self

	def getLoopsToBeFilled( self ):
		"Get last fill loops from the outside loop and the loops inside the inside loops."
		if self.lastFillLoops != None:
			return self.lastFillLoops
		loopsToBeFilled = [ self.boundary ]
		for surroundingLoop in self.innerSurroundings:
			loopsToBeFilled.append( surroundingLoop.boundary )
		return loopsToBeFilled

	def transferPaths( self, paths ):
		"Transfer paths."
		for surroundingLoop in self.innerSurroundings:
			transferPathsToSurroundingLoops( paths, surroundingLoop.innerSurroundings )
		self.paths = getTransferredPaths( paths, self.boundary )


class XIntersectionIndex:
	"A class to hold the x intersection position and the index of the loop which intersected."
	def __init__( self, index, x ):
		self.index = index
		self.x = x

	def __cmp__( self, other ):
		"Get comparison in order to sort x intersections in ascending order of x."
		if self.x > other.x:
			return 1
		if self.x < other.x:
			return - 1
		return 0

	def __repr__( self ):
		"Get the string representation of this x intersection."
		return '%s, %s' % ( self.index, self.x )

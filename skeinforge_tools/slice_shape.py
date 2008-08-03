"""
Slice shape is a script to slice a GNU Triangulated Surface file.

Slice slices a GNU Triangulated Surface file into gcode extrusion layers.  The 'Extrusion Diameter' is the diameter of the extrusion at the
default extruder speed, this is the most important slice preference.  The 'Extrusion Density' is the density of the extruded shape over the
density of the filament.  The 'Extrusion Width Over Thickness' ratio is the ratio of the extrusion width over the layer thickness.  A ratio of
one means the extrusion is a circle, a typical ratio of 1.5 means the extrusion is a wide oval.

Rarely changed preferences are Import Coarseness, Mesh Type, Infill Bridge Width Over Thickness & Infill in Direction
of Bridges.  When the triangle mesh has holes in it, slice switches over to a slow algorithm that spans gaps in the mesh.  The higher the
import coarseness, the wider the gaps in the mesh it will span.  An import coarseness of one means it will span gaps the width of the
extrusion.  When the Mesh Type preference is correct, the mesh will be accurately sliced, and if a hole is found, slice will switch over to
the algorithm that spans gaps.  If the Mesh Type preference is Unproven, slice will use the gap spanning algorithm from the start.  The
problem with the gap spanning algothm is that it will span gaps, even if there actually is a gap in the model.  Infill bridge width
over thickness ratio is the ratio of the extrusion width over the layer thickness on a bridge layer.  If the infill in direction of bridges
preference is chosen, the infill will be in the direction of bridges across gaps, so that the fill will be able to span a bridge easier.  To run
slice, in a shell type:
> python slice.py

The following examples slice the GNU Triangulated Surface file Hollow Square.gts.  The examples are run in a terminal in the folder which
contains Hollow Square.gts and slice.py.  The preferences can be set in the dialog or by changing the preferences file 'slice.csv' with a text editor
or a spreadsheet program set to separate tabs.


> python slice.py
This brings up the dialog, after clicking 'Slice', the following is printed:
File Hollow Square.gcode is being sliced.
The sliced file is saved as Hollow Square_slice.gcode


>python
Python 2.5.1 (r251:54863, Sep 22 2007, 01:43:31)
[GCC 4.2.1 (SUSE Linux)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import slice
>>> slice.main()
File Hollow Square.gts is being sliced.
The sliced file is saved as Hollow Square_slice.gcode
It took 3 seconds to slice the file.


>>> slice.writeOutput()
File Hollow Square.gcode is being sliced.
The sliced file is saved as Hollow Square_slice.gcode
It took 3 seconds to slice the file.


>>> slice.getSliceGcode("
54 162 108 Number of Vertices,Number of Edges,Number of Faces
-5.800000000000001 5.341893939393939 4.017841892579603 Vertex Coordinates XYZ
5.800000000000001 5.341893939393939 4.017841892579603
..
many lines of GNU Triangulated Surface vertices, edges and faces
..
")

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
from skeinforge_tools.skeinforge_utilities import gcodec
from skeinforge_tools.skeinforge_utilities import intercircle
from skeinforge_tools.skeinforge_utilities import preferences
from skeinforge_tools.skeinforge_utilities import triangle_mesh
from skeinforge_tools import analyze
from skeinforge_tools import polyfile
import cmath
import cStringIO
import math
import os
import time


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/02/05 $"
__license__ = "GPL 3.0"


def addAlreadyFilledArounds( alreadyFilledArounds, loop, radius ):
	"Add already filled loops around loop to alreadyFilledArounds."
	alreadyFilledLoop = []
	slightlyGreaterThanRadius = 1.01 * radius
	muchGreaterThanRadius = 2.5 * radius
	alreadyFilledArounds.append( alreadyFilledLoop )
	circleNodes = intercircle.getCircleNodesFromLoop( loop, slightlyGreaterThanRadius )
	centers = intercircle.getCentersFromCircleNodes( circleNodes )
	for center in centers:
		alreadyFilledInset = intercircle.getInsetFromClockwiseLoop( center, radius )
		if euclidean.getMaximumSpan( alreadyFilledInset ) > muchGreaterThanRadius or euclidean.isWiddershins( alreadyFilledInset ):
			alreadyFilledLoop.append( alreadyFilledInset )

def addEdgePair( edgePairTable, edges, faceEdgeIndex, remainingEdgeIndex, remainingEdgeTable ):
	"Add edge pair to the edge pair table."
	if faceEdgeIndex == remainingEdgeIndex:
		return
	if not faceEdgeIndex in remainingEdgeTable:
		return
	edgePair = EdgePair().getFromIndexesEdges( [ remainingEdgeIndex, faceEdgeIndex ], edges )
	edgePairTable[ str( edgePair ) ] = edgePair

def addPointsAtZ( edgePair, points, radius, vertices, z ):
	"Add points on the segment between the edge intersections with z."
	sliceIntersectionFirst = getSliceIntersectionFromEdge( edgePair.edges[ 0 ], vertices, z )
	sliceIntersectionSecond = getSliceIntersectionFromEdge( edgePair.edges[ 1 ], vertices, z )
	intercircle.addPointsFromSegment( points, radius, sliceIntersectionFirst, sliceIntersectionSecond )

def getCommonVertexIndex( edgeFirst, edgeSecond ):
	"Get the vertex index that both edges have in common."
	for edgeFirstVertexIndex in edgeFirst.vertexIndexes:
		if edgeFirstVertexIndex == edgeSecond.vertexIndexes[ 0 ] or edgeFirstVertexIndex == edgeSecond.vertexIndexes[ 1 ]:
			return edgeFirstVertexIndex
	print( "Inconsistent GNU Triangulated Surface" )
	print( edgeFirst )
	print( edgeSecond )
	return 0

def getDoubledRoundZ( overhangingSegment, segmentRoundZ ):
	"Get doubled plane angle around z of the overhanging segment."
	endpoint = overhangingSegment[ 0 ]
	roundZ = endpoint.point.dropAxis( 2 ) - endpoint.otherEndpoint.point.dropAxis( 2 )
	roundZ *= segmentRoundZ
	if abs( roundZ ) == 0.0:
		return complex()
	if roundZ.real < 0.0:
		roundZ *= - 1.0
	roundZLength = abs( roundZ )
	return roundZ * roundZ / roundZLength

def getLoopsFromCorrectMesh( edges, faces, vertices, z ):
	"Get loops from a slice of a correct mesh."
	remainingEdgeTable = getRemainingEdgeTable( edges, vertices, z )
	remainingValues = remainingEdgeTable.values()
	for edge in remainingValues:
		if len( edge.faceIndexes ) < 2:
			print( 'This should never happen, there is a hole in the triangle mesh, each edge should have two faces.' )
			print( edge )
			print( "Something will still be printed, but there is no guarantee that it will be the correct shape." )
			print( 'Once the gcode is saved, you should check over the layer with a z of:' )
			print( z )
			return None
	loops = []
	pathIndexes = getPathIndexesAddPath( edges, faces, loops, remainingEdgeTable, vertices, z )
	while pathIndexes != None:
		pathIndexes = getPathIndexesAddPath( edges, faces, loops, remainingEdgeTable, vertices, z )
	boundingLoops = []
	for loop in loops:
		boundingLoop = intercircle.BoundingLoop().getFromLoop( loop )
		boundingLoop.area = abs( euclidean.getPolygonArea( loop ) )
		boundingLoops.append( boundingLoop )
	boundingLoops.sort()
	sortedLoops = []
	for boundingLoop in boundingLoops:
		sortedLoops.append( boundingLoop.loop )
	return sortedLoops
#	untouchables = []
#	for boundingLoop in boundingLoops:
#		if not boundingLoop.isIntersectingList( untouchables ):
#			untouchables.append( boundingLoop )
#	if len( untouchables ) < len( boundingLoops ):
#		print( 'This should never happen, the slice layer intersects itself. Something will still be printed, but there is no guarantee that it will be the correct shape.' )
#		print( 'Once the gcode is saved, you should check over the layer with a z of:' )
#		print( z )
#	remainingLoops = []
#	for untouchable in untouchables:
#		remainingLoops.append( untouchable.loop )
#	return remainingLoops

def getLoopsFromUnprovenMesh( edges, extrusionWidth, faces, vertices, slicePreferences, z ):
	"Get loops from a slice of an unproven mesh."
	edgePairTable = {}
	importRadius = slicePreferences.importCoarseness.value * extrusionWidth
	points = []
	remainingEdgeTable = getRemainingEdgeTable( edges, vertices, z )
	remainingEdgeTableKeys = remainingEdgeTable.keys()
	for remainingEdgeIndexKey in remainingEdgeTable:
		edge = remainingEdgeTable[ remainingEdgeIndexKey ]
		sliceIntersection = getSliceIntersectionFromEdge( edge, vertices, z )
		points.append( sliceIntersection )
		for edgeFaceIndex in edge.faceIndexes:
			face = faces[ edgeFaceIndex ]
			for edgeIndex in face.edgeIndexes:
				addEdgePair( edgePairTable, edges, edgeIndex, remainingEdgeIndexKey, remainingEdgeTable )
	for edgePairValue in edgePairTable.values():
		addPointsAtZ( edgePairValue, points, importRadius, vertices, z )
	path = euclidean.getAwayPath( points, importRadius )
	circleNodes = intercircle.getCircleNodesFromPath( path, importRadius )
	centers = intercircle.getCentersFromCircleNodes( circleNodes )
	return intercircle.getLoopsFromLoopsDirection( True, centers )

def getLowestZoneIndex( zoneArray, z ):
	"Get the lowest zone index."
	lowestZoneIndex = 0
	lowestZone = 99999999.0
	for zoneIndex in range( len( zoneArray ) ):
		zone = zoneArray[ zoneIndex ]
		if zone < lowestZone:
			lowestZone = zone
			lowestZoneIndex = zoneIndex
	return lowestZoneIndex

def getNextEdgeIndexAroundZ( edge, faces, remainingEdgeTable ):
	"Get the next edge index in the mesh slice."
	for faceIndex in edge.faceIndexes:
		face = faces[ faceIndex ]
		for edgeIndex in face.edgeIndexes:
			if edgeIndex in remainingEdgeTable:
				return edgeIndex
	return - 1

def getOverhangDirection( belowOutsetLoops, segmentBegin, segmentEnd ):
	"Add to span direction from the endpoint segments which overhang the layer below."
	segment = segmentEnd.minus( segmentBegin )
	normalizedSegment = complex( segment.x, segment.y )
	normalizedSegment /= abs( normalizedSegment )
	segmentYMirror = complex( normalizedSegment.real, - normalizedSegment.imag )
	segmentBegin = euclidean.getRoundZAxisByPlaneAngle( segmentYMirror, segmentBegin )
	segmentEnd = euclidean.getRoundZAxisByPlaneAngle( segmentYMirror, segmentEnd )
	solidXIntersectionList = []
	y = segmentBegin.y
	solidXIntersectionList.append( euclidean.XIntersection().getFromIndexX( - 1.0, segmentBegin.x ) )
	solidXIntersectionList.append( euclidean.XIntersection().getFromIndexX( - 1.0, segmentEnd.x ) )
	for belowLoopIndex in range( len( belowOutsetLoops ) ):
		belowLoop = belowOutsetLoops[ belowLoopIndex ]
		rotatedOutset = euclidean.getPathRoundZAxisByPlaneAngle( segmentYMirror, belowLoop )
		euclidean.addXIntersections( rotatedOutset, belowLoopIndex, solidXIntersectionList, y )
	overhangingSegments = euclidean.getSegmentsFromIntersections( solidXIntersectionList, y, segmentBegin.z )
	overhangDirection = complex()
	for overhangingSegment in overhangingSegments:
		overhangDirection += getDoubledRoundZ( overhangingSegment, normalizedSegment )
	return overhangDirection

def getPath( edges, pathIndexes, loop, z ):
	"Get the path from the edge intersections."
	path = []
	for pathIndexIndex in range( len( pathIndexes ) ):
		pathIndex = pathIndexes[ pathIndexIndex ]
		edge = edges[ pathIndex ]
		pathPoint = getSliceIntersectionFromEdge( edge, loop, z )
		path.append( pathPoint )
	return path

def getPathIndexesAddPath( edges, faces, loops, remainingEdgeTable, vertices, z ):
	"Get the path indexes around a triangle mesh slice and add the path to the loops."
	if len( remainingEdgeTable ) < 1:
		return None
	pathIndexes = []
	remainingEdgeIndexKey = remainingEdgeTable.keys()[ 0 ]
	pathIndexes.append( remainingEdgeIndexKey )
	del remainingEdgeTable[ remainingEdgeIndexKey ]
	nextEdgeIndexAroundZ = getNextEdgeIndexAroundZ( edges[ remainingEdgeIndexKey ], faces, remainingEdgeTable )
	while nextEdgeIndexAroundZ != - 1:
		pathIndexes.append( nextEdgeIndexAroundZ )
		del remainingEdgeTable[ nextEdgeIndexAroundZ ]
		nextEdgeIndexAroundZ = getNextEdgeIndexAroundZ( edges[ nextEdgeIndexAroundZ ], faces, remainingEdgeTable )
	if len( pathIndexes ) < 3:
		print( "Dangling edges, will use intersecting circles to get import layer at height " + z.toString() )
		del loops[ : ]
		return None
	loops.append( getPath( edges, pathIndexes, vertices, z ) )
	return pathIndexes

def getRemainingEdgeTable( edges, vertices, z ):
	"Get the remaining edge hashtable."
	remainingEdgeTable = {}
	for edgeIndex in range( len( edges ) ):
		edge = edges[ edgeIndex ]
		if isZInEdge( edge, vertices, z ):
			remainingEdgeTable[ edgeIndex ] = edge
	return remainingEdgeTable

def getSegmentsFromPoints( loopLists, pointBegin, pointEnd ):
	"Get enpoint segments from the beginning and end of a line segment."
	normalizedSegment = pointEnd.dropAxis( 2 ) - pointBegin.dropAxis( 2 )
	normalizedSegmentLength = abs( normalizedSegment )
	if normalizedSegmentLength == 0.0:
		return
	normalizedSegment /= normalizedSegmentLength
	segmentYMirror = complex( normalizedSegment.real, - normalizedSegment.imag )
	pointBeginRotated = euclidean.getRoundZAxisByPlaneAngle( segmentYMirror, pointBegin )
	pointEndRotated = euclidean.getRoundZAxisByPlaneAngle( segmentYMirror, pointEnd )
	rotatedLoopLists = []
	for loopList in loopLists:
		rotatedLoopList = []
		rotatedLoopLists.append( rotatedLoopList )
		for loop in loopList:
			rotatedLoop = euclidean.getPathRoundZAxisByPlaneAngle( segmentYMirror, loop )
			rotatedLoopList.append( rotatedLoop )
	xIntersectionList = []
	xIntersectionList.append( euclidean.XIntersection().getFromIndexX( - 1, pointBeginRotated.x ) )
	xIntersectionList.append( euclidean.XIntersection().getFromIndexX( - 1, pointEndRotated.x ) )
	euclidean.addXIntersectionsFromLoopLists( rotatedLoopLists, xIntersectionList, pointBeginRotated.y )
	segments = euclidean.getSegmentsFromIntersections( xIntersectionList, pointBeginRotated.y, pointBegin.z )
	for segment in segments:
		endpointBegin = segment[ 0 ]
		endpointBegin.point = euclidean.getRoundZAxisByPlaneAngle( normalizedSegment, endpointBegin.point )
		endpointEnd = segment[ 1 ]
		endpointEnd.point = euclidean.getRoundZAxisByPlaneAngle( normalizedSegment, endpointEnd.point )
	return segments

def getSharedFace( firstEdge, faces, secondEdge ):
	"Get the face which is shared by two edges."
	for firstEdgeFaceIndex in firstEdge.faceIndexes:
		for secondEdgeFaceIndex in secondEdge.faceIndexes:
			if firstEdgeFaceIndex == secondEdgeFaceIndex:
				return faces[ firstEdgeFaceIndex ]
	return None

def getSliceGcode( gnuTriangulatedSurfaceText, slicePreferences = None ):
	"Slice a GNU Triangulated Surface text."
	if gnuTriangulatedSurfaceText == '':
		return ''
	if slicePreferences == None:
		slicePreferences = SlicePreferences()
		preferences.readPreferences( slicePreferences )
	skein = SliceSkein()
	skein.parseGnuTriangulatedSurface( gnuTriangulatedSurfaceText, slicePreferences )
	return skein.output.getvalue()

def getSliceIntersectionFromEdge( edge, loop, z ):
	"Get the point where the slice intersects the edge."
	firstVertex = loop[ edge.vertexIndexes[ 0 ] ]
	secondVertex = loop[ edge.vertexIndexes[ 1 ] ]
	zMinusFirst = z - firstVertex.z
	up = secondVertex.z - firstVertex.z
	sliceIntersection = secondVertex.minus( firstVertex )
	sliceIntersection.scale( zMinusFirst / up )
	sliceIntersection.add( firstVertex )
	return sliceIntersection

def isCloseToLast( paths, point, radius ):
	"Determine if the point is close to the last point of the last path."
	if len( paths ) < 1:
		return False
	lastPath = paths[ - 1 ]
	return lastPath[ - 1 ].distance( point ) < radius

def isIntersectingWithinList( loop, loopList ):
	"Determine if the loop is intersecting or is within the loop list."
	if euclidean.isLoopIntersectingLoops( loop, loopList ):
		return True
	totalNumberOfIntersections = 0
	for otherLoop in loopList:
		leftPoint = euclidean.getLeftPoint( otherLoop )
		totalNumberOfIntersections += euclidean.getNumberOfIntersectionsToLeft( leftPoint, loop )
	return totalNumberOfIntersections % 2 == 1

def isIntersectingWithinLists( loop, loopLists ):
	"Determine if the loop is intersecting or is within the loop lists."
	for loopList in loopLists:
		if isIntersectingWithinList( loop, loopList ):
			return True
	return False

def isZInEdge( edge, vertices, z ):
	"Determine if z is inside the edge."
	vertex1ZHigher = vertices[ edge.vertexIndexes[ 0 ] ].z > z
	vertex2ZHigher = vertices[ edge.vertexIndexes[ 1 ] ].z > z
	return vertex1ZHigher != vertex2ZHigher

def writeOutput( filename = '' ):
	"Slice a GNU Triangulated Surface file.  If no filename is specified, slice the first GNU Triangulated Surface file in this folder."
	if filename == '':
		unmodified = gcodec.getGNUTriangulatedSurfaceFiles()
		if len( unmodified ) == 0:
			print( "There are no GNU Triangulated Surface files in this folder." )
			return
		filename = unmodified[ 0 ]
	startTime = time.time()
	slicePreferences = SlicePreferences()
	preferences.readPreferences( slicePreferences )
	print( 'File ' + gcodec.getSummarizedFilename( filename ) + ' is being sliced.' )
	gnuTriangulatedSurfaceText = gcodec.getFileText( filename )
	if gnuTriangulatedSurfaceText == '':
		return
	suffixFilename = filename[ : filename.rfind( '.' ) ] + '_slice.gcode'
	sliceGcode = getSliceGcode( gnuTriangulatedSurfaceText, slicePreferences )
	gcodec.writeFileText( suffixFilename, sliceGcode )
	print( 'The sliced file is saved as ' + gcodec.getSummarizedFilename( suffixFilename ) )
	analyze.writeOutput( suffixFilename, sliceGcode )
	print( 'It took ' + str( int( round( time.time() - startTime ) ) ) + ' seconds to slice the file.' )


class SliceSkein:
	"A class to slice a GNU Triangulated Surface."
	def __init__( self ):
		self.belowLoops = None
		self.output = cStringIO.StringIO()

	def addFromFile( self, filename ):
		"Add lines of text from the filename."
		fileLines = gcodec.getTextLines( gcodec.getFileText( filename ) )
		for line in fileLines:
			self.addLine( line )

	def addFromUpperLowerFile( self, filename ):
		"Add lines of text from the filename or the lowercase filename, if there is no file by the original filename in the directory."
		directory = os.listdir( os.getcwd() )
		if filename in directory:
			self.addFromFile( filename )
			return
		filename = filename.lower()
		if filename in directory:
			self.addFromFile( filename )

	def addGcodeFromPerimeterPaths( self, loop, loopLists, radius ):
		"Add the perimeter paths to the output."
		segments = []
		for pointIndex in range( len( loop ) ):
			pointBegin = loop[ pointIndex ]
			pointEnd = loop[ ( pointIndex + 1 ) % len( loop ) ]
			segments += getSegmentsFromPoints( loopLists, pointBegin, pointEnd )
		perimeterPaths = []
		path = []
		muchSmallerThanRadius = 0.1 * radius
		for segment in segments:
			pointBegin = segment[ 0 ].point
			if not isCloseToLast( perimeterPaths, pointBegin, muchSmallerThanRadius ):
				path = [ pointBegin ]
				perimeterPaths.append( path )
			path.append( segment[ 1 ].point )
		if len( perimeterPaths ) > 1:
			firstPath = perimeterPaths[ 0 ]
			lastPath = perimeterPaths[ - 1 ]
			if lastPath[ - 1 ].distance( firstPath[ 0 ] ) < 0.1 * muchSmallerThanRadius:
				connectedBeginning = lastPath[ : - 1 ] + firstPath
				perimeterPaths[ 0 ] = connectedBeginning
				perimeterPaths.remove( lastPath )
		for perimeterPath in perimeterPaths:
			self.addGcodeFromThread( perimeterPath )

	def addGcodeFromRemainingLoop( self, loop, loopLists, radius ):
		"Add the remainder of the loop which does not overlap the alreadyFilledArounds loops."
		euclidean.addSurroundingLoopBeginning( loop, self )
		if isIntersectingWithinLists( loop, loopLists ):
			self.addGcodeFromPerimeterPaths( loop, loopLists, radius )
		else:
			self.addLine( '(<perimeter> )' ) # Indicate that a perimeter is beginning.
			self.addGcodeFromThread( loop + [ loop[ 0 ] ] )
		self.addLine( '(</surroundingLoop> )' )

	def addGcodeFromThread( self, thread ):
		"Add a thread to the output."
		if len( thread ) > 0:
			self.addGcodeMovement( thread[ 0 ] )
		else:
			print( "zero length vertex positions array which was skipped over, this should never happen" )
		if len( thread ) < 2:
			return
		self.addLine( "M101" ) # Turn extruder on.
		for point in thread[ 1 : ]:
			self.addGcodeMovement( point )
		self.addLine( "M103" ) # Turn extruder off.

	def addGcodeMovement( self, point ):
		"Add a movement to the output."
		self.addLine( "G1 X%s Y%s Z%s" % ( self.getRounded( point.x ), self.getRounded( point.y ), self.getRounded( point.z ) ) )

	def addInitializationToOutput( self ):
		"Add initialization gcode to the output."
		# From http://www.ahha.com/VarsAndMacros.doc
		# If you wish to run macros using comments in parentheses, the comment character must be changed from a semi-colon to a left parenthesis.
		# Note: the original closing single quotation mark was not ascii, so I replaced it with an apostrophe.
		# To do this, the following line should be placed at the beginning of the G-Code file that calls the macro:
#		self.addLine( "(*CMST '('*)" ) # Gcode to convert the comment character to '('.
		self.addFromUpperLowerFile( 'Start.txt' ) # Add a start file if it exists.
		self.addLine( '(<creator> skeinforge May 28, 2008 )' ) # GCode formatted comment
		self.addLine( 'M110' ) # GCode for compatibility with Nophead's code.
		self.addLine( '(<extruderInitialization> )' ) # GCode formatted comment
		self.addLine( 'G21' ) # Set units to mm.
		self.addLine( 'G90' ) # Set positioning to absolute.
		self.addLine( 'G28' ) # Start at home.
		self.addLine( 'M103' ) # Turn extruder off.
		self.addLine( 'M105' ) # Custom code for temperature reading.
		self.addFromUpperLowerFile( 'EndOfTheBeginning.txt' ) # Add a second start file if it exists.
		self.addLine( '(<decimalPlacesCarried> ' + str( self.decimalPlacesCarried ) + ' )' ) # Set decimal places carried.
		self.addLine( '(<extrusionDiameter> ' + self.getRounded( self.extrusionDiameter ) + ' )' ) # Set extrusion diameter.
		self.addLine( '(<extrusionHeight> ' + self.getRounded( self.extrusionHeight ) + ' )' ) # Set layer thickness.
		self.addLine( '(<extrusionPerimeterWidth> ' + self.getRounded( self.extrusionPerimeterWidth ) + ' )' ) # Set extrusion perimeter width.
		self.addLine( '(<extrusionWidth> ' + self.getRounded( self.extrusionWidth ) + ' )' ) # Set extrusion width.
		self.addLine( '(<fillInset> ' + str( self.fillInset ) + ' )' ) # Set fill inset.
		# Set bridge extrusion width over solid extrusion width.
		self.addLine( '(<bridgeExtrusionWidthOverSolid> ' + euclidean.getRoundedToThreePlaces( self.bridgeExtrusionWidth / self.extrusionWidth ) + ' )' )
		self.addLine( '(<procedureDone> slice )' ) # The skein has been sliced.
		self.addLine( '(<extrusionStart> )' ) # Initialization is finished, extrusion is starting.
		circleArea = self.extrusionDiameter * self.extrusionDiameter * math.pi / 4.0
		print( 'The extrusion fill density ratio is ' + euclidean.getRoundedToThreePlaces( self.extrusionWidth * self.extrusionHeight / circleArea ) )

	def addLine( self, line ):
		"Add a line of text and a newline to the output."
		self.output.write( line + "\n" )

	def addShutdownToOutput( self ):
		"Add shutdown gcode to the output."
		self.addLine( '(<extruderShutDown> )' ) # GCode formatted comment
		self.addLine( 'M103' ) # Turn extruder motor off.
		self.addLine( 'M104 S0' ) # Turn extruder heater off.
#		self.addLine( 'M30' ) # End gcode program.
		self.addFromUpperLowerFile( 'End.txt' ) # Add an end file if it exists.

	def addToZoneArray( self, point, zoneArray, z ):
		"Add a height to the zone array."
		zoneLayer = int( round( ( point.z - z ) / self.zZoneInterval ) )
		zoneAround = 2 * int( abs( zoneLayer ) )
		if zoneLayer < 0:
			zoneAround -= 1
		if zoneAround < len( zoneArray ):
			zoneArray[ zoneAround ] += 1

	def getBridgeDirection( self, layerLoops ):
		"Get span direction for the majority of the overhanging extrusion perimeter, if any."
		if not self.slicePreferences.infillDirectionBridge.value:
			return None
		if self.belowLoops == None:
			return None
		belowOutsetLoops = []
		overhangInset = 1.25 * self.extrusionWidth
		greaterThanOverhang = 1.1 * overhangInset
		for loop in self.belowLoops:
			centers = intercircle.getCentersFromLoopDirection( True, loop, greaterThanOverhang )
			for center in centers:
				outset = intercircle.getInsetFromClockwiseLoop( center, overhangInset )
				if euclidean.isLargeSameDirection( outset, center, self.extrusionWidth ):
					belowOutsetLoops.append( outset )
		bridgeDirection = complex()
		for loop in layerLoops:
			for pointIndex in range( len( loop ) ):
				previousIndex = ( pointIndex + len( loop ) - 1 ) % len( loop )
				bridgeDirection += getOverhangDirection( belowOutsetLoops, loop[ previousIndex ], loop[ pointIndex ] )
		if abs( bridgeDirection ) < self.halfExtrusionPerimeterWidth:
			return None
		else:
			bridgeDirection /= abs( bridgeDirection )
			return cmath.sqrt( bridgeDirection )

	def getExtrudateLoops( self, halfWidth, loop ):
		"Get the inset extrudate loops from the loop."
		slightlyGreaterThanHalfWIdth = 1.1 * halfWidth
		muchGreaterThanHalfWIdth = 2.5 * halfWidth
		extrudateLoops = []
		circleNodes = intercircle.getCircleNodesFromLoop( loop, slightlyGreaterThanHalfWIdth )
		centers = intercircle.getCentersFromCircleNodes( circleNodes )
		for center in centers:
			extrudateLoop = intercircle.getInsetFromClockwiseLoop( center, halfWidth )
			if euclidean.isLargeSameDirection( extrudateLoop, center, muchGreaterThanHalfWIdth ):
				if euclidean.isPathInsideLoop( loop, extrudateLoop ) == euclidean.isWiddershins( loop ):
					extrudateLoops.append( extrudateLoop )
		return extrudateLoops

	def getLoopsFromMesh( self, z ):
		"Get loops from a slice of a mesh."
		loops = []
		originalLoops = []
		if self.slicePreferences.correct.value:
			originalLoops = getLoopsFromCorrectMesh( self.triangleMesh.edges, self.triangleMesh.faces, self.triangleMesh.vertices, z )
		if len( originalLoops ) < 1:
			originalLoops = getLoopsFromUnprovenMesh( self.triangleMesh.edges, self.extrusionWidth, self.triangleMesh.faces, self.triangleMesh.vertices, self.slicePreferences, z )
		for original in originalLoops:
			loops.append( euclidean.getSimplifiedLoop( original, self.extrusionWidth ) )
		for pathIndex in range( len( loops ) ):
			loop = loops[ pathIndex ]
			leftPoint = euclidean.getLeftPoint( loop )
			totalNumberOfIntersectionsToLeft = 0
			for otherLoop in loops[ : pathIndex ] + loops[ pathIndex + 1 : ]:
				totalNumberOfIntersectionsToLeft += euclidean.getNumberOfIntersectionsToLeft( leftPoint, otherLoop )
			loopIsWiddershins = euclidean.isWiddershins( loop )
			isEven = totalNumberOfIntersectionsToLeft % 2 == 0
			if isEven != loopIsWiddershins:
				loop.reverse()
		return loops

	def getRounded( self, number ):
		"Get number rounded to the number of carried decimal places as a string."
		return euclidean.getRoundedToDecimalPlaces( self.decimalPlacesCarried, number )

	def getZAddExtruderPaths( self, z ):
		"Get next z and add extruder loops."
		alreadyFilledArounds = []
		zoneArray = []
		for point in self.triangleMesh.vertices:
			self.addToZoneArray( point, zoneArray, z )
		lowestZoneIndex = getLowestZoneIndex( zoneArray, z )
		halfAround = int( math.ceil( float( lowestZoneIndex ) / 2.0 ) )
		zAround = float( halfAround ) * self.zZoneInterval
		if lowestZoneIndex % 2 == 1:
			zAround = - zAround
		loops = self.getLoopsFromMesh( z + zAround )
		centers = []
		extruderPaths = []
		halfWidth = self.halfExtrusionPerimeterWidth
		slightlyGreaterThanExtrusionWIdth = 1.1 * halfWidth
		muchGreaterThanExtrusionWidth = 2.5 * self.extrusionWidth
		allExtrudateLoops = []
		for loop in loops:
			allExtrudateLoops += self.getExtrudateLoops( halfWidth, loop )
		bridgeDirection = self.getBridgeDirection( allExtrudateLoops )
		self.addLine( '(<layerStart> ' + self.getRounded( z ) + ' )' ) # Indicate that a new layer is starting.
		halfBridgeMinusLayer = 0.0
		if bridgeDirection != None:
			halfWidth *= self.bridgeExtrusionWidth / self.extrusionWidth
			slightlyGreaterThanExtrusionWIdth *= self.bridgeExtrusionWidth / self.extrusionWidth
			self.addLine( '(<bridgeDirection> ' + str( bridgeDirection ) + ' )' ) # Indicate the bridge direction.
			halfBridgeMinusLayer = 0.5 * ( self.bridgeextrusionHeight - self.extrusionHeight )
		allExtrudateLoops = []
		for loop in loops:
			extrudateLoops = self.getExtrudateLoops( halfWidth, loop )
			for extrudateLoop in extrudateLoops:
				for point in extrudateLoop:
					point.z += halfBridgeMinusLayer
				allExtrudateLoops.append( extrudateLoop )
				self.addGcodeFromRemainingLoop( extrudateLoop, alreadyFilledArounds, halfWidth )
				addAlreadyFilledArounds( alreadyFilledArounds, extrudateLoop, self.fillInset )
		self.belowLoops = allExtrudateLoops
		if bridgeDirection == None:
			return z + self.extrusionHeight
		return z + self.bridgeextrusionHeight

	def parseGnuTriangulatedSurface( self, gnuTriangulatedSurfaceText, slicePreferences ):
		"Parse gnu triangulated surface text and store the sliced gcode."
		self.slicePreferences = slicePreferences
		self.triangleMesh = triangle_mesh.TriangleMesh().getFromGNUTriangulatedSurfaceText( gnuTriangulatedSurfaceText )
		self.extrusionDiameter = slicePreferences.extrusionDiameter.value
		self.decimalPlacesCarried = int( max( 0.0, math.ceil( 1.0 - math.log10( self.extrusionDiameter / slicePreferences.extrusionDiameterOverPrecision.value ) ) ) )
		self.bridgeExtrusionWidth = slicePreferences.infillBridgeWidthOverDiameter.value * self.extrusionDiameter
		self.extrusionHeight = slicePreferences.extrusionHeightOverDiameter.value * self.extrusionDiameter
		self.extrusionPerimeterWidth = slicePreferences.extrusionPerimeterWidthOverDiameter.value * self.extrusionDiameter
		self.extrusionWidth = slicePreferences.extrusionWidthOverDiameter.value * self.extrusionDiameter
		self.halfExtrusionPerimeterWidth = 0.5 * self.extrusionPerimeterWidth
		self.fillInset = self.halfExtrusionPerimeterWidth * ( 2.0 - slicePreferences.infillPerimeterOverlap.value )
		if slicePreferences.perimeterInfillPreference.value:
			self.fillInset = self.halfExtrusionPerimeterWidth + 0.5 * self.extrusionWidth * ( 1.0 - slicePreferences.infillPerimeterOverlap.value )
		self.bridgeextrusionHeight = self.extrusionHeight * slicePreferences.extrusionWidthOverDiameter.value / slicePreferences.infillBridgeWidthOverDiameter.value
		self.halfThickness = 0.5 * self.extrusionHeight
		self.zZoneLayers = 99
		self.zZoneInterval = self.extrusionHeight / self.zZoneLayers / 100.0
		self.bottom = 999999999.0
		self.top = - self.bottom
		for point in self.triangleMesh.vertices:
			self.bottom = min( self.bottom, point.z )
			self.top = max( self.top, point.z )
		self.layerBottom = self.bottom + self.halfThickness
		self.layerTop = self.top - self.halfThickness * 0.5
		self.addInitializationToOutput()
		z = self.layerBottom
		while z < self.layerTop:
			z = self.getZAddExtruderPaths( z )
		self.addShutdownToOutput()


#extrusionWidthOverDiameter
#extrusionHeightOverDiameter
#(<extrusionDiameter> 0.5 )
#(<extrusionWidth> 0.599 )
#(<fillInset> 0.449484698309 )
#(<extrusionHeight> 0.4 )
class SlicePreferences:
	"A class to handle the slice preferences."
	def __init__( self ):
		"Set the default preferences, execute title & preferences filename."
		#Set the default preferences.
		self.extrusionDiameter = preferences.FloatPreference().getFromValue( 'Extrusion Diameter (mm):', 0.6 )
		self.extrusionDiameterOverPrecision = preferences.FloatPreference().getFromValue( 'Extrusion Diameter Over Precision (ratio):', 10.0 )
		self.extrusionHeightOverDiameter = preferences.FloatPreference().getFromValue( 'Extrusion Height Over Diameter (ratio):', 0.67 )
		self.extrusionPerimeterWidthOverDiameter = preferences.FloatPreference().getFromValue( 'Extrusion Perimeter Width Over Diameter (ratio):', 1.2 )
		self.extrusionWidthOverDiameter = preferences.FloatPreference().getFromValue( 'Extrusion Width Over Diameter (ratio):', 1.0 )
		self.filenameInput = preferences.Filename().getFromFilename( [ ( 'GNU Triangulated Surface files', '*.gts' ) ], 'Open File to be Sliced', '' )
		self.importCoarseness = preferences.FloatPreference().getFromValue( 'Import Coarseness (ratio):', 1.0 )
		importRadio = []
		self.correct = preferences.RadioLabel().getFromRadioLabel( 'Correct Mesh', 'Mesh Type:', importRadio, True )
		self.unproven = preferences.Radio().getFromRadio( 'Unproven Mesh', importRadio,False  )
		self.infillBridgeWidthOverDiameter = preferences.FloatPreference().getFromValue( 'Infill Bridge Width Over Thickness (ratio):', 1.0 )
		self.infillDirectionBridge = preferences.BooleanPreference().getFromValue( 'Infill in Direction of Bridges', True )
		self.infillPerimeterOverlap = preferences.FloatPreference().getFromValue( 'Infill Perimeter Overlap (ratio):', 0.1 )
		infillRadio = []
		self.perimeterInfillPreference = preferences.RadioLabel().getFromRadioLabel( 'Calculate Overlap from Perimeter and Infill', 'Infill Perimeter Overlap Method of Calculation:', infillRadio, True )
		self.perimeterPreference = preferences.Radio().getFromRadio( 'Calculate Overlap from Perimeter Only', infillRadio, False )
		#Create the archive, title of the execute button, title of the dialog & preferences filename.
		self.archive = [
			self.extrusionDiameter,
			self.extrusionDiameterOverPrecision,
			self.extrusionPerimeterWidthOverDiameter,
			self.extrusionHeightOverDiameter,
			self.extrusionWidthOverDiameter,
			self.filenameInput,
			self.importCoarseness,
			self.correct,
			self.unproven,
			self.infillBridgeWidthOverDiameter,
			self.infillDirectionBridge,
			self.infillPerimeterOverlap,
			self.perimeterInfillPreference,
			self.perimeterPreference ]
		self.executeTitle = 'Slice'
		self.filenamePreferences = preferences.getPreferencesFilePath( 'slice.csv' )
		self.filenameHelp = 'skeinforge_tools.slice.html'
		self.saveTitle = 'Save Preferences'
		self.title = 'Slice Preferences'

	def execute( self ):
		"Slice button has been clicked."
		filenames = polyfile.getFileOrGNUUnmodifiedGcodeDirectory( self.filenameInput.value, self.filenameInput.wasCancelled )
		for filename in filenames:
			writeOutput( filename )


def main( hashtable = None ):
	"Display the slice dialog."
	preferences.displayDialog( SlicePreferences() )

if __name__ == "__main__":
	main()
"""
Slice is a script to slice a GNU Triangulated Surface file.  Slice is the first script of the skeinforge tool chain.

To run slice, install python 2.x on your machine, which is avaliable from http://www.python.org/download/

To use the preferences dialog you'll also need Tkinter, which probably came with the python installation.  If it did not, look for it at:
www.tcl.tk/software/tcltk/

To export a GNU Triangulated Surface file from Art of Illusion, you can use the Export GNU Triangulated Surface script at:
http://members.axion.net/~enrique/Export%20GNU%20Triangulated%20Surface.bsh

To bring it into Art of Illusion, drop it into the folder ArtOfIllusion/Scripts/Tools/.

The GNU Triangulated Surface format is supported by Mesh Viewer, and it is described at:
http://gts.sourceforge.net/reference/gts-surfaces.html#GTS-SURFACE-WRITE

To turn an STL file into sliced gcode, first import the file using the STL import plugin in the import submenu of the file menu of Art of Illusion.
Then from the Scripts submenu in the Tools menu, choose 'Export GNU Triangulated Surface' and select the imported STL shape.  Click the
'Export Selected' checkbox and click OK.  Then type 'python slice.py' in a shell in the folder which slice is in and when the dialog pops up, set
the parameters.  Then click 'Slice', choose the file which you exported in 'Export GNU Triangulated Surface' and the sliced file will be saved
with the suffix '_slice'.

To write documentation for this program, open a shell in the slice.py directory, then type 'pydoc -w slice', then open 'slice.html' in a browser
or click on the '?' button in the dialog.  To use other functions of slice, type 'python' in a shell to run the python interpreter, then type 'import slice'
to import this program.

The computation intensive python modules will use psyco if it is available and run about twice as fast.  Psyco is described at:
http://psyco.sourceforge.net/index.html

The psyco download page is:
http://psyco.sourceforge.net/download.html

The following examples slice the GNU Triangulated Surface file Hollow Square.gts.  The examples are run in a terminal in the folder which
contains Hollow Square.gts and slice.py.  The preferences can be set in the dialog or by changing the preferences file 'slice.csv' with a text editor
or a spreadsheet program set to separate tabs.


> pydoc -w slice
wrote slice.html


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


>>> slice.sliceFile()
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
try:
	import psyco
	psyco.full()
except:
	pass
from vec3 import Vec3
import cStringIO
import euclidean
import gcodec
import intercircle
import math
import os
import preferences
import time
import vectorwrite


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/02/05 $"
__license__ = "GPL 3.0"


def addEdgePair( edgePairTable, edges, faceEdgeIndex, remainingEdgeIndex, remainingEdgeTable ):
	"Add edge pair to the edge pair table."
	if faceEdgeIndex == remainingEdgeIndex:
		return
	if not faceEdgeIndex in remainingEdgeTable:
		return
	edgePair = EdgePair().getFromIndexFirstSecond( remainingEdgeIndex, faceEdgeIndex, edges )
	edgePairTable[ str( edgePair ) ] = edgePair

def getCommonVertexIndex( edgeFirst, edgeSecond ):
	"Get the vertex index that both edges have in common."
	if edgeFirst.vertexIndexFirst == edgeSecond.vertexIndexFirst or edgeFirst.vertexIndexFirst == edgeSecond.vertexIndexSecond:
		return edgeSecond.vertexIndexFirst
	if edgeFirst.vertexIndexSecond == edgeSecond.vertexIndexFirst or edgeFirst.vertexIndexSecond == edgeSecond.vertexIndexSecond:
		return edgeSecond.vertexIndexSecond
	print( "Inconsistent GNU Triangulated Surface" )
	print( edgeFirst )
	print( edgeSecond )
	return 0

def getLoopsFromCorrectMesh( edges, faces, vertices, z ):
	"Get loops from a slice of a correct mesh."
	remainingEdgeTable = getRemainingEdgeTable( edges, vertices, z )
	remainingValues = remainingEdgeTable.values()
	for edge in remainingValues:
		if edge.faceIndexFirst == None:
			print( 'This should never happen, there is a hole in the triangle mesh, each edge should have two faces.' )
			print( edge )
			print( "Something will still be printed, but there is no guarantee that it will be the correct shape." )
			print( 'Once the gcode is saved, you should check over the layer with a z of:' )
			print( z )
			return None
		if edge.faceIndexSecond == None:
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
	return loops

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
		if edge.faceIndexFirst != None:
			faceOne = faces[ edge.faceIndexFirst ]
			addEdgePair( edgePairTable, edges, faceOne.edgeIndexFirst, remainingEdgeIndexKey, remainingEdgeTable )
			addEdgePair( edgePairTable, edges, faceOne.edgeIndexSecond, remainingEdgeIndexKey, remainingEdgeTable )
			addEdgePair( edgePairTable, edges, faceOne.edgeIndexThird, remainingEdgeIndexKey, remainingEdgeTable )
		if edge.faceIndexSecond != None:
			faceTwo = faces[ edge.faceIndexSecond ]
			addEdgePair( edgePairTable, edges, faceTwo.edgeIndexFirst, remainingEdgeIndexKey, remainingEdgeTable )
			addEdgePair( edgePairTable, edges, faceTwo.edgeIndexSecond, remainingEdgeIndexKey, remainingEdgeTable )
			addEdgePair( edgePairTable, edges, faceTwo.edgeIndexThird, remainingEdgeIndexKey, remainingEdgeTable )
	for edgePairValue in edgePairTable.values():
		edgePairValue.addPointsAtZ( points, importRadius, vertices, z )
	path = euclidean.getAwayPath( points, importRadius )
	allCircleNodes = intercircle.getCircleNodesFromPath( path, importRadius )
	allCircleIntersections = intercircle.getCircleIntersectionsFromCircleNodes( allCircleNodes )
	allCircleIntersectionLoops = intercircle.getCircleIntersectionLoops( allCircleIntersections )
	centers = intercircle.getCentersFromIntersectionLoops( allCircleIntersectionLoops )
	return intercircle.getLoopsfromLoopsDirection( slicePreferences.importTinyDetails.value, centers )

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
	if edge.faceIndexFirst != None:
		firstFace = faces[ edge.faceIndexFirst ]
		if firstFace.edgeIndexFirst in remainingEdgeTable:
			return firstFace.edgeIndexFirst
		if firstFace.edgeIndexSecond in remainingEdgeTable:
			return firstFace.edgeIndexSecond
		if firstFace.edgeIndexThird in remainingEdgeTable:
			return firstFace.edgeIndexThird
	if edge.faceIndexSecond != None:
		secondFace = faces[ edge.faceIndexSecond ]
		if secondFace.edgeIndexFirst in remainingEdgeTable:
			return secondFace.edgeIndexFirst
		if secondFace.edgeIndexSecond in remainingEdgeTable:
			return secondFace.edgeIndexSecond
		if secondFace.edgeIndexThird in remainingEdgeTable:
			return secondFace.edgeIndexThird
	return - 1

def getPath( edges, pathIndexes, loop, z ):
	"Get the path from the edge intersections."
	path = []
	for pathIndexIndex in range( len( pathIndexes ) ):
		pathIndex = pathIndexes[ pathIndexIndex ]
		edge = edges[ pathIndex ]
		pathPoint = getSliceIntersectionFromEdge( edge, loop, z )
		path.append( pathPoint )
	return path

def getPathIndexesAddPath( edges, faces, loops, remainingEdgeTable, loop, z ):
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
	loops.append( getPath( edges, pathIndexes, loop, z ) )
	return pathIndexes

def getRemainingEdgeTable( edges, vertices, z ):
	"Get the remaining edge hashtable."
	remainingEdgeTable = {}
	for edgeIndex in range( len( edges ) ):
		edge = edges[ edgeIndex ]
		if isZInEdge( edge, vertices, z ):
			remainingEdgeTable[ edgeIndex ] = edge
	return remainingEdgeTable

def getSharedFace( firstEdge, faces, secondEdge ):
	"Get the face which is shared by two edges."
	if firstEdge.faceIndexFirst == secondEdge.faceIndexFirst or firstEdge.faceIndexFirst == secondEdge.faceIndexSecond:
		return faces[ firstEdge.faceIndexFirst ]
	if firstEdge.faceIndexSecond == secondEdge.faceIndexFirst or firstEdge.faceIndexSecond == secondEdge.faceIndexSecond:
		return faces[ firstEdge.faceIndexSecond ]
	return None

def getSliceGcode( gnuTriangulatedSurfaceText, slicePreferences = None ):
	"Slice a GNU Triangulated Surface text."
	if gnuTriangulatedSurfaceText == '':
		return ''
	if slicePreferences == None:
		slicePreferences = SlicePreferences()
		preferences.readPreferences( slicePreferences )
	skein = SliceSkein()
	skein.parseGcode( slicePreferences, gnuTriangulatedSurfaceText )
	return skein.output.getvalue()

def getSliceIntersectionFromEdge( edge, loop, z ):
	"Get the point where the slice intersects the edge."
	firstVertex = loop[ edge.vertexIndexFirst ]
	secondVertex = loop[ edge.vertexIndexSecond ]
	zMinusFirst = z - firstVertex.z
	up = secondVertex.z - firstVertex.z
	sliceIntersection = secondVertex.minus( firstVertex )
	sliceIntersection.scale( zMinusFirst / up )
	sliceIntersection.add( firstVertex )
	return sliceIntersection

def isZInEdge( edge, vertices, z ):
	"Determine if z is inside the edge."
	vertex1ZHigher = vertices[ edge.vertexIndexFirst ].z > z
	vertex2ZHigher = vertices[ edge.vertexIndexSecond ].z > z
	return vertex1ZHigher != vertex2ZHigher

def sliceFile( filename = '' ):
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
	gcodec.writeFileText( suffixFilename, getSliceGcode( gnuTriangulatedSurfaceText, slicePreferences ) )
	print( 'The sliced file is saved as ' + gcodec.getSummarizedFilename( suffixFilename ) )
	if slicePreferences.writeSVG.value:
		vectorwrite.writeVectorFile( suffixFilename )
	print( 'It took ' + str( int( round( time.time() - startTime ) ) ) + ' seconds to slice the file.' )


class Edge:
	"An edge of a triangle mesh."
	def __init__( self ):
		"Set the face indexes to None."
		self.faceIndexFirst = None
		self.faceIndexSecond = None
	
	def __repr__( self ):
		"Get the string representation of this Edge."
		return str( self.index ) + ' ' + str( self.faceIndexFirst ) + ' ' + str( self.faceIndexSecond ) + ' ' + str( self.vertexIndexFirst ) + ' ' + str( self.vertexIndexSecond )

	def addFaceIndex( self, faceIndex ):
		"Add first None face index to input face index."
		if self.faceIndexFirst == None:
			self.faceIndexFirst = faceIndex
			return
		self.faceIndexSecond = faceIndex

	def getFromVertexIndices( self, edgeIndex, vertexIndexFirst, vertexIndexSecond ):
		"Initialize from two vertex indices."
		self.index = edgeIndex
		self.vertexIndexFirst = vertexIndexFirst
		self.vertexIndexSecond = vertexIndexSecond
		return self


class EdgePair:
	def __init__( self ):
		"Pair of edges on a face."
		self.edgeIndexFirst = 0
		self.edgeIndexSecond = 0
		self.edgeFirst = None
		self.edgeSecond = None

	def __repr__( self ):
		"Get the string representation of this EdgePair."
		return str( self.edgeIndexFirst ) + " " + str( self.edgeIndexSecond )

	def addPointsAtZ( self, points, radius, vertices, z ):
		"Add points on the segment between the edge intersections with z."
		sliceIntersectionFirst = getSliceIntersectionFromEdge( self.edgeFirst, vertices, z )
		sliceIntersectionSecond = getSliceIntersectionFromEdge( self.edgeSecond, vertices, z )
		intercircle.addPointsFromSegment( points, radius, sliceIntersectionFirst, sliceIntersectionSecond )

	def getFromIndexFirstSecond( self, edgeIndexFirst, edgeIndexSecond, edges ):
		"Initialize from edge indices."
		self.edgeIndexFirst = edgeIndexFirst
		self.edgeIndexSecond = edgeIndexSecond
		if edgeIndexSecond < edgeIndexFirst:
			self.edgeIndexFirst = edgeIndexSecond
			self.edgeIndexSecond = edgeIndexFirst
		self.edgeFirst = edges[ self.edgeIndexFirst ]
		self.edgeSecond = edges[ self.edgeIndexSecond ]
		return self


class Face:
	"A face of a triangle mesh."
	def __init__( self ):
		"Set the edge indexes to None."
		self.edgeIndexFirst = None
		self.edgeIndexSecond = None
		self.edgeIndexThird = None
	
	def __repr__( self ):
		"Get the string representation of this Face."
		representation = str( self.index ) + ' ' + str( self.edgeIndexFirst ) + ' ' + str( self.edgeIndexSecond ) + ' ' + str( self.edgeIndexThird )
		return representation + ' ' + str( self.vertexIndexFirst ) + ' ' + str( self.vertexIndexSecond ) + ' ' + str( self.vertexIndexThird )

	def getFromEdgeIndices( self, edges, faceIndex, edgeIndexFirst, edgeIndexSecond, edgeIndexThird ):
		"Initialize from edge indices."
		self.index = faceIndex
		self.edgeIndexFirst = edgeIndexFirst
		self.edgeIndexSecond = edgeIndexSecond
		self.edgeIndexThird = edgeIndexThird
		edgeFirst = edges[ edgeIndexFirst ]
		edgeFirst.addFaceIndex( faceIndex )
		edgeSecond = edges[ edgeIndexSecond ]
		edgeSecond.addFaceIndex( faceIndex )
		edgeThird = edges[ edgeIndexThird ]
		edgeThird.addFaceIndex( faceIndex )
		self.vertexIndexFirst = getCommonVertexIndex( edgeFirst, edgeSecond )
		self.vertexIndexSecond = getCommonVertexIndex( edgeThird, edgeFirst )
		self.vertexIndexThird = getCommonVertexIndex( edgeSecond, edgeThird )
		return self


class SliceSkein:
	"A class to slice a GNU Triangulated Surface."
	def __init__( self ):
		self.output = cStringIO.StringIO()

	def addExtruderPaths( self, layerIndex ):
		"Add extruder loops."
		self.addLine( '( Extruder paths for layer ' + str( layerIndex ) + ' )' ) # GCode formatted comment
		self.addLine( 'M113 (' + str( layerIndex ) ) # Indicate that a new layer is starting.
		z = self.layerBottom + float( layerIndex ) * self.layerThickness
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
		doubleExtrusionWidth = 2.0 * self.extrusionWidth
		extruderPaths = []
		for loop in loops:
			centersFromLoopDirection = intercircle.getCentersfromLoopDirection( not euclidean.isWiddershins( loop ), loop, self.extrusionWidth )
			for centerFromDirection in centersFromLoopDirection:
				if euclidean.getMaximumSpan( centerFromDirection ) > doubleExtrusionWidth:
					centers.append( centerFromDirection )
		for center in centers:
			extrudateLoop = intercircle.getInsetFromClockwiseLoop( center, self.halfExtrusionWidth )
			self.addGcodeFromThread( extrudateLoop + [ extrudateLoop[ 0 ] ] )

	def addGcodeMovement( self, point ):
		"Add a movement to the output."
		self.addLine( "G1 X%s Y%s Z%s" % ( euclidean.getRoundedToThreePlaces( point.x ), euclidean.getRoundedToThreePlaces( point.y ), euclidean.getRoundedToThreePlaces( point.z ) ) )

	def addGcodeFromThread( self, thread ):
		"Add a thread to the output."
		if len( thread ) > 0:
			self.addGcodeMovement( thread[ 0 ] )
		else:
			print( "zero length vertex positions array which was skipped over, this should never happen" )
		if len( thread ) < 2:
			return
		self.addLine( "M101" ) # Turn extruder on.
		if len( thread ) > 3:
			self.addLine( 'M114' ) # Indicate that a loop is beginning.
		for point in thread[ 1 : ]:
			self.addGcodeMovement( point )
		self.addLine( "M103" ) # Turn extruder off.

	def addInitializationToOutput( self ):
		"Add initialization gcode to the output."
		self.addLine( '( GCode generated by May 8, 2008 slice.py )' ) # GCode formatted comment
		self.addLine( '( Extruder Initialization )' ) # GCode formatted comment
		self.addLine( "M100 P210" ); # Set extruder speed to 210.
		self.addLine( "M103" ); # Turn extruder off.
		self.addLine( "M105" ); # Custom code for temperature reading.
		self.addLine( "M108 (" + euclidean.getRoundedToThreePlaces( self.extrusionDiameter ) ); # Set extrusion diameter.
		self.addLine( "M109 (" + euclidean.getRoundedToThreePlaces( self.extrusionWidth ) ); # Set extrusion width.
		self.addLine( "M110 (" + euclidean.getRoundedToThreePlaces( self.layerThickness ) ); # Set layer thickness.
		self.addLine( "G21" ); # Set units to mm.
		self.addLine( "G90" ); # Set positioning to absolute.
		self.addLine( "G28" ); # Start at home.
		self.addLine( "M111 (slice)" ); # The skein has been sliced.
		self.addLine( "M112" ); # Initialization is finished, extrusion is starting.
		self.addLine( "( Extruder Movement )" ); # GCode formatted comment

	def addLine( self, line ):
		"Add a line of text and a newline to the output."
		self.output.write( line + "\n" )

	def addShutdownToOutput( self ):
		"Add shutdown gcode to the output."
		self.addLine( '( Extruder Shut Down )' ) # GCode formatted comment
		self.addLine( "M103" ) # Turn extruder off.

	def addToZoneArray( self, point, zoneArray, z ):
		"Add a height to the zone array."
		zoneLayer = int( round( ( point.z - z ) / self.zZoneInterval ) )
		zoneAround = 2 * int( abs( zoneLayer ) )
		if zoneLayer < 0:
			zoneAround -= 1
		if zoneAround < len( zoneArray ):
			zoneArray[ zoneAround ] += 1

	def getLoopsFromMesh( self, z ):
		"Get loops from a slice of a mesh."
		loops = []
		originalLoops = []
		if self.slicePreferences.correct.value:
			originalLoops = getLoopsFromCorrectMesh( self.triangleMesh.edges, self.triangleMesh.faces, self.triangleMesh.vertices, z )
		if len( loops ) < 1:
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

	def parseGcode( self, slicePreferences, gnuTriangulatedSurfaceText ):
		"Parse gnu triangulated surface text and store the sliced gcode."
		self.slicePreferences = slicePreferences
		self.triangleMesh = TriangleMesh().getFromGNUTriangulatedSurfaceText( gnuTriangulatedSurfaceText )
		self.extrusionDiameter = slicePreferences.extrusionDiameter.value
		squareSectionWidth = self.extrusionDiameter * math.sqrt( math.pi / slicePreferences.extrusionFillDensity.value ) / 2.0
		extrusionWidthOverThicknessSquareRoot = math.sqrt( slicePreferences.extrusionWidthOverThickness.value )
		self.extrusionWidth = squareSectionWidth * extrusionWidthOverThicknessSquareRoot
		self.halfExtrusionWidth = 0.5 * self.extrusionWidth
		self.layerThickness = squareSectionWidth / extrusionWidthOverThicknessSquareRoot
		self.halfThickness = 0.5 * self.layerThickness
		self.zZoneLayers = 99
		self.zZoneInterval = self.layerThickness / self.zZoneLayers / 100.0
		self.bottom = 999999999.0
		self.top = - self.bottom
		for point in self.triangleMesh.vertices:
			self.bottom = min( self.bottom, point.z )
			self.top = max( self.top, point.z )
		self.layerBottom = self.bottom + self.halfThickness
		self.layerTop = self.top - self.halfThickness * 0.5
		skeinHeight = self.layerTop - self.layerBottom
		numberOfLayers = int( math.floor( skeinHeight / self.layerThickness ) + 1 )
		self.addInitializationToOutput()
		for layerIndex in range( numberOfLayers ):
			self.addExtruderPaths( layerIndex )
		self.addShutdownToOutput()


class SlicePreferences:
	"A class to handle the slice preferences."
	def __init__( self ):
		"Set the default preferences, execute title & preferences filename."
		#Set the default preferences.
		self.extrusionDiameter = preferences.FloatPreference().getFromValue( 'Extrusion Diameter (mm):', 0.8 )
		self.extrusionFillDensity = preferences.FloatPreference().getFromValue( 'Extrusion Density (ratio):', 0.9 )
		self.extrusionWidthOverThickness = preferences.FloatPreference().getFromValue( 'Extrusion Width Over Thickness (ratio):', 1.0 )
		self.filenameInput = preferences.Filename().getFromFilename( [ ( 'GNU Triangulated Surface files', '*.gts' ) ], 'Open File to be Sliced', '' )
		self.fillBeginRotation = preferences.FloatPreference().getFromValue( 'Fill Begin Rotation (degrees):', 45.0 )
		self.importCoarseness = preferences.FloatPreference().getFromValue( 'Import Coarseness (ratio):', 1.0 )
		importRadio = []
		self.correct = preferences.RadioLabel().getFromRadioLabel( 'Correct Mesh', 'Mesh Type:', importRadio, True )
		self.unproven = preferences.Radio().getFromRadio( 'Unproven Mesh', importRadio,False  )
		self.importTinyDetails = preferences.BooleanPreference().getFromValue( 'Import Tiny Details:', True )
		self.writeSVG = preferences.BooleanPreference().getFromValue( 'Write Scalable Vector Graphics:', True )
		directoryRadio = []
		self.directoryPreference = preferences.RadioLabel().getFromRadioLabel( 'Slice All GNU Triangulated Surface Files in a Directory', 'File or Directory:', directoryRadio, False )
		self.filePreference = preferences.Radio().getFromRadio( 'Slice File', directoryRadio, True )
		#Create the archive, title of the execute button, title of the dialog & preferences filename.
		self.archive = [
			self.extrusionDiameter,
			self.extrusionFillDensity,
			self.extrusionWidthOverThickness,
			self.filenameInput,
			self.importCoarseness,
			self.correct,
			self.unproven,
			self.importTinyDetails,
			self.writeSVG,
			self.directoryPreference,
			self.filePreference ]
		self.executeTitle = 'Slice'
#		self.filename = getPreferencesFilePath( 'slice.csv' )
		self.filenamePreferences = 'slice.csv'
		self.filenameHelp = 'slice.html'
		self.title = 'Slice Preferences'

	def execute( self ):
		"Slice button has been clicked."
		filenames = gcodec.getGNUDirectoryOrFile( self.directoryPreference.value, self.filenameInput.value, self.filenameInput.wasCancelled )
		for filename in filenames:
			sliceFile( filename )


"""
Quoted from http://gts.sourceforge.net/reference/gts-surfaces.html#GTS-SURFACE-WRITE
"All the lines beginning with GTS_COMMENTS (#!) are ignored. The first line contains three unsigned integers separated by spaces. The first integer is the number of vertices, nv, the second is the number of edges, ne and the third is the number of faces, nf.

Follows nv lines containing the x, y and z coordinates of the vertices. Follows ne lines containing the two indices (starting from one) of the vertices of each edge. Follows nf lines containing the three ordered indices (also starting from one) of the edges of each face.

The format described above is the least common denominator to all GTS files. Consistent with an object-oriented approach, the GTS file format is extensible. Each of the lines of the file can be extended with user-specific attributes accessible through the read() and write() virtual methods of each of the objects written (surface, vertices, edges or faces). When read with different object classes, these extra attributes are just ignored."
"""

class TriangleMesh:
	"A triangle mesh."
	def __init__( self ):
		"Add empty lists."
		self.edges = []
		self.faces = []
		self.vertices = []
	
	def __repr__( self ):
		"Get the string representation of this StretchedXSegment."
		return str( self.vertices ) + '\n' + str( self.edges ) + '\n' + str( self.faces )

	def getFromGNUTriangulatedSurfaceText( self, gnuTriangulatedSurfaceText ):
		"Initialize from gnuTriangulatedSurfaceText."
		lines = gcodec.getTextLines( gnuTriangulatedSurfaceText )
		linesWithoutComments = []
		for line in lines:
			if len( line ) > 0:
				firstCharacter = line[ 0 ]
				if firstCharacter != '#' and firstCharacter != '!':
					linesWithoutComments.append( line )
		splitLine = linesWithoutComments[ 0 ].split( " " )
		numberOfVertices = int( splitLine[ 0 ] )
		numberOfEdges = int( splitLine[ 1 ] )
		numberOfFaces = int( splitLine[ 2 ] )
		faceTriples = []
		for vertexIndex in range( numberOfVertices ):
			line = linesWithoutComments[ vertexIndex + 1 ]
			splitLine = line.split( " " )
			vertex = Vec3().getFromXYZ( float( splitLine[ 0 ] ), float( splitLine[ 1 ] ), float( splitLine[ 2 ] ) )
			self.vertices.append( vertex )
		edgeStart = numberOfVertices + 1
		for edgeIndex in range( numberOfEdges ):
			line = linesWithoutComments[ edgeIndex + edgeStart ]
			splitLine = line.split( " " )
			edge = Edge().getFromVertexIndices( edgeIndex, int( splitLine[ 0 ] ) - 1, int( splitLine[ 1 ] ) - 1 )
			self.edges.append( edge )
		faceStart = edgeStart + numberOfEdges
		for faceIndex in range( numberOfFaces ):
			line = linesWithoutComments[ faceIndex + faceStart ]
			splitLine = line.split( " " )
			edgeIndexFirst = int( splitLine[ 0 ] ) - 1
			edgeIndexSecond = int( splitLine[ 1 ] ) - 1
			edgeIndexThird = int( splitLine[ 2 ] ) - 1
			face = Face().getFromEdgeIndices( self.edges, faceIndex, edgeIndexFirst, edgeIndexSecond, edgeIndexThird )
			self.faces.append( face )
		return self


def main( hashtable = None ):
	"Display the slice dialog."
	preferences.displayDialog( SlicePreferences() )

if __name__ == "__main__":
	main()

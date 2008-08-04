"""
Triangle Mesh holds the faces and edges of a triangular mesh.

It can read from and write to a GNU Triangulated Surface (.gts) file.

The following examples slice the GNU Triangulated Surface file Hollow Square.gts.  The examples are run in a terminal in the folder which
contains Hollow Square.gts and triangle_mesh.py.


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
#Init has to be imported first because it has code to workaround the python bug where relative imports don't work if the module is imported as a main module.
import __init__

from skeinforge_tools.skeinforge_utilities.vec3 import Vec3
from skeinforge_tools.skeinforge_utilities import gcodec
import cStringIO


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__credits__ = 'Art of Illusion <http://www.artofillusion.org/>'
__date__ = "$Date: 2008/02/05 $"
__license__ = "GPL 3.0"


def getCommonVertexIndex( edgeFirst, edgeSecond ):
	"Get the vertex index that both edges have in common."
	for edgeFirstVertexIndex in edgeFirst.vertexIndexes:
		if edgeFirstVertexIndex == edgeSecond.vertexIndexes[ 0 ] or edgeFirstVertexIndex == edgeSecond.vertexIndexes[ 1 ]:
			return edgeFirstVertexIndex
	print( "Inconsistent GNU Triangulated Surface" )
	print( edgeFirst )
	print( edgeSecond )
	return 0

def getTriangleMesh( filename = '' ):
	"Slice a GNU Triangulated Surface file.  If no filename is specified, slice the first GNU Triangulated Surface file in this folder."
	if filename == '':
		unmodified = gcodec.getGNUTriangulatedSurfaceFiles()
		if len( unmodified ) == 0:
			print( "There are no GNU Triangulated Surface files in this folder." )
			return None
		filename = unmodified[ 0 ]
	gnuTriangulatedSurfaceText = gcodec.getFileText( filename )
	triangleMesh = TriangleMesh().getFromGNUTriangulatedSurfaceText( gnuTriangulatedSurfaceText )
	return triangleMesh


class Edge:
	"An edge of a triangle mesh."
	def __init__( self ):
		"Set the face indexes to None."
		self.faceIndexes = []
		self.vertexIndexes = []
	
	def __repr__( self ):
		"Get the string representation of this Edge."
		return str( self.index ) + ' ' + str( self.faceIndexes ) + ' ' + str( self.vertexIndexes )

	def addFaceIndex( self, faceIndex ):
		"Add first None face index to input face index."
		self.faceIndexes.append( faceIndex )

	def getFromVertexIndexes( self, edgeIndex, vertexIndexes ):
		"Initialize from two vertex indices."
		self.index = edgeIndex
		self.vertexIndexes = vertexIndexes[ : ]
		self.vertexIndexes.sort()
		return self

	def getGNUTriangulatedSurfaceLine( self ):
		"Get the GNU Triangulated Surface (.gts) line of text."
		return '%s %s' % ( self.vertexIndexes[ 0 ] + 1, self.vertexIndexes[ 1 ] + 1 )


class EdgePair:
	def __init__( self ):
		"Pair of edges on a face."
		self.edgeIndexes = []
		self.edges = []

	def __repr__( self ):
		"Get the string representation of this EdgePair."
		return str( self.edgeIndexes )

	def getFromIndexFirstSecond( self, edgeIndexes, edges ):
		"Initialize from edge indices."
		self.edgeIndexes = edgeIndexes[ : ]
		self.edgeIndexes.sort()
		for edgeIndex in self.edgeIndexes:
			self.edges.append( edges[ edgeIndex ] )
		return self

class Face:
	"A face of a triangle mesh."
	def __init__( self ):
		"Set the edge indexes to None."
		self.edgeIndexes = []
		self.index = None
		self.vertexIndexes = []
	
	def __repr__( self ):
		"Get the string representation of this Face."
		return str( self.index ) + ' ' + str( self.edgeIndexes ) + ' ' + str( self.vertexIndexes )

	def getFromEdgeIndexes( self, edgeIndexes, edges, faceIndex ):
		"Initialize from edge indices."
		self.index = faceIndex
		self.edgeIndexes = edgeIndexes
		for edgeIndex in edgeIndexes:
			edges[ edgeIndex ].addFaceIndex( faceIndex )
		for triangleIndex in range( 3 ):
			indexFirst = ( 3 - triangleIndex ) % 3
			indexSecond = ( 4 - triangleIndex ) % 3
			self.vertexIndexes.append( getCommonVertexIndex( edges[ edgeIndexes[ indexFirst ] ], edges[ edgeIndexes[ indexSecond ] ] ) )
		return self

	def getGNUTriangulatedSurfaceLine( self ):
		"Get the GNU Triangulated Surface (.gts) line of text."
		return '%s %s %s' % ( self.edgeIndexes[ 0 ] + 1, self.edgeIndexes[ 1 ] + 1, self.edgeIndexes[ 2 ] + 1 )

	def setEdgeIndexesToVertexIndexes( self, edges, edgeTable ):
		"Set the edge indexes to the vertex indexes."
		for triangleIndex in range( 3 ):
			indexFirst = ( 3 - triangleIndex ) % 3
			indexSecond = ( 4 - triangleIndex ) % 3
			vertexIndexFirst = self.vertexIndexes[ indexFirst ]
			vertexIndexSecond = self.vertexIndexes[ indexSecond ]
			vertexIndexPair = [ vertexIndexFirst, vertexIndexSecond ]
			vertexIndexPair.sort()
			edgeIndex = len( edges )
			if str( vertexIndexPair ) in edgeTable:
				edgeIndex = edgeTable[ str( vertexIndexPair ) ]
			else:
				edgeTable[ str( vertexIndexPair ) ] = edgeIndex
				edge = Edge().getFromVertexIndexes( edgeIndex, vertexIndexPair )
				edges.append( edge )
			edges[ edgeIndex ].addFaceIndex( self.index )
			self.edgeIndexes.append( edgeIndex )
		return self


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
		"Get the string representation of this TriangleMesh."
		return str( self.vertices ) + '\n' + str( self.edges ) + '\n' + str( self.faces )

	def getGNUTriangulatedSurfaceText( self ):
		"Get this mesh in the GNU Triangulated Surface (.gts) format."
		output = cStringIO.StringIO()
		output.write( '%s %s %s Number of Vertices,Number of Edges,Number of Faces\n' % ( len( self.vertices ), len( self.edges ), len( self.faces ) ) )
		output.write( '%s %s %s Vertex Coordinates XYZ\n' % ( self.vertices[ 0 ].x, self.vertices[ 0 ].y, self.vertices[ 0 ].z ) )
		for vertex in self.vertices[ 1 : ]:
			output.write( '%s %s %s\n' % ( vertex.x, vertex.y, vertex.z ) )
		output.write( '%s Edge Vertex Indices Starting from 1\n' % self.edges[ 0 ].getGNUTriangulatedSurfaceLine() )
		for edge in self.edges[ 1 : ]:
			output.write( '%s\n' % edge.getGNUTriangulatedSurfaceLine() )
		output.write( '%s Face Edge Indices Starting from 1\n' % self.faces[ 0 ].getGNUTriangulatedSurfaceLine() )
		for face in self.faces[ 1 : ]:
			output.write( '%s\n' % face.getGNUTriangulatedSurfaceLine() )
		return output.getvalue()

	def getFromGNUTriangulatedSurfaceText( self, gnuTriangulatedSurfaceText ):
		"Initialize from a GNU Triangulated Surface Text."
		lines = gcodec.getTextLines( gnuTriangulatedSurfaceText )
		linesWithoutComments = []
		for line in lines:
			if len( line ) > 0:
				firstCharacter = line[ 0 ]
				if firstCharacter != '#' and firstCharacter != '!':
					linesWithoutComments.append( line )
		splitLine = linesWithoutComments[ 0 ].split()
		numberOfVertices = int( splitLine[ 0 ] )
		numberOfEdges = int( splitLine[ 1 ] )
		numberOfFaces = int( splitLine[ 2 ] )
		faceTriples = []
		for vertexIndex in range( numberOfVertices ):
			line = linesWithoutComments[ vertexIndex + 1 ]
			splitLine = line.split()
			vertex = Vec3( float( splitLine[ 0 ] ), float( splitLine[ 1 ] ), float( splitLine[ 2 ] ) )
			self.vertices.append( vertex )
		edgeStart = numberOfVertices + 1
		for edgeIndex in range( numberOfEdges ):
			line = linesWithoutComments[ edgeIndex + edgeStart ]
			splitLine = line.split()
			vertexIndexes = []
			for word in splitLine[ : 2 ]:
				vertexIndexes.append( int( word ) - 1 )
			edge = Edge().getFromVertexIndexes( edgeIndex, vertexIndexes )
			self.edges.append( edge )
		faceStart = edgeStart + numberOfEdges
		for faceIndex in range( numberOfFaces ):
			line = linesWithoutComments[ faceIndex + faceStart ]
			splitLine = line.split()
			edgeIndexes = []
			for word in splitLine[ : 3 ]:
				edgeIndexes.append( int( word ) - 1 )
			face = Face().getFromEdgeIndexes( edgeIndexes, self.edges, faceIndex )
			self.faces.append( face )
		return self

	def setEdgesForAllFaces( self ):
		"Set the face edges of all the faces."
		edgeTable = {}
		for face in self.faces:
			face.setEdgeIndexesToVertexIndexes( self.edges, edgeTable )

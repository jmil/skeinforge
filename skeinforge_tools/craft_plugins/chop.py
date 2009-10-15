"""
Chop shape is a script to chop a list of slice layers.

Chop chops a list of slices into svg slice layers.  The 'Layer Thickness' is the thickness the extrusion layer at default extruder speed,
this is the most important chop preference.  The 'Perimeter Width over Thickness' is the ratio of the extrusion perimeter width to the
layer thickness.  The higher the value the more the perimeter will be inset, the default is 1.8.  A ratio of one means the extrusion is a
circle, a typical ratio of 1.8 means the extrusion is a wide oval.  These values should be measured from a test extrusion line.

When a triangle mesh has holes in it, the triangle mesh slicer switches over to a slow algorithm that spans gaps in the mesh.  The
higher the 'Import Coarseness' setting, the wider the gaps in the mesh it will span.  An import coarseness of one means it will span gaps
of the perimeter width.  When the Mesh Type preference is Correct Mesh, the mesh will be accurately carved, and if a hole is found,
carve will switch over to the algorithm that spans gaps.  If the Mesh Type preference is Unproven Mesh, carve will use the gap spanning
algorithm from the start.  The problem with the gap spanning algothm is that it will span gaps, even if there is not actually a gap in the
model.

The 'Extra Decimal Places' is the number of extra decimal places export will output compared to the number of decimal places in the
layer thickness.  The higher the 'Extra Decimal Places', the more significant figures the output numbers will have, the default is one.

Chop slices from top to bottom.  The output will go from the "Layers From" index to the "Layers To" index.  The default for the
"Layers From" index is zero and the default for the "Layers To" is a really big number.  To get only the bottom layer, set the
"Layers From" to minus one.

To run chop, in a shell type:
> python chop.py

The following examples chop the file Screw Holder Bottom.stl.  The examples are run in a terminal in the folder which contains
Screw Holder Bottom.stl and chop.py.  The preferences can be set in the dialog or by changing the preferences file 'chop.csv'
with a text editor or a spreadsheet program set to separate tabs.


> python chop.py
This brings up the dialog, after clicking 'Chop', the following is printed:
File Screw Holder Bottom.stl is being chopped.
The chopped file is saved as Screw Holder Bottom_chop.svg


>python
Python 2.5.1 (r251:54863, Sep 22 2007, 01:43:31)
[GCC 4.2.1 (SUSE Linux)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import chop
>>> chop.main()
File Screw Holder Bottom.stl is being chopped.
The chopped file is saved as Screw Holder Bottom_chop.svg
It took 3 seconds to chop the file.


>>> chop.writeOutput()
File Screw Holder Bottom.gcode is being chopped.
The chopped file is saved as Screw Holder Bottom_chop.svg
It took 3 seconds to chop the file.

"""

from __future__ import absolute_import
try:
	import psyco
	psyco.full()
except:
	pass
#Init has to be imported first because it has code to workaround the python bug where relative imports don't work if the module is imported as a main module.
import __init__

from skeinforge_tools import polyfile
from skeinforge_tools.skeinforge_utilities import euclidean
from skeinforge_tools.skeinforge_utilities import gcodec
from skeinforge_tools.skeinforge_utilities import interpret
from skeinforge_tools.skeinforge_utilities import preferences
from skeinforge_tools.skeinforge_utilities import svg_codec
import math
import os
import sys
import time


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/02/05 $"
__license__ = "GPL 3.0"


def getCraftedText( fileName, text = '', chopPreferences = None ):
	"Get chopped text."
	if gcodec.getHasSuffix( fileName, '.svg' ):
		if text == '':
			text = gcodec.getFileText( fileName )
		return text
	return getCraftedTextFromFileName( fileName, chopPreferences = None )

def getCraftedTextFromFileName( fileName, chopPreferences = None ):
	"Chop a shape file."
	carving = svg_codec.getCarving( fileName )
	if carving == None:
		return ''
	if chopPreferences == None:
		chopPreferences = ChopPreferences()
		preferences.getReadPreferences( chopPreferences )
	return ChopSkein().getCarvedSVG( chopPreferences, carving, fileName )

def getPreferencesConstructor():
	"Get the preferences constructor."
	return ChopPreferences()

def writeOutput( fileName = '' ):
	"Chop a GNU Triangulated Surface file.  If no fileName is specified, chop the first GNU Triangulated Surface file in this folder."
	if fileName == '':
		unmodified = gcodec.getFilesWithFileTypesWithoutWords( interpret.getImportPluginFilenames() )
		if len( unmodified ) == 0:
			print( "There are no carvable files in this folder." )
			return
		fileName = unmodified[ 0 ]
	startTime = time.time()
	print( 'File ' + gcodec.getSummarizedFilename( fileName ) + ' is being chopped.' )
	chopGcode = getCraftedText( fileName )
	if chopGcode == '':
		return
	suffixFilename = fileName[ : fileName.rfind( '.' ) ] + '_chop.svg'
	suffixDirectoryName = os.path.dirname( suffixFilename )
	suffixReplacedBaseName = os.path.basename( suffixFilename ).replace( ' ', '_' )
	suffixFilename = os.path.join( suffixDirectoryName, suffixReplacedBaseName )
	gcodec.writeFileText( suffixFilename, chopGcode )
	print( 'The chopped file is saved as ' + gcodec.getSummarizedFilename( suffixFilename ) )
	print( 'It took ' + str( int( round( time.time() - startTime ) ) ) + ' seconds to chop the file.' )
	preferences.openWebPage( suffixFilename )


class ChopPreferences:
	"A class to handle the chop preferences."
	def __init__( self ):
		"Set the default preferences, execute title & preferences fileName."
		#Set the default preferences.
		self.archive = []
		self.addExtraTopLayerIfNecessary = preferences.BooleanPreference().getFromValue( 'Add Extra Top Layer if Necessary', True )
		self.archive.append( self.addExtraTopLayerIfNecessary )
		self.fileNameInput = preferences.Filename().getFromFilename( interpret.getTranslatorFileTypeTuples(), 'Open File to be Chopped', '' )
		self.archive.append( self.fileNameInput )
		self.extraDecimalPlaces = preferences.IntPreference().getFromValue( 'Extra Decimal Places (integer):', 1 )
		self.archive.append( self.extraDecimalPlaces )
		self.importCoarseness = preferences.FloatPreference().getFromValue( 'Import Coarseness (ratio):', 1.0 )
		self.archive.append( self.importCoarseness )
		self.meshTypeLabel = preferences.LabelDisplay().getFromName( 'Mesh Type: ' )
		self.archive.append( self.meshTypeLabel )
		importRadio = []
		self.correctMesh = preferences.Radio().getFromRadio( 'Correct Mesh', importRadio, True )
		self.archive.append( self.correctMesh )
		self.unprovenMesh = preferences.Radio().getFromRadio( 'Unproven Mesh', importRadio, False )
		self.archive.append( self.unprovenMesh )
		self.layerThickness = preferences.FloatPreference().getFromValue( 'Layer Thickness (mm):', 0.4 )
		self.archive.append( self.layerThickness )
		self.layersFrom = preferences.IntPreference().getFromValue( 'Layers From (index):', 0 )
		self.archive.append( self.layersFrom )
		self.layersTo = preferences.IntPreference().getFromValue( 'Layers To (index):', 999999999 )
		self.archive.append( self.layersTo )
		self.perimeterWidth = preferences.FloatPreference().getFromValue( 'Perimeter Width (mm):', 0.6 )
		self.archive.append( self.perimeterWidth )
		#Create the archive, title of the execute button, title of the dialog & preferences fileName.
		self.executeTitle = 'Chop'
		self.saveCloseTitle = 'Save and Close'
		preferences.setHelpPreferencesFileNameTitleWindowPosition( self, 'skeinforge_tools.craft_plugins.chop.html' )

	def execute( self ):
		"Chop button has been clicked."
		fileNames = polyfile.getFileOrDirectoryTypes( self.fileNameInput.value, interpret.getImportPluginFilenames(), self.fileNameInput.wasCancelled )
		for fileName in fileNames:
			writeOutput( fileName )


class ChopSkein( svg_codec.SVGCodecSkein ):
	"A class to chop a carving."
	def addExtraTopLayerIfNecessary( self, rotatedBoundaryLayers ):
		"Add extra top layer if necessary."
		topRotatedBoundaryLayer = rotatedBoundaryLayers[ - 1 ]
		cuttingSafeHeight = topRotatedBoundaryLayer.z + 0.5001 * self.layerThickness
		if cuttingSafeHeight > self.cornerMaximum.z:
			return
		extraTopRotatedBoundaryLayer = topRotatedBoundaryLayer.getCopyAtZ( topRotatedBoundaryLayer.z + self.layerThickness )
		rotatedBoundaryLayers.append( extraTopRotatedBoundaryLayer )

	def addRotatedLoopLayersToOutput( self, rotatedBoundaryLayers ):
		"Add rotated boundary layers to the output."
		truncatedRotatedBoundaryLayers = rotatedBoundaryLayers[ self.chopPreferences.layersFrom.value : self.chopPreferences.layersTo.value ]
		for truncatedRotatedBoundaryLayerIndex in xrange( len( truncatedRotatedBoundaryLayers ) ):
			truncatedRotatedBoundaryLayer = truncatedRotatedBoundaryLayers[ truncatedRotatedBoundaryLayerIndex ]
			self.addRotatedLoopLayerToOutput( truncatedRotatedBoundaryLayerIndex, truncatedRotatedBoundaryLayer )

	def addRotatedLoopLayerToOutput( self, layerIndex, rotatedBoundaryLayer ):
		"Add rotated boundary layer to the output."
		self.addLayerStart( layerIndex, rotatedBoundaryLayer.z )
		pathString = '\t\t\t<path transform="scale(%s, %s) translate(%s, %s)" d="' % ( self.unitScale, - self.unitScale, self.getRounded( - self.cornerMinimum.x ), self.getRounded( - self.cornerMinimum.y ) )
		if len( rotatedBoundaryLayer.loops ) > 0:
			pathString += self.getSVGLoopString( rotatedBoundaryLayer.loops[ 0 ] )
		for loop in rotatedBoundaryLayer.loops[ 1 : ]:
			pathString += ' ' + self.getSVGLoopString( loop )
		pathString += '"/>'
		self.addLine( pathString )
		self.addLine( '\t\t</g>' )

	def getCarvedSVG( self, chopPreferences, carving, fileName ):
		"Parse gnu triangulated surface text and store the chopped gcode."
		self.chopPreferences = chopPreferences
		self.layerThickness = chopPreferences.layerThickness.value
		self.setExtrusionDiameterWidth( chopPreferences )
		carving.setCarveLayerThickness( self.layerThickness )
		importRadius = 0.5 * chopPreferences.importCoarseness.value * abs( self.perimeterWidth )
		carving.setCarveImportRadius( max( importRadius, 0.01 * self.layerThickness ) )
		carving.setCarveIsCorrectMesh( chopPreferences.correctMesh.value )
		rotatedBoundaryLayers = carving.getCarveRotatedBoundaryLayers()
		if len( rotatedBoundaryLayers ) < 1:
			return ''
		self.cornerMaximum = carving.getCarveCornerMaximum()
		self.cornerMinimum = carving.getCarveCornerMinimum()
		if chopPreferences.addExtraTopLayerIfNecessary.value:
			self.addExtraTopLayerIfNecessary( rotatedBoundaryLayers )
		rotatedBoundaryLayers.reverse()
		#reset from slicable
		self.layerThickness = carving.getCarveLayerThickness()
		self.setExtrusionDiameterWidth( chopPreferences )
		self.decimalPlacesCarried = max( 0, 1 + chopPreferences.extraDecimalPlaces.value - int( math.floor( math.log10( self.layerThickness ) ) ) )
		self.extent = self.cornerMaximum - self.cornerMinimum
		self.svgTemplateLines = self.getReplacedSVGTemplateLines( fileName, rotatedBoundaryLayers )
		self.addInitializationToOutputSVG( 'chop' )
		self.addRotatedLoopLayersToOutput( rotatedBoundaryLayers )
		self.addShutdownToOutput()
		return self.output.getvalue()

	def setExtrusionDiameterWidth( self, chopPreferences ):
		"Set the extrusion diameter & width and the bridge thickness & width."
		self.perimeterWidth = chopPreferences.perimeterWidth.value


def main():
	"Display the chop dialog."
	if len( sys.argv ) > 1:
		writeOutput( ' '.join( sys.argv[ 1 : ] ) )
	else:
		preferences.startMainLoopFromConstructor( getPreferencesConstructor() )

if __name__ == "__main__":
	main()

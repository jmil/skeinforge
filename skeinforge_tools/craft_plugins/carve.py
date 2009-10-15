"""
Carve shape is a script to carve a list of slice layers.

Carve carves a list of slices into svg slice layers.  The 'Layer Thickness' is the thickness the extrusion layer at default extruder speed,
this is the most important carve preference.  The 'Perimeter Width over Thickness' is the ratio of the extrusion perimeter width to the
layer thickness.  The higher the value the more the perimeter will be inset, the default is 1.8.  A ratio of one means the extrusion is a
circle, a typical ratio of 1.8 means the extrusion is a wide oval.  These values should be measured from a test extrusion line.

When a triangle mesh has holes in it, the triangle mesh slicer switches over to a slow algorithm that spans gaps in the mesh.  The
higher the 'Import Coarseness' setting, the wider the gaps in the mesh it will span.  An import coarseness of one means it will span gaps
of the perimeter width.  When the Mesh Type preference is Correct Mesh, the mesh will be accurately carved, and if a hole is found,
carve will switch over to the algorithm that spans gaps.  If the Mesh Type preference is Unproven Mesh, carve will use the gap spanning
algorithm from the start.  The problem with the gap spanning algothm is that it will span gaps, even if there is not actually a gap in the
model.

If 'Infill in Direction of Bridges'  is selected, the infill will be in the direction of bridges across gaps, so that the fill will be able to span a
bridge easier.

The 'Extra Decimal Places' is the number of extra decimal places export will output compared to the number of decimal places in the
layer thickness.  The higher the 'Extra Decimal Places', the more significant figures the output numbers will have, the default is one.

Carve slices from bottom to top.  The output will go from the "Layers From" index to the "Layers To" index.  The default for the
"Layers From" index is zero and the default for the "Layers To" is a really big number.  To get a single layer, set the "Layers From"
to zero and the "Layers To" to one.

To run carve, in a shell type:
> python carve.py

The following examples carve the file Screw Holder Bottom.stl.  The examples are run in a terminal in the folder which contains
Screw Holder Bottom.stl and carve.py.  The preferences can be set in the dialog or by changing the preferences file 'carve.csv'
with a text editor or a spreadsheet program set to separate tabs.


> python carve.py
This brings up the dialog, after clicking 'Carve', the following is printed:
File Screw Holder Bottom.stl is being carved.
The carved file is saved as Screw Holder Bottom_carve.svg


>python
Python 2.5.1 (r251:54863, Sep 22 2007, 01:43:31)
[GCC 4.2.1 (SUSE Linux)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import carve
>>> carve.main()
File Screw Holder Bottom.stl is being carved.
The carved file is saved as Screw Holder Bottom_carve.svg
It took 3 seconds to carve the file.


>>> carve.writeOutput()
File Screw Holder Bottom.gcode is being carved.
The carved file is saved as Screw Holder Bottom_carve.svg
It took 3 seconds to carve the file.

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
from skeinforge_tools.skeinforge_utilities import interpret
from skeinforge_tools.skeinforge_utilities import preferences
from skeinforge_tools.skeinforge_utilities import svg_codec
from skeinforge_tools.skeinforge_utilities import triangle_mesh
from skeinforge_tools import polyfile
import math
import os
import sys
import time


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/02/05 $"
__license__ = "GPL 3.0"


def getCarving( fileName ):
	"Get a carving for the file using an import plugin."
	importPluginFilenames = interpret.getImportPluginFilenames()
	for importPluginFilename in importPluginFilenames:
		fileTypeDot = '.' + importPluginFilename
		if fileName[ - len( fileTypeDot ) : ].lower() == fileTypeDot:
			pluginModule = gcodec.getModule( importPluginFilename, 'import_plugins', os.path.dirname( __file__ ) )
			if pluginModule != None:
				return pluginModule.getCarving( fileName )
	print( 'Could not find plugin to handle ' + fileName )
	return None

def getCraftedText( fileName, text = '', carvePreferences = None ):
	"Get carved text."
	if gcodec.getHasSuffix( fileName, '.svg' ):
		if text == '':
			text = gcodec.getFileText( fileName )
		return text
	return getCraftedTextFromFileName( fileName, carvePreferences = None )

def getCraftedTextFromFileName( fileName, carvePreferences = None ):
	"Carve a shape file."
	carving = getCarving( fileName )
	if carving == None:
		return ''
	if carvePreferences == None:
		carvePreferences = CarvePreferences()
		preferences.getReadPreferences( carvePreferences )
	return CarveSkein().getCarvedSVG( carvePreferences, carving, fileName )

def getPreferencesConstructor():
	"Get the preferences constructor."
	return CarvePreferences()

def writeOutput( fileName = '' ):
	"Carve a GNU Triangulated Surface file.  If no fileName is specified, carve the first GNU Triangulated Surface file in this folder."
	if fileName == '':
		unmodified = gcodec.getFilesWithFileTypesWithoutWords( interpret.getImportPluginFilenames() )
		if len( unmodified ) == 0:
			print( "There are no carvable files in this folder." )
			return
		fileName = unmodified[ 0 ]
	startTime = time.time()
	print( 'File ' + gcodec.getSummarizedFilename( fileName ) + ' is being carved.' )
	carveGcode = getCraftedText( fileName )
	if carveGcode == '':
		return
	suffixFilename = fileName[ : fileName.rfind( '.' ) ] + '_carve.svg'
	suffixDirectoryName = os.path.dirname( suffixFilename )
	suffixReplacedBaseName = os.path.basename( suffixFilename ).replace( ' ', '_' )
	suffixFilename = os.path.join( suffixDirectoryName, suffixReplacedBaseName )
	gcodec.writeFileText( suffixFilename, carveGcode )
	print( 'The carved file is saved as ' + gcodec.getSummarizedFilename( suffixFilename ) )
	print( 'It took ' + str( int( round( time.time() - startTime ) ) ) + ' seconds to carve the file.' )
	preferences.openWebPage( suffixFilename )


class CarvePreferences:
	"A class to handle the carve preferences."
	def __init__( self ):
		"Set the default preferences, execute title & preferences fileName."
		#Set the default preferences.
		self.archive = []
		self.fileNameInput = preferences.Filename().getFromFilename( interpret.getTranslatorFileTypeTuples(), 'Open File to be Carved', '' )
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
		self.infillBridgeThicknessOverLayerThickness = preferences.FloatPreference().getFromValue( 'Infill Bridge Thickness over Layer Thickness (ratio):', 1.0 )
		self.archive.append( self.infillBridgeThicknessOverLayerThickness )
		self.infillDirectionBridge = preferences.BooleanPreference().getFromValue( 'Infill in Direction of Bridges', True )
		self.archive.append( self.infillDirectionBridge )
		self.layerThickness = preferences.FloatPreference().getFromValue( 'Layer Thickness (mm):', 0.4 )
		self.archive.append( self.layerThickness )
		self.layersFrom = preferences.IntPreference().getFromValue( 'Layers From (index):', 0 )
		self.archive.append( self.layersFrom )
		self.layersTo = preferences.IntPreference().getFromValue( 'Layers To (index):', 999999999 )
		self.archive.append( self.layersTo )
		self.perimeterWidthOverThickness = preferences.FloatPreference().getFromValue( 'Perimeter Width over Thickness (ratio):', 1.8 )
		self.archive.append( self.perimeterWidthOverThickness )
		#Create the archive, title of the execute button, title of the dialog & preferences fileName.
		self.executeTitle = 'Carve'
		self.saveCloseTitle = 'Save and Close'
		preferences.setHelpPreferencesFileNameTitleWindowPosition( self, 'skeinforge_tools.craft_plugins.carve.html' )

	def execute( self ):
		"Carve button has been clicked."
		fileNames = polyfile.getFileOrDirectoryTypes( self.fileNameInput.value, interpret.getImportPluginFilenames(), self.fileNameInput.wasCancelled )
		for fileName in fileNames:
			writeOutput( fileName )


class CarveSkein( svg_codec.SVGCodecSkein ):
	"A class to carve a carving."
	def addRotatedLoopLayersToOutput( self, rotatedBoundaryLayers ):
		"Add rotated boundary layers to the output."
		truncatedRotatedBoundaryLayers = rotatedBoundaryLayers[ self.carvePreferences.layersFrom.value : self.carvePreferences.layersTo.value ]
		for truncatedRotatedBoundaryLayerIndex in xrange( len( truncatedRotatedBoundaryLayers ) ):
			truncatedRotatedBoundaryLayer = truncatedRotatedBoundaryLayers[ truncatedRotatedBoundaryLayerIndex ]
			self.addRotatedLoopLayerToOutput( truncatedRotatedBoundaryLayerIndex, truncatedRotatedBoundaryLayer )

	def addRotatedLoopLayerToOutput( self, layerIndex, rotatedBoundaryLayer ):
		"Add rotated boundary layer to the output."
		self.addLayerStart( layerIndex, rotatedBoundaryLayer.z )
		if rotatedBoundaryLayer.rotation != None:
			self.addLine('\t\t\t<!--bridgeRotation--> %s' % rotatedBoundaryLayer.rotation ) # Indicate the bridge rotation.
#			<path transform="scale(3.7, -3.7) translate(0, 5)" d="M 0 -5 L 50 0 L60 50 L 5 50 z M 5 3 L5 15 L15 15 L15 5 z"/>
#		transform = 'scale(' + unitScale + ' ' + (unitScale * -1) + ') translate(' + (sliceMinX * -1) + ' ' + (sliceMinY * -1) + ')'
		pathString = '\t\t\t<path transform="scale(%s, %s) translate(%s, %s)" d="' % ( self.unitScale, - self.unitScale, self.getRounded( - self.cornerMinimum.x ), self.getRounded( - self.cornerMinimum.y ) )
		if len( rotatedBoundaryLayer.loops ) > 0:
			pathString += self.getSVGLoopString( rotatedBoundaryLayer.loops[ 0 ] )
		for loop in rotatedBoundaryLayer.loops[ 1 : ]:
			pathString += ' ' + self.getSVGLoopString( loop )
		pathString += '"/>'
		self.addLine( pathString )
		self.addLine( '\t\t</g>' )

	def getCarvedSVG( self, carvePreferences, carving, fileName ):
		"Parse gnu triangulated surface text and store the carved gcode."
		self.carvePreferences = carvePreferences
		self.layerThickness = carvePreferences.layerThickness.value
		self.setExtrusionDiameterWidth( carvePreferences )
		if carvePreferences.infillDirectionBridge.value:
			carving.setCarveBridgeLayerThickness( self.bridgeLayerThickness )
		carving.setCarveLayerThickness( self.layerThickness )
		importRadius = 0.5 * carvePreferences.importCoarseness.value * abs( self.perimeterWidth )
		carving.setCarveImportRadius( max( importRadius, 0.01 * self.layerThickness ) )
		carving.setCarveIsCorrectMesh( carvePreferences.correctMesh.value )
		rotatedBoundaryLayers = carving.getCarveRotatedBoundaryLayers()
		if len( rotatedBoundaryLayers ) < 1:
			return ''
		self.cornerMaximum = carving.getCarveCornerMaximum()
		self.cornerMinimum = carving.getCarveCornerMinimum()
		#reset from slicable
		self.layerThickness = carving.getCarveLayerThickness()
		self.setExtrusionDiameterWidth( carvePreferences )
		self.decimalPlacesCarried = max( 0, 1 + carvePreferences.extraDecimalPlaces.value - int( math.floor( math.log10( self.layerThickness ) ) ) )
		self.extent = self.cornerMaximum - self.cornerMinimum
		self.svgTemplateLines = self.getReplacedSVGTemplateLines( fileName, rotatedBoundaryLayers )
		self.addInitializationToOutputSVG( 'carve' )
		self.addRotatedLoopLayersToOutput( rotatedBoundaryLayers )
		self.addShutdownToOutput()
		return self.output.getvalue()

	def setExtrusionDiameterWidth( self, carvePreferences ):
		"Set the extrusion diameter & width and the bridge thickness & width."
		self.bridgeLayerThickness = self.layerThickness * carvePreferences.infillBridgeThicknessOverLayerThickness.value
		self.perimeterWidth = carvePreferences.perimeterWidthOverThickness.value * self.layerThickness


def main():
	"Display the carve dialog."
	if len( sys.argv ) > 1:
		writeOutput( ' '.join( sys.argv[ 1 : ] ) )
	else:
		preferences.startMainLoopFromConstructor( getPreferencesConstructor() )

if __name__ == "__main__":
	main()

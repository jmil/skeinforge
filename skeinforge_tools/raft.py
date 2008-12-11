"""
Raft is a script to create a reusable raft, elevate the nozzle and set the temperature.

The default 'Activate Raft' checkbox is on.  When it is on, the functions described below will work, when it is off, the
functions will not be called.  The raft script sets the temperature.  If the "Activate Raft, Elevate Nozzle, Orbit and Set
Altitude" checkbox is checked, the script will also create a raft, elevate the nozzle, orbit and set the altitude of the bottom
of the raft.

Raft is based on the Nophead's reusable raft, which has a base layer running one way, and a couple of perpendicular layers
above.  Each set of layers can be set to a different temperature.  There is the option of having the extruder orbit the raft for a
while, so the heater barrel has time to reach a different temperature, without ooze accumulating around the nozzle.  To run
raft, in a shell type:
> python raft.py

The important values for the raft preferences are the temperatures of the raft, the first layer and the next layers.  These will be
different for each material.  The default preferences for ABS, HDPE, PCL & PLA are extrapolated from Nophead's
experiments.  To change the material, in a shell type:
> python material.py

This brings up the material preferences dialog.  In that dialog you can add or delete a material on the listbox and you change
the selected material.  After you can change the selected material, run raft again.  If there are preferences for the new material,
those will be in the raft dialog.  If there are no preferences for the new material, the preferences will be set to defaults and you
will have to set new preferences for the new material.

The "Base Infill Density" preference is the infill density ratio of the base of the raft, the default ratio is half.  The "Base Layer
Height over Extrusion Height" preference is the ratio of the height & width of the base layer compared to the height and width
of the shape infill, the default is two.  The feedrate will be slower for raft layers which have thicker extrusions than the shape
infill.  The "Base Layers" preference is the number of base layers, the default is one.  The "Base Nozzle Lift over Half Base
Extrusion Height" is the amount the nozzle is above the center of the extrusion divided by half the base extrusion height.

The interface of the raft has equivalent preferences called "Interface Infill Density", "Interface Layer Height over Extrusion
Height", "Interface Layers" and "Interface Nozzle Lift over Half Base Extrusion Height".  The shape has the equivalent
preference of called "Operating Nozzle Lift over Half Extrusion Height".

The altitude that the bottom of the raft will be set to the "Bottom Altitude" preference.

The raft fills a rectangle whose size is the rectangle around the bottom layer of the shape expanded on each side by the
"Raft Outset Radius over Extrusion Width" preference times the extrusion width, minus the "Infill Overhang" ratio times the
width of the extrusion of the raft.

In the "Support Material Choice" radio button group, if "No Support Material" is selected then raft will not add support
material, this is the default because the raft takes time to generate.  If "Support Material Everywhere" is selected, support
material will be added wherever there are overhangs, even inside the object; because support material inside objects is hard
or impossible to remove, this option should only be chosen if the shape has a cavity that needs support and there is some
way to extract the support material.  If "Support Material on Exterior Only" is selected, support material will be added only
the exterior of the object; this is the best option for most objects which require support material.  The "Support Minimum
Angle" preference is the minimum angle that a surface overhangs before support material is added, the default is sixty
degrees. The "Support Inset over Perimeter Extrusion Width" is the amount that the support material is inset into the object
over the perimeter extrusion width, the default is zero.

The extruder will orbit for at least "Temperature Change Time Before Raft" seconds before extruding the raft.  It will orbit for
at least "Temperature Change Time Before First Layer Outline" seconds before extruding the outline of the first layer of the
shape.  It will orbit for at least "Temperature Change Time Before Next Threads" seconds before extruding within the outline
of the first layer of the shape and before extruding the next layers of the shape.  It will orbit for at least "Temperature
Change Time Before Support Layers" seconds before extruding the support layers.  It will orbit for at least "Temperature
Change Time Before Supported Layers" seconds before extruding the layer of the shape above the support layer.  If a time
is zero, it will not orbit.

The "Temperature of Raft" preference sets the temperature of the raft.  The "Temperature of Shape First Layer Outline"
preference sets the temperature of the outline of the first layer of the shape.  The "Temperature of Shape First Layer Within"
preference sets the temperature within the outline of the first layer of the shape.  The "Temperature of Shape Next Layers"
preference sets the temperature of the next layers of the shape.  The "Temperature of Support Layers" preference sets the
temperature of the support layer.  The "Temperature of Supported Layers" preference sets the temperature of the layer of the
shape above the support layer.

If the "Turn Extruder On Early" checkbox is checked, the extruder will be turned on before the first layer is extruded.  Now that
oozebane turns on the extruder just before a thread begins, the "Turn Extruder On Early" option is probably not necesary so the
default is now off.

The following examples raft the files Hollow Square.gcode & Hollow Square.gts.  The examples are run in a terminal in the folder
which contains Hollow Square.gcode, Hollow Square.gts and raft.py.  The raft function will raft if "Activate Raft, Elevate Nozzle,
Orbit and Set Altitude" is true, which can be set in the dialog or by changing the preferences file 'raft.csv' with a text editor or a
spreadsheet program set to separate tabs.  The functions writeOutput and getRaftChainGcode check to see if the text has
been rafted, if not they call getSpeedChainGcode in speed.py to get speeded gcode; once they have the speeded text, then
they raft.  Pictures of rafting in action are available from the Metalab blog at:
http://reprap.soup.io/?search=rafting


> python raft.py
This brings up the dialog, after clicking 'Raft', the following is printed:
File Hollow Square.gts is being chain rafted.
The rafted file is saved as Hollow Square_raft.gcode


>python
Python 2.5.1 (r251:54863, Sep 22 2007, 01:43:31)
[GCC 4.2.1 (SUSE Linux)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import raft
>>> raft.main()
This brings up the raft dialog.


>>> raft.writeOutput()
Hollow Square.gts
File Hollow Square.gts is being chain rafted.
The rafted file is saved as Hollow Square_raft.gcode


>>> raft.getRaftGcode("
( GCode generated by May 8, 2008 slice.py )
( Extruder Initialization )
..
many lines of gcode
..
")


>>> raft.getRaftChainGcode("
( GCode generated by May 8, 2008 slice.py )
( Extruder Initialization )
..
many lines of gcode
..
")

"""

from __future__ import absolute_import
#Init has to be imported first because it has code to workaround the python bug where relative imports don't work if the module is imported as a main module.
import __init__

from skeinforge_tools.skeinforge_utilities.vec3 import Vec3
from skeinforge_tools.skeinforge_utilities import euclidean
from skeinforge_tools.skeinforge_utilities import gcodec
from skeinforge_tools.skeinforge_utilities import intercircle
from skeinforge_tools.skeinforge_utilities import preferences
from skeinforge_tools import analyze
from skeinforge_tools import import_translator
from skeinforge_tools import material
from skeinforge_tools import polyfile
from skeinforge_tools import speed
import cStringIO
import math
import sys
import time


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


#maybe later wide support
def addXIntersectionsFromSegment( index, segment, xIntersectionIndexList ):
	"Add the x intersections from the segment."
	for endpoint in segment:
		xIntersectionIndexList.append( euclidean.XIntersectionIndex( index, endpoint.point.x ) )

def addXIntersectionsFromSegments( index, segments, xIntersectionIndexList ):
	"Add the x intersections from the segments."
	for segment in segments:
		addXIntersectionsFromSegment( index, segment, xIntersectionIndexList )

def getEndpointsFromSegments( segments ):
	"Get the endpoints from the segments."
	endpoints = []
	for segment in segments:
		for endpoint in segment:
			endpoints.append( endpoint )
	return endpoints

def getExtendedLineSegment( extensionDistance, lineSegment ):
	"Add shortened line segment."
	pointBegin = lineSegment[ 0 ].point
	pointEnd = lineSegment[ 1 ].point
	segment = pointEnd.minus( pointBegin )
	segmentLength = segment.lengthXYPlane()
	if segmentLength <= 0.0 * extensionDistance:
		print( "This should never happen in getExtendedLineSegment in raft, the segment should have a length greater than zero." )
		print( lineSegment )
		return None
	segmentExtend = segment.times( extensionDistance / segmentLength )
	lineSegment[ 0 ].point = pointBegin.minus( segmentExtend )
	lineSegment[ 1 ].point = pointEnd.plus( segmentExtend )
	return lineSegment

def getFillXIntersectionIndexes( fillLoops, y ):
	"Get fill x intersection indexes inside loops."
	xIntersectionIndexList = []
	euclidean.addXIntersectionIndexesFromLoops( fillLoops, 0, xIntersectionIndexList, y )
	return xIntersectionIndexList

def getHorizontalSegments( fillLoops, alreadyFilledArounds, y, z ):
	"Get horizontal segments inside loops."
	xIntersectionIndexList = []
	euclidean.addXIntersectionIndexesFromLoops( fillLoops, - 1, xIntersectionIndexList, y )
	euclidean.addXIntersectionIndexesFromLoops( alreadyFilledArounds, 0, xIntersectionIndexList, y )
	return euclidean.getSegmentsFromXIntersectionIndexes( xIntersectionIndexList, y, z )

def getJoinOfXIntersectionIndexes( xIntersectionIndexList ):
	"Get x intersections from surrounding layers."
	xIntersectionList = []
	solidTable = {}
	solid = False
	xIntersectionIndexList.sort()
	for xIntersectionIndex in xIntersectionIndexList:
		euclidean.toggleHashtable( solidTable, xIntersectionIndex.index, "" )
		oldSolid = solid
		solid = len( solidTable ) > 0
		if oldSolid != solid:
			xIntersectionList.append( xIntersectionIndex.x )
	return xIntersectionList

#raft outline temperature http://hydraraptor.blogspot.com/2008/09/screw-top-pot.html
def getRaftChainGcode( filename, gcodeText, raftPreferences = None ):
	"Raft a gcode linear move text.  Chain raft the gcode if it is not already rafted."
	gcodeText = gcodec.getGcodeFileText( filename, gcodeText )
	if not gcodec.isProcedureDone( gcodeText, 'speed' ):
		gcodeText = speed.getSpeedChainGcode( filename, gcodeText )
	return getRaftGcode( gcodeText, raftPreferences )

def getRaftGcode( gcodeText, raftPreferences = None ):
	"Raft a gcode linear move text."
	if gcodeText == '':
		return ''
	if gcodec.isProcedureDone( gcodeText, 'raft' ):
		return gcodeText
	if raftPreferences == None:
		raftPreferences = RaftPreferences()
		preferences.readPreferences( raftPreferences )
	if not raftPreferences.activateRaft.value:
		return gcodeText
	skein = RaftSkein()
	skein.parseGcode( gcodeText, raftPreferences )
	return skein.output.getvalue()

def getSquareLoop( beginComplex, endComplex, z ):
	"Get a square loop from the beginning to the end and back."
	loop = [ Vec3( beginComplex.real, beginComplex.imag, z ) ]
	loop.append( Vec3( beginComplex.real, endComplex.imag, z ) )
	loop.append( Vec3( endComplex.real, endComplex.imag, z ) )
	loop.append( Vec3( endComplex.real, beginComplex.imag, z ) )
	return loop

def joinSegmentTables( fromTable, intoTable, z ):
	"Join both segment tables and put the join into the intoTable."
	intoTableKeys = intoTable.keys()
	fromTableKeys = fromTable.keys()
	joinedKeyTable = {}
	concatenatedSegmentTableKeys = intoTableKeys + fromTableKeys
	for concatenatedSegmentTableKey in concatenatedSegmentTableKeys:
		joinedKeyTable[ concatenatedSegmentTableKey ] = None
	joinedKeys = joinedKeyTable.keys()
	joinedKeys.sort()
	joinedSegmentTable = {}
	for joinedKey in joinedKeys:
		xIntersectionIndexList = []
		if joinedKey in intoTable:
			addXIntersectionsFromSegments( 0, intoTable[ joinedKey ], xIntersectionIndexList )
		if joinedKey in fromTable:
			addXIntersectionsFromSegments( 1, fromTable[ joinedKey ], xIntersectionIndexList )
		xIntersections = getJoinOfXIntersectionIndexes( xIntersectionIndexList )
		lineSegments = euclidean.getSegmentsFromXIntersections( xIntersections, joinedKey, z )
		if len( lineSegments ) > 0:
			intoTable[ joinedKey ] = lineSegments
		else:
			print( "This should never happen, there are no line segments in joinSegments in raft." )

def subtractFill( fillXIntersectionIndexTable, supportLayerTable ):
	"Subtract fill from the support layer table."
	supportLayerTableKeys = supportLayerTable.keys()
	supportLayerTableKeys.sort()
	if len( supportLayerTableKeys ) < 1:
		return
	firstSegments = supportLayerTable[ supportLayerTableKeys[ 0 ] ]
	if len( firstSegments ) < 1:
		print( "This should never happen in subtractFill in raft, there are no segments in the first support layer table value." )
		return
	z = firstSegments[ 0 ][ 0 ].point.z
	for supportLayerTableKey in supportLayerTableKeys:
		xIntersectionIndexList = []
		addXIntersectionsFromSegments( - 1, supportLayerTable[ supportLayerTableKey ], xIntersectionIndexList )
		if supportLayerTableKey in fillXIntersectionIndexTable:
			addXIntersectionsFromSegments( 0, fillXIntersectionIndexTable[ supportLayerTableKey ], xIntersectionIndexList )
		lineSegments = euclidean.getSegmentsFromXIntersectionIndexes( xIntersectionIndexList, supportLayerTableKey, z )
		if len( lineSegments ) > 0:
			supportLayerTable[ supportLayerTableKey ] = lineSegments
		else:
			del supportLayerTable[ supportLayerTableKey ]

def writeOutput( filename = '' ):
	"""Raft a gcode linear move file.  Chain raft the gcode if it is not already rafted.
	If no filename is specified, raft the first unmodified gcode file in this folder."""
	if filename == '':
		unmodified = import_translator.getGNUTranslatorFilesUnmodified()
		if len( unmodified ) == 0:
			print( "There are no unmodified gcode files in this folder." )
			return
		filename = unmodified[ 0 ]
	raftPreferences = RaftPreferences()
	preferences.readPreferences( raftPreferences )
	startTime = time.time()
	print( 'File ' + gcodec.getSummarizedFilename( filename ) + ' is being chain rafted.' )
	suffixFilename = filename[ : filename.rfind( '.' ) ] + '_raft.gcode'
	raftGcode = getRaftChainGcode( filename, '', raftPreferences )
	if raftGcode == '':
		return
	gcodec.writeFileText( suffixFilename, raftGcode )
	print( 'The rafted file is saved as ' + gcodec.getSummarizedFilename( suffixFilename ) )
	analyze.writeOutput( suffixFilename, raftGcode )
	print( 'It took ' + str( int( round( time.time() - startTime ) ) ) + ' seconds to raft the file.' )


class RaftPreferences:
	"A class to handle the raft preferences."
	def __init__( self ):
		"Set the default preferences, execute title & preferences filename."
		materialName = material.getSelectedMaterial()
		#Set the default preferences.
		self.archive = []
		self.activateRaft = preferences.BooleanPreference().getFromValue( 'Activate Raft:', True )
		self.archive.append( self.activateRaft )
		self.addRaftElevateNozzleOrbitSetAltitude = preferences.BooleanPreference().getFromValue( 'Add Raft, Elevate Nozzle, Orbit and Set Altitude:', True )
		self.archive.append( self.addRaftElevateNozzleOrbitSetAltitude )
		self.baseInfillDensity = preferences.FloatPreference().getFromValue( 'Base Infill Density (ratio):', 0.5 )
		self.archive.append( self.baseInfillDensity )
		self.baseLayerHeightOverExtrusionHeight = preferences.FloatPreference().getFromValue( 'Base Layer Height over Extrusion Height:', 2.0 )
		self.archive.append( self.baseLayerHeightOverExtrusionHeight )
		self.baseLayers = preferences.IntPreference().getFromValue( 'Base Layers (integer):', 1 )
		self.archive.append( self.baseLayers )
		self.baseNozzleLiftOverHalfBaseExtrusionHeight = preferences.FloatPreference().getFromValue( 'Base Nozzle Lift over Half Base Extrusion Height (ratio):', 0.75 )
		self.archive.append( self.baseNozzleLiftOverHalfBaseExtrusionHeight )
		self.bottomAltitude = preferences.FloatPreference().getFromValue( 'Bottom Altitude:', 0.0 )
		self.archive.append( self.bottomAltitude )
		self.filenameInput = preferences.Filename().getFromFilename( import_translator.getGNUTranslatorGcodeFileTypeTuples(), 'Open File to be Rafted', '' )
		self.archive.append( self.filenameInput )
		self.infillOverhang = preferences.FloatPreference().getFromValue( 'Infill Overhang (ratio):', 0.1 )
		self.archive.append( self.infillOverhang )
		self.interfaceInfillDensity = preferences.FloatPreference().getFromValue( 'Interface Infill Density (ratio):', 0.5 )
		self.archive.append( self.interfaceInfillDensity )
		self.interfaceLayerHeightOverExtrusionHeight = preferences.FloatPreference().getFromValue( 'Interface Layer Height over Extrusion Height:', 1.0 )
		self.archive.append( self.interfaceLayerHeightOverExtrusionHeight )
		self.interfaceLayers = preferences.IntPreference().getFromValue( 'Interface Layers (integer):', 2 )
		self.archive.append( self.interfaceLayers )
		self.interfaceNozzleLiftOverHalfInterfaceExtrusionHeight = preferences.FloatPreference().getFromValue( 'Interface Nozzle Lift over Half Interface Extrusion Height (ratio):', 1.0 )
		self.archive.append( self.interfaceNozzleLiftOverHalfInterfaceExtrusionHeight )
		self.material = preferences.LabelDisplay().getFromName( 'Material: ' + materialName )
		self.archive.append( self.material )
		self.operatingNozzleLiftOverHalfExtrusionHeight = preferences.FloatPreference().getFromValue( 'Operating Nozzle Lift over Half Extrusion Height (ratio):', 1.0 )
		self.archive.append( self.operatingNozzleLiftOverHalfExtrusionHeight )
		self.raftOutsetRadiusOverExtrusionWidth = preferences.FloatPreference().getFromValue( 'Raft Outset Radius over Extrusion Width (ratio):', 15.0 )
		self.archive.append( self.raftOutsetRadiusOverExtrusionWidth )
		self.supportInsetOverPerimeterExtrusionWidth = preferences.FloatPreference().getFromValue( 'Support Inset over Perimeter Extrusion Width (ratio):', 0.0 )
		self.archive.append( self.supportInsetOverPerimeterExtrusionWidth )
		supportRadio = []
		self.supportChoiceLabel = preferences.LabelDisplay().getFromName( 'Support Material Choice: ' )
		self.archive.append( self.supportChoiceLabel )
		self.supportChoiceNoSupportMaterial = preferences.Radio().getFromRadio( 'No Support Material', supportRadio, True )
		self.archive.append( self.supportChoiceNoSupportMaterial )
		self.supportChoiceSupportMateriaEverywhere = preferences.Radio().getFromRadio( 'Support Material Everywhere', supportRadio, False )
		self.archive.append( self.supportChoiceSupportMateriaEverywhere )
		self.supportChoiceSupportMaterialOnExteriorOnly = preferences.Radio().getFromRadio( 'Support Material on Exterior Only', supportRadio, False )
		self.archive.append( self.supportChoiceSupportMaterialOnExteriorOnly )
		self.supportMinimumAngle = preferences.FloatPreference().getFromValue( 'Support Minimum Angle (degrees):', 60.0 )
		self.archive.append( self.supportMinimumAngle )
		self.temperatureChangeBeforeTimeRaft = preferences.FloatPreference().getFromValue( 'Temperature Change Time Before Raft (seconds):', 120.0 )
		self.archive.append( self.temperatureChangeBeforeTimeRaft )
		self.temperatureChangeTimeBeforeFirstLayerOutline = preferences.FloatPreference().getFromValue( 'Temperature Change Time Before First Layer Outline (seconds):', 120.0 )
		self.archive.append( self.temperatureChangeTimeBeforeFirstLayerOutline )
		self.temperatureChangeTimeBeforeNextThreads = preferences.FloatPreference().getFromValue( 'Temperature Change Time Before Next Threads (seconds):', 120.0 )
		self.archive.append( self.temperatureChangeTimeBeforeNextThreads )
		self.temperatureChangeTimeBeforeSupportLayers = preferences.FloatPreference().getFromValue( 'Temperature Change Time Before Support Layers (seconds):', 120.0 )
		self.archive.append( self.temperatureChangeTimeBeforeSupportLayers )
		self.temperatureChangeTimeBeforeSupportedLayers = preferences.FloatPreference().getFromValue( 'Temperature Change Time Before Supported Layers (seconds):', 120.0 )
		self.archive.append( self.temperatureChangeTimeBeforeSupportedLayers )
		self.temperatureRaft = preferences.FloatPreference().getFromValue( 'Temperature of Raft (Celcius):', 200.0 )
		self.archive.append( self.temperatureRaft )
		self.temperatureShapeFirstLayerOutline = preferences.FloatPreference().getFromValue( 'Temperature of Shape First Layer Outline (Celcius):', 220.0 )
		self.archive.append( self.temperatureShapeFirstLayerOutline )
		self.temperatureShapeFirstLayerWithin = preferences.FloatPreference().getFromValue( 'Temperature of Shape First Layer Within (Celcius):', 195.0 )
		self.archive.append( self.temperatureShapeFirstLayerWithin )
		self.temperatureShapeNextLayers = preferences.FloatPreference().getFromValue( 'Temperature of Shape Next Layers (Celcius):', 230.0 )
		self.archive.append( self.temperatureShapeNextLayers )
		self.temperatureShapeSupportLayers = preferences.FloatPreference().getFromValue( 'Temperature of Support Layers (Celcius):', 200.0 )
		self.archive.append( self.temperatureShapeSupportLayers )
		self.temperatureShapeSupportedLayers = preferences.FloatPreference().getFromValue( 'Temperature of Supported Layers (Celcius):', 230.0 )
		self.archive.append( self.temperatureShapeSupportedLayers )
		self.turnExtruderOnEarly = preferences.BooleanPreference().getFromValue( 'Turn Extruder On Early:', False )
		self.archive.append( self.turnExtruderOnEarly )
		#Create the archive, title of the execute button, title of the dialog & preferences filename.
		self.executeTitle = 'Raft'
		self.filenamePreferences = preferences.getPreferencesFilePath( 'raft_' + materialName + '.csv' )
		self.filenameHelp = 'skeinforge_tools.raft.html'
		self.saveTitle = 'Save Preferences'
		self.title = 'Raft Preferences'

	def execute( self ):
		"Raft button has been clicked."
		filenames = polyfile.getFileOrDirectoryTypesUnmodifiedGcode( self.filenameInput.value, import_translator.getGNUTranslatorFileTypes(), self.filenameInput.wasCancelled )
		for filename in filenames:
			writeOutput( filename )


class RaftSkein:
	"A class to raft a skein of extrusions."
	def __init__( self ):
		self.boundaryLayers = []
		self.cornerHigh = Vec3( - 999999999.0, - 999999999.0, - 999999999.0 )
		self.cornerLow = Vec3( 999999999.0, 999999999.0, 999999999.0 )
		self.decimalPlacesCarried = 3
		self.extrusionHeight = 0.4
		self.extrusionStart = True
		self.extrusionTop = 0.0
		self.extrusionWidth = 0.6
		self.feedrateMinute = 961.0
		self.interfaceStepsUntilEnd = []
		self.isFirstLayerWithinTemperatureAdded = False
		self.isStartupEarly = False
		self.isSurroundingLoop = True
		self.layerIndex = - 1
		self.lineIndex = 0
		self.lines = None
		self.oldLocation = None
		self.operatingLayerEndLine = '(<operatingLayerEnd> )'
		self.operatingJump = None
		self.output = cStringIO.StringIO()
		self.supportLayers = []
		self.supportLayerTables = []

	def addBaseLayer( self, baseExtrusionWidth, baseStep, stepBegin, stepEnd ):
		"Add a base layer."
		baseExtrusionHeight = self.extrusionHeight * self.baseLayerHeightOverExtrusionHeight
		halfBaseExtrusionHeight = 0.5 * baseExtrusionHeight
		halfBaseExtrusionWidth = 0.5 * baseExtrusionWidth
		stepsUntilEnd = self.getStepsUntilEnd( stepBegin.real + halfBaseExtrusionWidth, stepEnd.real, baseStep )
		baseOverhang = self.raftPreferences.infillOverhang.value * halfBaseExtrusionWidth - halfBaseExtrusionWidth
		beginY = stepBegin.imag - baseOverhang
		endY = stepEnd.imag + baseOverhang
		segments = []
		zCenter = self.extrusionTop + halfBaseExtrusionHeight
		z = zCenter + halfBaseExtrusionHeight * self.raftPreferences.baseNozzleLiftOverHalfBaseExtrusionHeight.value
		for x in stepsUntilEnd:
			begin = Vec3( x, beginY, z )
			end = Vec3( x, endY, z )
			segments.append( euclidean.getSegmentFromPoints( begin, end ) )
		if len( segments ) < 1:
			print( 'This should never happen, the base layer has a size of zero.' )
			return
		self.addLayerFromSegments( self.feedrateMinute / self.baseLayerHeightOverExtrusionHeight / self.baseLayerHeightOverExtrusionHeight, baseExtrusionHeight, segments, zCenter )

	def addGcodeFromFeedrateThread( self, feedrateMinute, thread ):
		"Add a thread to the output."
		if len( thread ) > 0:
			self.addGcodeFromFeedrateMovement( feedrateMinute, thread[ 0 ] )
		else:
			print( "zero length vertex positions array which was skipped over, this should never happen" )
		if len( thread ) < 2:
			return
		self.addLine( "M101" ) # Turn extruder on.
		for point in thread[ 1 : ]:
			self.addGcodeFromFeedrateMovement( feedrateMinute, point )
		self.addLine( "M103" ) # Turn extruder off.

	def addGcodeFromFeedrateMovement( self, feedrateMinute, point ):
		"Add a movement to the output."
		self.addLine( self.getGcodeFromFeedrateMovement( feedrateMinute, point ) )

	def addInterfaceLayer( self ):
		"Add an interface layer."
		interfaceExtrusionHeight = self.extrusionHeight * self.interfaceLayerHeightOverExtrusionHeight
		halfInterfaceExtrusionHeight = 0.5 * interfaceExtrusionHeight
		segments = []
		zCenter = self.extrusionTop + halfInterfaceExtrusionHeight
		z = zCenter + halfInterfaceExtrusionHeight * self.raftPreferences.interfaceNozzleLiftOverHalfInterfaceExtrusionHeight.value
		for y in self.interfaceStepsUntilEnd:
			begin = Vec3( self.interfaceBeginX, y, z )
			end = Vec3( self.interfaceEndX, y, z )
			segments.append( euclidean.getSegmentFromPoints( begin, end ) )
		if len( segments ) < 1:
			print( 'This should never happen, the interface layer has a size of zero.' )
			return
		self.addLayerFromSegments( self.feedrateMinute / self.interfaceLayerHeightOverExtrusionHeight / self.interfaceLayerHeightOverExtrusionHeight, interfaceExtrusionHeight, segments, zCenter )

	def addLayerFromSegments( self, feedrateMinute, layerExtrusionHeight, segments, zCenter ):
		"Add a layer from segments and raise the extrusion top."
		firstSegment = segments[ 0 ]
		nearestPoint = firstSegment[ 1 ].point
		path = [ firstSegment[ 0 ].point, nearestPoint ]
		for segment in segments[ 1 : ]:
			segmentBegin = segment[ 0 ]
			segmentEnd = segment[ 1 ]
			nextEndpoint = segmentBegin
			if nearestPoint.distance2( segmentBegin.point ) > nearestPoint.distance2( segmentEnd.point ):
				nextEndpoint = segmentEnd
			path.append( nextEndpoint.point )
			nextEndpoint = nextEndpoint.otherEndpoint
			nearestPoint = nextEndpoint.point
			path.append( nearestPoint )
		self.addLine( '(<layerStart> ' + self.getRounded( zCenter ) + ' )' ) # Indicate that a new layer is starting.
		self.addGcodeFromFeedrateThread( feedrateMinute, path )
		self.extrusionTop += layerExtrusionHeight

	def addLine( self, line ):
		"Add a line of text and a newline to the output."
		if len( line ) > 0:
			self.output.write( line + "\n" )

	def addRaft( self ):
		self.extrusionTop = self.raftPreferences.bottomAltitude.value
		complexRadius = complex( self.raftOutsetRadius, self.raftOutsetRadius )
		self.baseLayerHeightOverExtrusionHeight = self.raftPreferences.baseLayerHeightOverExtrusionHeight.value
		baseExtrusionWidth = self.extrusionWidth * self.baseLayerHeightOverExtrusionHeight
		baseStep = baseExtrusionWidth / self.raftPreferences.baseInfillDensity.value
		self.interfaceLayerHeightOverExtrusionHeight = self.raftPreferences.interfaceLayerHeightOverExtrusionHeight.value
		interfaceExtrusionWidth = self.extrusionWidth * self.interfaceLayerHeightOverExtrusionHeight
		self.interfaceStep = interfaceExtrusionWidth / self.raftPreferences.interfaceInfillDensity.value
		self.setCornersZ()
		halfExtrusionHeight = 0.5 * self.extrusionHeight
		self.complexHigh = complexRadius + self.cornerHigh.dropAxis( 2 )
		self.complexLow = self.cornerLow.dropAxis( 2 ) - complexRadius
		extent = self.complexHigh - self.complexLow
		extentStepX = interfaceExtrusionWidth + 2.0 * self.interfaceStep * math.ceil( 0.5 * ( extent.real - self.interfaceStep ) / self.interfaceStep )
		extentStepY = baseExtrusionWidth + 2.0 * baseStep * math.ceil( 0.5 * ( extent.imag - baseStep ) / baseStep )
		center = 0.5 * ( self.complexHigh + self.complexLow )
		extentStep = complex( extentStepX, extentStepY )
		stepBegin = center - 0.5 * extentStep
		stepEnd = stepBegin + extentStep
		zBegin = self.extrusionTop + self.extrusionHeight
		beginLoop = getSquareLoop( self.cornerLow.dropAxis( 2 ), self.cornerHigh.dropAxis( 2 ), zBegin )
		extrudeRaft = self.raftPreferences.baseLayers.value > 0 or self.raftPreferences.interfaceLayers.value > 0
		if extrudeRaft:
			self.addTemperature( self.raftPreferences.temperatureRaft.value )
		else:
			self.addTemperature( self.raftPreferences.temperatureShapeFirstLayerOutline.value )
		self.addLine( '(<layerStart> ' + self.getRounded( self.extrusionTop ) + ' )' ) # Indicate that a new layer is starting.
		intercircle.addOrbits( beginLoop, self, self.raftPreferences.temperatureChangeBeforeTimeRaft.value )
		for baseLayerIndex in range( self.raftPreferences.baseLayers.value ):
			self.addBaseLayer( baseExtrusionWidth, baseStep, stepBegin, stepEnd )
		self.setInterfaceVariables( interfaceExtrusionWidth, stepBegin, stepEnd )
		for interfaceLayerIndex in range( self.raftPreferences.interfaceLayers.value ):
			self.addInterfaceLayer()
		self.setBoundaryLayers()
		self.operatingJump = self.extrusionTop - self.cornerLow.z + halfExtrusionHeight + halfExtrusionHeight * self.raftPreferences.operatingNozzleLiftOverHalfExtrusionHeight.value
		if extrudeRaft:
			self.addTemperature( self.raftPreferences.temperatureShapeFirstLayerOutline.value )
			squareLoop = getSquareLoop( stepBegin, stepEnd, self.extrusionTop )
			intercircle.addOrbits( squareLoop, self, self.raftPreferences.temperatureChangeTimeBeforeFirstLayerOutline.value )

	def addSupportLayerTable( self, layerIndex ):
		"Add support segments from the boundary layers."
		aboveLoops = self.supportLayers[ layerIndex + 1 ]
		if len( aboveLoops ) < 1:
			self.supportLayerTables.append( {} )
			return
		supportLayer = self.supportLayers[ layerIndex ]
		horizontalSegmentTable = {}
		aboveZ = aboveLoops[ 0 ][ 0 ].z
		rise = self.extrusionHeight
		z = aboveZ - self.extrusionHeight
		if len( supportLayer ) > 0:
			z = supportLayer[ 0 ][ 0 ].z
			rise = aboveZ - z
		outsetSupportLayer = intercircle.getInsetLoops( - self.minimumSupportRatio * rise, supportLayer )
		numberOfSubSteps = 10
		subStepSize = self.interfaceStep / float( numberOfSubSteps )
		for y in self.interfaceStepsUntilEnd:
			xTotalIntersectionIndexList = []
			for subStepIndex in xrange( 2 * numberOfSubSteps + 1 ):
				ySubStep = y + ( subStepIndex - numberOfSubSteps ) * subStepSize
				xIntersectionIndexList = []
				euclidean.addXIntersectionIndexesFromLoops( aboveLoops, - 1, xIntersectionIndexList, ySubStep )
				euclidean.addXIntersectionIndexesFromLoops( outsetSupportLayer, 0, xIntersectionIndexList, ySubStep )
				xIntersections = euclidean.getXIntersectionsFromIntersections( xIntersectionIndexList )
				for xIntersection in xIntersections:
					xTotalIntersectionIndexList.append( euclidean.XIntersectionIndex( subStepIndex, xIntersection ) )
			xTotalIntersections = getJoinOfXIntersectionIndexes( xTotalIntersectionIndexList )
			lineSegments = euclidean.getSegmentsFromXIntersections( xTotalIntersections, y, z )
			if len( lineSegments ) > 0:
				horizontalSegmentTable[ y ] = lineSegments
		self.supportLayerTables.append( horizontalSegmentTable )

	def addSupportLayerTemperature( self, segments ):
		"Add support layer and temperature before the object layer."
		self.addTemperatureOrbits( segments, self.raftPreferences.temperatureShapeSupportLayers, self.raftPreferences.temperatureChangeTimeBeforeSupportLayers )
		endpoints = getEndpointsFromSegments( segments )
		aroundPixelTable = {}
		aroundWidth = .444444444444
		layerFillInset = .222222222222
		boundaryLoops = self.boundaryLayers[ self.layerIndex ]
		for boundaryLoop in boundaryLoops:
			euclidean.addLoopToPixelTable( boundaryLoop, aroundPixelTable, aroundWidth )
		paths = euclidean.getPathsFromEndpoints( endpoints, layerFillInset, aroundPixelTable, aroundWidth )
		for path in paths:
			for point in path:
				if self.operatingJump != None:
					point.z += self.operatingJump
			self.addGcodeFromFeedrateThread( self.feedrateMinute, path )
		self.addTemperatureOrbits( segments, self.raftPreferences.temperatureShapeSupportedLayers, self.raftPreferences.temperatureChangeTimeBeforeSupportedLayers )

	def addTemperature( self, temperature ):
		"Add a line of temperature."
		self.addLine( 'M104 S' + euclidean.getRoundedToThreePlaces( temperature ) ) # Set temperature.

	def addTemperatureOrbits( self, segments, temperaturePreference, temperatureTimeChangePreference ):
		"Add the temperature and orbits around the support layer."
		if self.layerIndex < 0:
			return
		boundaryLoops = self.boundaryLayers[ self.layerIndex ]
		self.addTemperature( temperaturePreference.value )
		if len( boundaryLoops ) < 1:
			endpoints = getEndpointsFromSegments( segments )
			layerCornerHigh = Vec3( - 999999999.0, - 999999999.0, - 999999999.0 )
			layerCornerLow = Vec3( 999999999.0, 999999999.0, 999999999.0 )
			for endpoint in endpoints:
				layerCornerHigh = euclidean.getPointMaximum( layerCornerHigh, endpoint.point )
				layerCornerLow = euclidean.getPointMinimum( layerCornerLow, endpoint.point )
			z = endpoints[ 0 ].point.z
			squareLoop = getSquareLoop( layerCornerLow.dropAxis( 2 ), layerCornerHigh.dropAxis( 2 ), z )
			intercircle.setZAccordingToOperatingJump( squareLoop, self.operatingJump )
			intercircle.addOrbits( squareLoop, self, temperatureTimeChangePreference.value )
			return
		perimeterInset = 0.4 * self.extrusionPerimeterWidth
		insetBoundaryLoops = intercircle.getInsetLoops( perimeterInset, boundaryLoops )
		if len( insetBoundaryLoops ) < 1:
			insetBoundaryLoops = boundaryLoops
		largestLoop = euclidean.getLargestLoop( insetBoundaryLoops )
		intercircle.setZAccordingToOperatingJump( largestLoop, self.operatingJump )
		intercircle.addOrbits( largestLoop, self, temperatureTimeChangePreference.value )

	def addToFillXIntersectionIndexTables( self, fillXIntersectionIndexTables, layerIndex ):
		"Add fill segments from the boundary layers."
		boundaryLoops = self.supportLayers[ layerIndex ]
		alreadyFilledOutsets = []
		layerOffsetWidth = self.extrusionWidth
		slightlyGreaterThanOffset = 1.01 * layerOffsetWidth
		muchGreaterThanLayerOffset = 2.5 * layerOffsetWidth
		for boundaryLoop in boundaryLoops:
			centers = intercircle.getCentersFromLoopDirection( euclidean.isWiddershins( boundaryLoop ), boundaryLoop, slightlyGreaterThanOffset )
			for center in centers:
				alreadySupportedOutset = intercircle.getSimplifiedInsetFromClockwiseLoop( center, layerOffsetWidth )
				if euclidean.getMaximumSpan( alreadySupportedOutset ) > muchGreaterThanLayerOffset:
					if euclidean.isPathInsideLoop( boundaryLoop, alreadySupportedOutset ) != euclidean.isWiddershins( boundaryLoop ):
						alreadyFilledOutsets.append( alreadySupportedOutset )
		if len( alreadyFilledOutsets ) < 1:
			fillXIntersectionIndexTables.append( {} )
			return
		fillXIntersectionIndexTable = {}
		z = alreadyFilledOutsets[ 0 ][ 0 ].z
		for y in self.interfaceStepsUntilEnd:
			xIntersectionIndexes = getFillXIntersectionIndexes( alreadyFilledOutsets, y )
			if len( xIntersectionIndexes ) > 0:
				xIntersections = getJoinOfXIntersectionIndexes( xIntersectionIndexes )
				lineSegments = euclidean.getSegmentsFromXIntersections( xIntersections, y, z )
				fillXIntersectionIndexTable[ y ] = lineSegments
		fillXIntersectionIndexTables.append( fillXIntersectionIndexTable )

	def extendSegments( self, supportLayerTable ):
		"Extend the support segments."
		supportLayerKeys = supportLayerTable.keys()
		horizontalSegmentSegmentTable = {}
		for supportLayerKey in supportLayerKeys:
			lineSegments = supportLayerTable[ supportLayerKey ]
			lastSegmentZ = None
			xIntersectionIndexList = []
			for lineSegmentIndex in xrange( len( lineSegments ) ):
				lineSegment = lineSegments[ lineSegmentIndex ]
				extendedLineSegment = getExtendedLineSegment( self.raftOutsetRadius, lineSegment )
				if extendedLineSegment != None:
					addXIntersectionsFromSegment( lineSegmentIndex, extendedLineSegment, xIntersectionIndexList )
					lastSegmentZ = extendedLineSegment[ 0 ].point.z
			xIntersections = getJoinOfXIntersectionIndexes( xIntersectionIndexList )
			for xIntersectionIndex in xrange( len( xIntersections ) ):
				xIntersection = xIntersections[ xIntersectionIndex ]
				xIntersection = max( xIntersection, self.interfaceBeginX )
				xIntersection = min( xIntersection, self.interfaceEndX )
				xIntersections[ xIntersectionIndex ] = xIntersection
			if lastSegmentZ != None:
				extendedLineSegments = euclidean.getSegmentsFromXIntersections( xIntersections, supportLayerKey, lastSegmentZ )
				supportLayerTable[ supportLayerKey ] = extendedLineSegments
			else:
				del supportLayerTable[ supportLayerKey ]

	def getBoundaryLine( self, splitLine ):
		"Get elevated boundary gcode line."
		location = gcodec.getLocationFromSplitLine( None, splitLine )
		if self.operatingJump != None:
			location.z += self.operatingJump
		return '(<boundaryPoint> X%s Y%s Z%s )' % ( self.getRounded( location.x ), self.getRounded( location.y ), self.getRounded( location.z ) )

	def getGcodeFromFeedrateMovement( self, feedrateMinute, point ):
		"Get a gcode movement."
		return "G1 X%s Y%s Z%s F%s" % ( self.getRounded( point.x ), self.getRounded( point.y ), self.getRounded( point.z ), self.getRounded( feedrateMinute ) )

	def getRaftedLine( self, splitLine ):
		"Get elevated gcode line with operating feedrate."
		location = gcodec.getLocationFromSplitLine( self.oldLocation, splitLine )
		self.feedrateMinute = gcodec.getFeedrateMinute( self.feedrateMinute, splitLine )
		self.oldLocation = Vec3().getFromVec3( location )
		if self.operatingJump != None:
			location.z += self.operatingJump
		if not self.isFirstLayerWithinTemperatureAdded and not self.isSurroundingLoop:
			self.isFirstLayerWithinTemperatureAdded = True
			self.addTemperature( self.raftPreferences.temperatureShapeFirstLayerWithin.value )
			if self.raftPreferences.addRaftElevateNozzleOrbitSetAltitude.value:
				intercircle.addOperatingOrbits( self.boundaryLayers[ self.layerIndex ], self.operatingJump, self, self.raftPreferences.temperatureChangeTimeBeforeNextThreads.value )
		return self.getGcodeFromFeedrateMovement( self.feedrateMinute, location )

	def getRounded( self, number ):
		"Get number rounded to the number of carried decimal places as a string."
		return euclidean.getRoundedToDecimalPlaces( self.decimalPlacesCarried, number )

	def getStepsUntilEnd( self, begin, end, stepSize ):
		"Get steps from the beginning until the end."
		step = begin
		steps = []
		while step < end:
			steps.append( step )
			step += stepSize
		return steps

	def getSupportLayerSegments( self ):
		"Get the support layer segments."
		if len( self.supportLayerTables ) <= self.layerIndex:
			return []
		segments = []
		supportLayerTable = self.supportLayerTables[ self.layerIndex ]
		supportLayerKeys = supportLayerTable.keys()
		supportLayerKeys.sort()
		for supportLayerKey in supportLayerKeys:
			segments += supportLayerTable[ supportLayerKey ]
		return segments

	def joinSegments( self, supportLayerTableIndex ):
		"Join the support segments of this layer with those of the layer above."
		horizontalSegmentTable = self.supportLayerTables[ supportLayerTableIndex ]
		horizontalSegmentTableKeys = horizontalSegmentTable.keys()
		aboveHorizontalSegmentTable = self.supportLayerTables[ supportLayerTableIndex + 1 ]
		aboveHorizontalSegmentTableKeys = aboveHorizontalSegmentTable.keys()
		z = 2.2123
		if len( aboveHorizontalSegmentTableKeys ) > 0:
			firstSegments = aboveHorizontalSegmentTable[ aboveHorizontalSegmentTableKeys[ 0 ] ]
			if len( firstSegments ) > 0:
				z = firstSegments[ 0 ][ 0 ].point.z - self.extrusionHeight
		if len( horizontalSegmentTableKeys ) > 0:
			firstSegments = horizontalSegmentTable[ horizontalSegmentTableKeys[ 0 ] ]
			if len( firstSegments ) > 0:
				z = firstSegments[ 0 ][ 0 ].point.z
		joinSegmentTables( aboveHorizontalSegmentTable, horizontalSegmentTable, z )

	def parseGcode( self, gcodeText, raftPreferences ):
		"Parse gcode text and store the raft gcode."
		self.raftPreferences = raftPreferences
		self.minimumSupportRatio = math.tan( math.radians( raftPreferences.supportMinimumAngle.value ) )
		self.raftOutsetRadius = self.raftPreferences.raftOutsetRadiusOverExtrusionWidth.value * self.extrusionWidth
		self.lines = gcodec.getTextLines( gcodeText )
		self.parseInitialization()
		if raftPreferences.addRaftElevateNozzleOrbitSetAltitude.value:
			self.addRaft()
		self.addTemperature( raftPreferences.temperatureShapeFirstLayerOutline.value )
		if raftPreferences.turnExtruderOnEarly.value:
			self.addLine( 'M101' )
			self.isStartupEarly = True
		for line in self.lines[ self.lineIndex : ]:
			self.parseLine( line )

	def parseInitialization( self ):
		"Parse gcode initialization and store the parameters."
		for self.lineIndex in range( len( self.lines ) ):
			line = self.lines[ self.lineIndex ]
			splitLine = line.split()
			firstWord = gcodec.getFirstWord( splitLine )
			if firstWord == '(<decimalPlacesCarried>':
				self.decimalPlacesCarried = int( splitLine[ 1 ] )
			elif firstWord == '(<extrusionHeight>':
				self.extrusionHeight = float( splitLine[ 1 ] )
			elif firstWord == '(<extrusionPerimeterWidth>':
				self.extrusionPerimeterWidth = float( splitLine[ 1 ] )
				self.supportOutset = self.extrusionPerimeterWidth - self.extrusionPerimeterWidth * self.raftPreferences.supportInsetOverPerimeterExtrusionWidth.value
			elif firstWord == '(<extrusionWidth>':
				self.extrusionWidth = float( splitLine[ 1 ] )
			elif firstWord == '(<extrusionStart>':
				self.addLine( '(<procedureDone> raft )' )
				self.addLine( line )
				self.lineIndex += 1
				return
			elif firstWord == '(<feedrateMinute>':
				self.feedrateMinute = float( splitLine[ 1 ] )
			elif firstWord == '(<orbitalFeedratePerSecond>':
				self.orbitalFeedratePerSecond = float( splitLine[ 1 ] )
			self.addLine( line )

	def parseLine( self, line ):
		"Parse a gcode line and add it to the raft skein."
		splitLine = line.split()
		if len( splitLine ) < 1:
			return
		firstWord = splitLine[ 0 ]
		if firstWord == 'G1':
			if self.extrusionStart:
				line = self.getRaftedLine( splitLine )
		elif firstWord == 'M101':
			if self.isStartupEarly:
				self.isStartupEarly = False
				return
		elif firstWord == '(<boundaryPoint>':
			line = self.getBoundaryLine( splitLine )
		elif firstWord == '(</extrusionStart>':
			self.extrusionStart = False
			self.addLine( self.operatingLayerEndLine )
		elif firstWord == '(<layerStart>':
			self.layerIndex += 1
			if self.operatingJump != None:
				line = '(<layerStart> ' + self.getRounded( self.extrusionTop + float( splitLine[ 1 ] ) ) + ' )'
			segments = self.getSupportLayerSegments()
			if self.layerIndex == 1:
				if len( segments ) < 1:
					self.addTemperature( self.raftPreferences.temperatureShapeNextLayers.value )
					if self.raftPreferences.addRaftElevateNozzleOrbitSetAltitude.value:
						intercircle.addOperatingOrbits( self.boundaryLayers[ self.layerIndex ], self.operatingJump, self, self.raftPreferences.temperatureChangeTimeBeforeNextThreads.value )
			if self.layerIndex > len( self.supportLayerTables ) + 1:
				self.addLine( self.operatingLayerEndLine )
				self.operatingLayerEndLine = ''
			self.addLine( line )
			line = ''
			if len( segments ) > 0:
				self.addSupportLayerTemperature( segments )
		self.addLine( line )

	def setBoundaryLayers( self ):
		"Set the boundary layers."
		boundaryLoop = None
		boundaryLoops = None
		for line in self.lines[ self.lineIndex : ]:
			splitLine = line.split()
			firstWord = gcodec.getFirstWord( splitLine )
			if firstWord == '(<boundaryPoint>':
				if boundaryLoop == None:
					boundaryLoop = []
					boundaryLoops.append( boundaryLoop )
				boundaryLoop.append( gcodec.getLocationFromSplitLine( None, splitLine ) )
			elif firstWord == '(<layerStart>':
				boundaryLoops = []
				self.boundaryLayers.append( boundaryLoops )
			elif firstWord == '(</surroundingLoop>':
				boundaryLoop = None
		if self.raftPreferences.supportChoiceNoSupportMaterial.value:
			return
		if len( self.interfaceStepsUntilEnd ) < 1:
			return
		if len( self.boundaryLayers ) < 2:
			return
		for boundaryLayer in self.boundaryLayers:
			self.supportLayers.append( intercircle.getInsetLoops( - self.supportOutset, boundaryLayer ) )
		for layerIndex in xrange( len( self.supportLayers ) - 1 ):
			self.addSupportLayerTable( layerIndex )
		self.truncateSupportLayerTables()
		fillXIntersectionIndexTables = []
		for supportLayerTableIndex in xrange( len( self.supportLayerTables ) ):
			self.addToFillXIntersectionIndexTables( fillXIntersectionIndexTables, supportLayerTableIndex )
		if self.raftPreferences.supportChoiceSupportMaterialOnExteriorOnly.value:
			for supportLayerTableIndex in xrange( 1, len( self.supportLayerTables ) ):
				self.subtractJoinedFill( fillXIntersectionIndexTables, supportLayerTableIndex )
		for supportLayerTableIndex in xrange( len( self.supportLayerTables ) - 2, - 1, - 1 ):
			self.joinSegments( supportLayerTableIndex )
		for supportLayerTable in self.supportLayerTables:
			self.extendSegments( supportLayerTable )
		for supportLayerTableIndex in xrange( len( self.supportLayerTables ) ):
			subtractFill( fillXIntersectionIndexTables[ supportLayerTableIndex ], self.supportLayerTables[ supportLayerTableIndex ] )

	def setCornersZ( self ):
		"Set maximum and minimum corners and z."
		layerIndex = - 1
		for line in self.lines[ self.lineIndex : ]:
			splitLine = line.split()
			firstWord = gcodec.getFirstWord( splitLine )
			if firstWord == 'G1':
				location = gcodec.getLocationFromSplitLine( self.oldLocation, splitLine )
				self.cornerHigh = euclidean.getPointMaximum( self.cornerHigh, location )
				self.cornerLow = euclidean.getPointMinimum( self.cornerLow, location )
				self.oldLocation = location
			elif firstWord == '(<layerStart>':
				layerIndex += 1
				if self.raftPreferences.supportChoiceNoSupportMaterial.value:
					if layerIndex > 1:
						return

	def setInterfaceVariables( self, interfaceExtrusionWidth, stepBegin, stepEnd ):
		"Set the interface variables."
		halfInterfaceExtrusionWidth = 0.5 * interfaceExtrusionWidth
		self.interfaceStepsUntilEnd = self.getStepsUntilEnd( stepBegin.imag + halfInterfaceExtrusionWidth, stepEnd.imag, self.interfaceStep )
		self.interfaceOverhang = self.raftPreferences.infillOverhang.value * halfInterfaceExtrusionWidth - halfInterfaceExtrusionWidth
		self.interfaceBeginX = stepBegin.real - self.interfaceOverhang
		self.interfaceEndX = stepEnd.real + self.interfaceOverhang

	def subtractJoinedFill( self, fillXIntersectionIndexTables, supportLayerTableIndex ):
		"Join the fill then subtract it from the support layer table."
		fillXIntersectionIndexTable = fillXIntersectionIndexTables[ supportLayerTableIndex ]
		fillXIntersectionIndexTableKeys = fillXIntersectionIndexTable.keys()
		belowHorizontalSegmentTable = fillXIntersectionIndexTables[ supportLayerTableIndex - 1 ]
		belowHorizontalSegmentTableKeys = belowHorizontalSegmentTable.keys()
		z = 3.2123
		if len( belowHorizontalSegmentTableKeys ) > 0:
			firstSegments = belowHorizontalSegmentTable[ belowHorizontalSegmentTableKeys[ 0 ] ]
			if len( firstSegments ) > 0:
				z = firstSegments[ 0 ][ 0 ].point.z + self.extrusionHeight
		if len( fillXIntersectionIndexTableKeys ) > 0:
			firstSegments = fillXIntersectionIndexTable[ fillXIntersectionIndexTableKeys[ 0 ] ]
			if len( firstSegments ) > 0:
				z = firstSegments[ 0 ][ 0 ].point.z
		joinSegmentTables( belowHorizontalSegmentTable, fillXIntersectionIndexTable, z )
		supportLayerTable = self.supportLayerTables[ supportLayerTableIndex ]
		subtractFill( fillXIntersectionIndexTable, supportLayerTable )

	def truncateSupportLayerTables( self ):
		"Truncate the support segments after the last support segment which contains elements."
		for supportLayerTableIndex in xrange( len( self.supportLayerTables ) - 1, - 1, - 1 ):
			if len( self.supportLayerTables[ supportLayerTableIndex ] ) > 0:
				self.supportLayerTables = self.supportLayerTables[ : supportLayerTableIndex + 1 ]
				return
		self.supportLayerTables = []


def main():
	"Display the raft dialog."
	if len( sys.argv ) > 1:
		writeOutput( ' '.join( sys.argv[ 1 : ] ) )
	else:
		preferences.displayDialog( RaftPreferences() )

if __name__ == "__main__":
	main()

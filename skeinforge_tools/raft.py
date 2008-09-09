"""
Raft is a script to create a reusable raft, elevate the nozzle and set the feedrate, flowrate and temperature.

The raft script sets the feedrate, flowrate and temperature.  If the "Activate Raft, Elevate Nozzle, Orbit and Set Altitude"
checkbox is checked, the script will also create a raft, elevate the nozzle, orbit and set the altitude of the bottom of the raft.

Raft is based on the Nophead's reusable raft, which has a base layer running one way, and a couple of perpendicular layers
above.  Each set of layers can be set to a different temperature.  There is the option of having the extruder orbit the raft for a
while, so the heater barrel has time to reach a different temperature, without ooze accumulating around the nozzle.  To run
raft, in a shell type:
> python raft.py

The important values for the raft preferences are the temperatures of the raft, the first layer and the next layers.  These will be
different for each material.  The default preferences for ABS, HDPE, PCL & PLA are from Nophead's experiments.  To change
the material, in a shell type:
> python material.py

This brings up the material preferences dialog.  In that dialog you can add or delete a material on the listbox and you change
the selected material.  After you can change the selected material, run raft again.  If there are preferences for the new material,
those will be in the raft dialog.  If there are no preferences for the new material, the preferences will be set to defaults and you
will have to set new preferences for the new material.

The "Base Infill Density" preference is the infill density ratio of the base of the raft, the default ratio is half.  The
"Base Layer Height over Extrusion Height" preference is the ratio of the height & width of the base layer compared to the
height and width of the shape infill, the default is two.  The "Base Layers" preference is the number of base layers, the default
is one.  The "Base Nozzle Lift over Half Base Extrusion Height" is the amount the nozzle is above the center of the
extrusion divided by half the base extrusion height.

The interface of the raft has equivalent preferences called "Interface Infill Density",
"Interface Layer Height over Extrusion Height", "Interface Layers" and "Interface Nozzle Lift over Half Base Extrusion Height".
The shape has the equivalent preference of called "Operating Nozzle Lift over Half Extrusion Height".

The altitude that the bottom of the raft will be set to the "Bottom Altitude" preference.  The feedrate for the shape will be set
to the 'Feedrate" preference.  The feedrate will be slower for raft layers which have thicker extrusions than the shape infill.

The speed of the orbit compared to the operating extruder speed will be set to the 'Orbital Feedrate over Operating Feedrate'
preference.

In the "Flowrate Choice" radio button group, if "Do Not Add Flowrate" is selected then raft will not add a flowrate to the gcode
output.  If "Metric" is selected, the flowrate in cubic millimeters per second will be added to the output.  If "PWM Setting" is
selected, the value in the "Flowrate PWM Setting" field will be added to the output.

The raft fills a rectangle whose size is the rectangle around the bottom layer of the shape expanded on each side by the
"Raft Outset Radius over Extrusion Width" preference times the extrusion width, minus the "Infill Overhang" ratio times the
width of the extrusion of the raft.

The extruder will orbit for at least "Temperature Change Time of Raft" seconds before extruding the raft.  It will orbit for at least
"Temperature Change Time of First Layer" seconds before extruding the first layer of the shape.  It will orbit for at least
"Temperature Change Time of Next Layers" seconds before extruding the next layers of the shape.  If a time is zero, it will not
orbit.

The "Temperature of Raft" preference sets the temperature of the raft.  The "Temperature of Shape First Layer" preference sets
the temperature of the first layer of the shape.  The "Temperature of Shape Next Layers" preference sets the temperature of the
next layers of the shape.

The following examples raft the files Hollow Square.gcode & Hollow Square.gts.  The examples are run in a terminal in the folder
which contains Hollow Square.gcode, Hollow Square.gts and raft.py.  The raft function will raft if
"Activate Raft, Elevate Nozzle, Orbit and Set Altitude" is true, which can be set in the dialog or by changing the preferences file
'raft.csv' with a text editor or a spreadsheet program set to separate tabs.  The functions writeOutput and getRaftChainGcode
check to see if the text has been rafted, if not they call getCombChainGcode in comb.py to get combed gcode; once they have
the combed text, then they raft.


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
from skeinforge_tools import comb
from skeinforge_tools import import_translator
from skeinforge_tools import material
from skeinforge_tools import polyfile
import cStringIO
import math
import sys
import time


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


#maybe cool for a minute
def getRaftChainGcode( filename, gcodeText, raftPreferences = None ):
	"Raft a gcode linear move text.  Chain raft the gcode if it is not already rafted."
	gcodeText = gcodec.getGcodeFileText( filename, gcodeText )
	if not gcodec.isProcedureDone( gcodeText, 'comb' ):
		gcodeText = comb.getCombChainGcode( filename, gcodeText )
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
	skein = RaftSkein()
	skein.parseGcode( gcodeText, raftPreferences )
	return skein.output.getvalue()

def getSquareLoop( begin, end ):
	"Get a square loop from the beginning to the end and back."
	loop = [ begin ]
	loop.append( Vec3( begin.x, end.y, begin.z ) )
	loop.append( end )
	loop.append( Vec3( end.x, begin.y, begin.z ) )
	return loop

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


class RaftSkein:
	"A class to raft a skein of extrusions."
	def __init__( self ):
		self.boundaryLoop = None
		self.boundaryLoops = []
		self.cornerHigh = Vec3( - 999999999.0, - 999999999.0, - 999999999.0 )
		self.cornerLow = Vec3( 999999999.0, 999999999.0, 999999999.0 )
		self.decimalPlacesCarried = 3
		self.extrusionDiameter = 0.6
		self.extrusionTop = 0.0
		self.extrusionWidth = 0.6
		self.feedratePerSecond = 16.0
		self.isStartupEarly = False
		self.layerIndex = - 1
		self.extrusionHeight = 0.4
		self.lineIndex = 0
		self.lines = None
		self.oldLocation = None
		self.operatingJump = None
		self.output = cStringIO.StringIO()

	def addBaseLayer( self, baseExtrusionWidth, baseStep, stepBegin, stepEnd ):
		"Add a base layer."
		baseExtrusionHeight = self.extrusionHeight * self.baseLayerHeightOverExtrusionHeight
		halfBaseExtrusionHeight = 0.5 * baseExtrusionHeight
		halfBaseExtrusionWidth = 0.5 * baseExtrusionWidth
		stepsUntilEnd = self.getStepsUntilEnd( stepBegin.imag + halfBaseExtrusionWidth, stepEnd.imag, baseStep )
		baseOverhang = self.raftPreferences.infillOverhang.value * halfBaseExtrusionWidth - halfBaseExtrusionWidth
		beginX = stepBegin.real - baseOverhang
		endX = stepEnd.real + baseOverhang
		segments = []
		zCenter = self.extrusionTop + halfBaseExtrusionHeight
		z = zCenter + halfBaseExtrusionHeight * self.raftPreferences.baseNozzleLiftOverHalfBaseExtrusionHeight.value
		for y in stepsUntilEnd:
			begin = Vec3( beginX, y, z )
			end = Vec3( endX, y, z )
			segments.append( euclidean.getSegmentFromPoints( begin, end ) )
		if len( segments ) < 1:
			print( 'This should never happen, the base layer has a size of zero.' )
			return
		self.addLayerFromSegments( self.feedratePerSecond / self.baseLayerHeightOverExtrusionHeight / self.baseLayerHeightOverExtrusionHeight, baseExtrusionHeight, segments, zCenter )

	def addFlowrate( self ):
		"Add flowrate line."
		roundedFlowrate = euclidean.getRoundedToThreePlaces( math.pi * self.extrusionDiameter * self.extrusionDiameter / 4.0 * self.feedratePerSecond )
		self.addLine( '(<flowrateCubicMillimetersPerSecond> ' + roundedFlowrate + ' )' )
		if self.raftPreferences.flowrateDoNotAddFlowratePreference.value:
			return
		if self.raftPreferences.flowrateMetricPreference.value:
			self.addLine( 'M108 S' + roundedFlowrate )
			return
		self.addLine( 'M108 S' + euclidean.getRoundedToThreePlaces( self.raftPreferences.flowratePWMSetting.value ) )

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

	def addInterfaceLayer( self, interfaceExtrusionWidth, interfaceStep, stepBegin, stepEnd ):
		"Add an interface layer."
		interfaceExtrusionHeight = self.extrusionHeight * self.interfaceLayerHeightOverExtrusionHeight
		halfInterfaceExtrusionHeight = 0.5 * interfaceExtrusionHeight
		halfInterfaceExtrusionWidth = 0.5 * interfaceExtrusionWidth
		stepsUntilEnd = self.getStepsUntilEnd( stepBegin.real + halfInterfaceExtrusionWidth, stepEnd.real, interfaceStep )
		interfaceOverhang = self.raftPreferences.infillOverhang.value * halfInterfaceExtrusionWidth - halfInterfaceExtrusionWidth
		beginY = stepBegin.imag - interfaceOverhang
		endY = stepEnd.imag + interfaceOverhang
		segments = []
		zCenter = self.extrusionTop + halfInterfaceExtrusionHeight
		z = zCenter + halfInterfaceExtrusionHeight * self.raftPreferences.interfaceNozzleLiftOverHalfInterfaceExtrusionHeight.value
		for x in stepsUntilEnd:
			begin = Vec3( x, beginY, z )
			end = Vec3( x, endY, z )
			segments.append( euclidean.getSegmentFromPoints( begin, end ) )
		if len( segments ) < 1:
			print( 'This should never happen, the interface layer has a size of zero.' )
			return
		self.addLayerFromSegments( self.feedratePerSecond / self.interfaceLayerHeightOverExtrusionHeight / self.interfaceLayerHeightOverExtrusionHeight, interfaceExtrusionHeight, segments, zCenter )

	def addLayerFromSegments( self, feedrateSecond, layerExtrusionHeight, segments, zCenter ):
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
		self.addGcodeFromFeedrateThread( 60.0 * feedrateSecond, path )
		self.extrusionTop += layerExtrusionHeight

	def addLine( self, line ):
		"Add a line of text and a newline to the output."
		self.output.write( line + "\n" )

	def addRaft( self ):
		self.extrusionTop = self.raftPreferences.bottomAltitude.value
		radius = self.raftPreferences.raftOutsetRadiusOverExtrusionWidth.value * self.extrusionWidth
		complexRadius = complex( radius, radius )
		self.baseLayerHeightOverExtrusionHeight = self.raftPreferences.baseLayerHeightOverExtrusionHeight.value
		baseExtrusionWidth = self.extrusionWidth * self.baseLayerHeightOverExtrusionHeight
		baseStep = baseExtrusionWidth / self.raftPreferences.baseInfillDensity.value
		self.interfaceLayerHeightOverExtrusionHeight = self.raftPreferences.interfaceLayerHeightOverExtrusionHeight.value
		interfaceExtrusionWidth = self.extrusionWidth * self.interfaceLayerHeightOverExtrusionHeight
		interfaceStep = interfaceExtrusionWidth / self.raftPreferences.interfaceInfillDensity.value
		self.setCornersZ()
		halfExtrusionHeight = 0.5 * self.extrusionHeight
		self.complexHigh = complexRadius + self.cornerHigh.dropAxis( 2 )
		self.complexLow = self.cornerLow.dropAxis( 2 ) - complexRadius
		extent = self.complexHigh - self.complexLow
		extentStepX = interfaceExtrusionWidth + 2.0 * interfaceStep * math.ceil( 0.5 * ( extent.real - interfaceStep ) / interfaceStep )
		extentStepY = baseExtrusionWidth + 2.0 * baseStep * math.ceil( 0.5 * ( extent.imag - baseStep ) / baseStep )
		center = 0.5 * ( self.complexHigh + self.complexLow )
		extentStep = complex( extentStepX, extentStepY )
		stepBegin = center - 0.5 * extentStep
		stepEnd = stepBegin + extentStep
		zBegin = self.extrusionTop + self.extrusionHeight
		beginLoop = getSquareLoop( Vec3( self.cornerLow.x, self.cornerLow.y, zBegin ), Vec3( self.cornerHigh.x, self.cornerHigh.y, zBegin ) )
		extrudeRaft = self.raftPreferences.baseLayers.value > 0 or self.raftPreferences.interfaceLayers.value > 0
		if extrudeRaft:
			self.addTemperature( self.raftPreferences.temperatureRaft.value )
		else:
			self.addTemperature( self.raftPreferences.temperatureShapeFirstLayer.value )
		self.addLine( '(<layerStart> ' + self.getRounded( self.extrusionTop ) + ' )' ) # Indicate that a new layer is starting.
		intercircle.addOrbits( beginLoop, self, self.raftPreferences.temperatureChangeTimeRaft.value )
		for baseLayerIndex in range( self.raftPreferences.baseLayers.value ):
			self.addBaseLayer( baseExtrusionWidth, baseStep, stepBegin, stepEnd )
		for interfaceLayerIndex in range( self.raftPreferences.interfaceLayers.value ):
			self.addInterfaceLayer( interfaceExtrusionWidth, interfaceStep, stepBegin, stepEnd )
		self.operatingJump = self.extrusionTop - self.cornerLow.z + halfExtrusionHeight + halfExtrusionHeight * self.raftPreferences.operatingNozzleLiftOverHalfExtrusionHeight.value
		if extrudeRaft:
			self.addTemperature( self.raftPreferences.temperatureShapeFirstLayer.value )
			squareLoop = getSquareLoop( Vec3( stepBegin.real, stepBegin.imag, self.extrusionTop ), Vec3( stepEnd.real, stepEnd.imag, self.extrusionTop ) )
			intercircle.addOrbits( squareLoop, self, self.raftPreferences.temperatureChangeTimeFirstLayer.value )

	def addTemperature( self, temperature ):
		"Add a line of temperature."
		self.addLine( 'M104 S' + euclidean.getRoundedToThreePlaces( temperature ) ) # Set temperature.

	def getGcodeFromFeedrateMovement( self, feedrateMinute, point ):
		"Get a gcode movement."
		return "G1 X%s Y%s Z%s F%s" % ( self.getRounded( point.x ), self.getRounded( point.y ), self.getRounded( point.z ), self.getRounded( feedrateMinute ) )

	def getRaftedLine( self, splitLine ):
		"Get elevated gcode line with operating feedrate."
		location = gcodec.getLocationFromSplitLine( self.oldLocation, splitLine )
		self.oldLocation = Vec3().getFromVec3( location )
		if self.operatingJump != None:
			location.z += self.operatingJump
		return self.getGcodeFromFeedrateMovement( 60.0 * self.feedratePerSecond, location )

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

	def parseGcode( self, gcodeText, raftPreferences ):
		"Parse gcode text and store the raft gcode."
		self.raftPreferences = raftPreferences
		self.feedratePerSecond = raftPreferences.feedratePerSecond.value
		self.orbitalFeedratePerSecond = self.feedratePerSecond * raftPreferences.orbitalFeedrateOverOperatingFeedrate.value
		self.lines = gcodec.getTextLines( gcodeText )
		self.parseInitialization()
		if raftPreferences.activateRaft.value:
			self.addRaft()
		self.addTemperature( raftPreferences.temperatureShapeFirstLayer.value )
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
			firstWord = ''
			if len( splitLine ) > 0:
				firstWord = splitLine[ 0 ]
			if firstWord == '(<decimalPlacesCarried>':
				self.decimalPlacesCarried = int( splitLine[ 1 ] )
			elif firstWord == '(<extrusionDiameter>':
				self.extrusionDiameter = float( splitLine[ 1 ] )
				self.addFlowrate()
			elif firstWord == '(<extrusionHeight>':
				self.extrusionHeight = float( splitLine[ 1 ] )
			elif firstWord == '(<extrusionPerimeterWidth>':
				self.extrusionPerimeterWidth = float( splitLine[ 1 ] )
			elif firstWord == '(<extrusionWidth>':
				self.extrusionWidth = float( splitLine[ 1 ] )
				self.addLine( '(<orbitalFeedratePerSecond> %s )' % self.orbitalFeedratePerSecond )
			elif firstWord == '(<extrusionStart>':
				self.addLine( '(<procedureDone> raft )' )
				self.addLine( line )
				self.lineIndex += 1
				return
			self.addLine( line )

	def parseLine( self, line ):
		"Parse a gcode line and add it to the raft skein."
		splitLine = line.split()
		if len( splitLine ) < 1:
			return
		firstWord = splitLine[ 0 ]
		if firstWord == 'G1':
			line = self.getRaftedLine( splitLine )
		elif firstWord == 'M101':
			if self.isStartupEarly:
				self.isStartupEarly = False
				return
		elif firstWord == '(<boundaryPoint>':
			self.boundaryLoop.append( gcodec.getLocationFromSplitLine( None, splitLine ) )
		elif firstWord == '(<layerStart>':
			self.layerIndex += 1
			if self.operatingJump != None:
				line = '(<layerStart> ' + self.getRounded( self.extrusionTop + float( splitLine[ 1 ] ) ) + ' )'
			if self.layerIndex == 1:
				intercircle.addOperatingOrbits( self.operatingJump, self, self.raftPreferences.temperatureChangeTimeNextLayers.value )
			if self.layerIndex > 1:
				self.addLine( '(<operatingLayerEnd> )' )
			self.boundaryLoops = []
		elif firstWord == '(<surroundingLoop>':
			self.boundaryLoop = []
			self.boundaryLoops.append( self.boundaryLoop )
		self.addLine( line )

	def setCornersZ( self ):
		"Set maximum and minimum corners and z."
		layerIndex = - 1
		for line in self.lines[ self.lineIndex : ]:
			splitLine = line.split( ' ' )
			firstWord = ''
			if len( splitLine ) > 0:
				firstWord = splitLine[ 0 ]
			if firstWord == 'G1':
				location = gcodec.getLocationFromSplitLine( self.oldLocation, splitLine )
				self.cornerHigh = euclidean.getPointMaximum( self.cornerHigh, location )
				self.cornerLow = euclidean.getPointMinimum( self.cornerLow, location )
				self.oldLocation = location
			elif firstWord == '(<layerStart>':
				layerIndex += 1
				if layerIndex > 1:
					return


class RaftPreferences:
	"A class to handle the raft preferences."
	def __init__( self ):
		"Set the default preferences, execute title & preferences filename."
		materialName = material.getSelectedMaterial()
		#Set the default preferences.
		self.archive = []
		self.activateRaft = preferences.BooleanPreference().getFromValue( 'Activate Raft, Elevate Nozzle, Orbit and Set Altitude:', True )
		self.archive.append( self.activateRaft )
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
		self.feedratePerSecond = preferences.FloatPreference().getFromValue( 'Feedrate (mm/s):', 16.0 )
		self.archive.append( self.feedratePerSecond )
		flowrateRadio = []
		self.filenameInput = preferences.Filename().getFromFilename( import_translator.getGNUTranslatorGcodeFileTypeTuples(), 'Open File to be Rafted', '' )
		self.archive.append( self.filenameInput )
		self.flowrateDoNotAddFlowratePreference = preferences.RadioLabel().getFromRadioLabel( 'Do Not Add Flowrate', 'Flowrate Choice:', flowrateRadio, False )
		self.archive.append( self.flowrateDoNotAddFlowratePreference )
		self.flowrateMetricPreference = preferences.Radio().getFromRadio( 'Metric', flowrateRadio, False )
		self.archive.append( self.flowrateMetricPreference )
		self.flowratePWMPreference = preferences.Radio().getFromRadio( 'PWM Setting', flowrateRadio, True )
		self.archive.append( self.flowratePWMPreference )
		self.flowratePWMSetting = preferences.FloatPreference().getFromValue( 'Flowrate PWM Setting (if PWM Setting is Chosen):', 210.0 )
		self.archive.append( self.flowratePWMSetting )
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
		self.orbitalFeedrateOverOperatingFeedrate = preferences.FloatPreference().getFromValue( 'Orbital Feedrate over Operating Feedrate (ratio):', 0.5 )
		self.archive.append( self.orbitalFeedrateOverOperatingFeedrate )
		self.raftOutsetRadiusOverExtrusionWidth = preferences.FloatPreference().getFromValue( 'Raft Outset Radius over Extrusion Width (ratio):', 15.0 )
		self.archive.append( self.raftOutsetRadiusOverExtrusionWidth )
		self.temperatureChangeTimeRaft = preferences.FloatPreference().getFromValue( 'Temperature Change Time of Raft (seconds):', 120.0 )
		self.archive.append( self.temperatureChangeTimeRaft )
		self.temperatureChangeTimeFirstLayer = preferences.FloatPreference().getFromValue( 'Temperature Change Time of First Layer (seconds):', 120.0 )
		self.archive.append( self.temperatureChangeTimeFirstLayer )
		self.temperatureChangeTimeNextLayers = preferences.FloatPreference().getFromValue( 'Temperature Change Time of Next Layers (seconds):', 120.0 )
		self.archive.append( self.temperatureChangeTimeNextLayers )
		self.temperatureRaft = preferences.FloatPreference().getFromValue( 'Temperature of Raft (Celcius):', 200.0 )
		self.archive.append( self.temperatureRaft )
		self.temperatureShapeFirstLayer = preferences.FloatPreference().getFromValue( 'Temperature of Shape First Layer (Celcius):', 215.0 )
		self.archive.append( self.temperatureShapeFirstLayer )
		self.temperatureShapeNextLayers = preferences.FloatPreference().getFromValue( 'Temperature of Shape Next Layers (Celcius):', 230.0 )
		self.archive.append( self.temperatureShapeNextLayers )
		self.turnExtruderOnEarly = preferences.BooleanPreference().getFromValue( 'Turn Extruder On Early:', True )
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


def main():
	"Display the raft dialog."
	if len( sys.argv ) > 1:
		writeOutput( ' '.join( sys.argv[ 1 : ] ) )
	else:
		preferences.displayDialog( RaftPreferences() )

if __name__ == "__main__":
	main()

"""
Raft is a script to create a reusable raft, elevate the nozzle and set the feedrate, flowrate and temperature.

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

The raft script sets the feedrate, flowrate and temperature.  If the "Add Raft, Elevate Nozzle, Orbit and Set Altitude" checkbox
is checked, the script will also create a raft, elevate the nozzle, orbit and set the altitude of the bottom of the raft.

The "Base Infill Density" preference is the infill density ratio of the base of the raft, the default ratio is half.  The
"Base Layer Height over Extrusion Height" preference is the ratio of the height & width of the base layer compared to the
height and width of the shape infill, the default is two.  The "Base Layers" preference is the number of base layers, the default
is one.  The "Base Nozzle Lift over Half Base Extrusion Height" is the amount the nozzle is above the center of the
extrusion divided by half the base extrusion height.

The interface of the raft has equivalent preferences called "Interface Infill Density",
"Interface Layer Height over Extrusion Height", "Interface Layers" and "Interface Nozzle Lift over Half Base Extrusion Height".  The
shape has the equivalent preference of called "Operating Nozzle Lift over Half Extrusion Height".

The altitude that the bottom of the raft will be set to the "Bottom Altitude" preference.  The feedrate for the shape will be set
to the 'Feedrate" preference.  The feedrate will be slower for raft layers which have thicker extrusions than the shape infill.

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

For raft to run, install python 2.x on your machine, which is avaliable from http://www.python.org/download/

To use the preferences dialog you'll also need Tkinter, which probably came with the python installation.  If it did not, look for it at:
www.tcl.tk/software/tcltk/

To export a GNU Triangulated Surface file from Art of Illusion, you can use the Export GNU Triangulated Surface script at:
http://members.axion.net/~enrique/Export%20GNU%20Triangulated%20Surface.bsh

To bring it into Art of Illusion, drop it into the folder ArtOfIllusion/Scripts/Tools/.

The GNU Triangulated Surface format is supported by Mesh Viewer, and it is described at:
http://gts.sourceforge.net/reference/gts-surfaces.html#GTS-SURFACE-WRITE

To turn an STL file into filled, rafted gcode, first import the file using the STL import plugin in the import submenu of the file menu
of Art of Illusion.  Then from the Scripts submenu in the Tools menu, choose Export GNU Triangulated Surface and select the
imported STL shape.  Then type 'python slice.py' in a shell in the folder which slice, raft and the rest of the skeinforge tool chain
are in and when the dialog pops up, set the parameters and click 'Save Preferences'.  Then type 'python fill.py' in the shell
and when the dialog pops up, set the parameters and click 'Save Preferences'.  Then type 'python tower.py' in the shell
and when the dialog pops up, change the parameters if you wish but the do nothing default is fine.  Then type 'python comb.py'
in the shell and when the dialog pops up, change the parameters if you wish but the default 'Comb Hair' is fine.  Then type
'python raft.py' in a shell and when the dialog pops up, change the parameters if you wish but the default is fine to start.
Then click 'Raft', choose the file which you exported in Export GNU Triangulated Surface and the filled & rafted file will be
saved with the suffix '_raft'.  To change the material, type 'python material.py' in a shell and when the dialog pops up, you can
change the material, so the next time you bring up raft the preferences will be for that material.  If you add a material which is not
on the list, the preferences for the new material will be set to defaults and you'll have to enter the preferences for that material in
raft.

To write documentation for this program, open a shell in the raft.py directory, then type 'pydoc -w raft', then open 'raft.html' in
a browser or click on the '?' button in the dialog.  To write documentation for all the python scripts in the directory, type 'pydoc -w ./'.
To use other functions of raft, type 'python' in a shell to run the python interpreter, then type 'import raft' to import this program.

The computation intensive python modules will use psyco if it is available and run about twice as fast.  Psyco is described at:
http://psyco.sourceforge.net/index.html

The psyco download page is:
http://psyco.sourceforge.net/download.html

The following examples raft the files Hollow Square.gcode & Hollow Square.gts.  The examples are run in a terminal in the folder
which contains Hollow Square.gcode, Hollow Square.gts and raft.py.  The raft function will raft if 'Add Raft' is true, which can be
set in the dialog or by changing the preferences file 'raft.csv' with a text editor or a spreadsheet program set to separate tabs.
The functions raftChainFile and getRaftChainGcode check to see if the text has been rafted, if not they call getCombChainGcode
in comb.py to get combed gcode; once they have the combed text, then they raft.


> pydoc -w raft
wrote raft.html


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


>>> raft.raftChainFile()
Hollow Square.gts
File Hollow Square.gts is being chain rafted.
The rafted file is saved as Hollow Square_raft.gcode


>>> raft.raftFile()
File Hollow Square.gcode is being rafted.
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

import sys
from skeinforge_utilities.vec3 import Vec3
import comb
import cStringIO
from skeinforge_utilities import euclidean
from skeinforge_utilities import gcodec
from skeinforge_utilities import intercircle
import material
import math
import multifile
from skeinforge_utilities import preferences
import time
import vectorwrite


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


#maybe cool for a minute
def getRaftChainGcode( gcodeText, raftPreferences = None ):
	"Raft a gcode linear move text.  Chain raft the gcode if it is not already rafted."
	if not gcodec.isProcedureDone( gcodeText, 'comb' ):
		gcodeText = comb.getCombChainGcode( gcodeText )
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

def raftChainFile( filename = '' ):
	"""Raft a gcode linear move file.  Chain raft the gcode if it is not already rafted.
	If no filename is specified, raft the first unmodified gcode file in this folder."""
	if filename == '':
		unmodified = gcodec.getGNUGcode()
		if len( unmodified ) == 0:
			print( "There are no unmodified gcode files in this folder." )
			return
		filename = unmodified[ 0 ]
	raftPreferences = RaftPreferences()
	preferences.readPreferences( raftPreferences )
	startTime = time.time()
	print( 'File ' + gcodec.getSummarizedFilename( filename ) + ' is being chain rafted.' )
	gcodeText = gcodec.getFileText( filename )
	if gcodeText == '':
		return
	suffixFilename = filename[ : filename.rfind( '.' ) ] + '_raft.gcode'
	gcodec.writeFileText( suffixFilename, getRaftChainGcode( gcodeText, raftPreferences ) )
	print( 'The rafted file is saved as ' + gcodec.getSummarizedFilename( suffixFilename ) )
	vectorwrite.writeSkeinforgeVectorFile( suffixFilename )
	print( 'It took ' + str( int( round( time.time() - startTime ) ) ) + ' seconds to raft the file.' )

def raftFile( filename = '' ):
	"Raft a gcode linear move file.  If no filename is specified, raft the first unmodified gcode file in this folder."
	if filename == '':
		unmodified = gcodec.getUnmodifiedGCodeFiles()
		if len( unmodified ) == 0:
			print( "There are no unmodified gcode files in this folder." )
			return
		filename = unmodified[ 0 ]
	raftPreferences = RaftPreferences()
	preferences.readPreferences( raftPreferences )
	print( 'File ' + gcodec.getSummarizedFilename( filename ) + ' is being rafted.' )
	gcodeText = gcodec.getFileText( filename )
	if gcodeText == '':
		return
	suffixFilename = filename[ : filename.rfind( '.' ) ] + '_raft.gcode'
	gcodec.writeFileText( suffixFilename, getRaftGcode( gcodeText, raftPreferences ) )
	print( 'The rafted file is saved as ' + suffixFilename )
	vectorwrite.writeSkeinforgeVectorFile( suffixFilename )

class RaftSkein:
	"A class to raft a skein of extrusions."
	def __init__( self ):
		self.boundaryLoop = None
		self.boundaryLoops = []
		self.cornerHigh = Vec3( - 999999999.0, - 999999999.0, - 999999999.0 )
		self.cornerLow = Vec3( 999999999.0, 999999999.0, 999999999.0 )
		self.extrusionDiameter = 0.6
		self.extrusionWidth = 0.6
		self.feedratePerSecond = 16.0
		self.layerIndex = - 1
		self.extrusionHeight = 0.4
		self.lineIndex = 0
		self.lines = None
		self.oldLocation = None
                self.extrusionTop = 0.0
		self.operatingJump = 0.0
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
#		print( 'The operating flowrate is %s mm3/s.' % roundedFlowrate )
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
		beginY = stepBegin.real - interfaceOverhang
		endY = stepEnd.real + interfaceOverhang
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
		self.addLine( '(<layerStart> ' + euclidean.getRoundedToThreePlaces( zCenter ) + ' )' ) # Indicate that a new layer is starting.
		self.addGcodeFromFeedrateThread( 60.0 * feedrateSecond, path )
		self.extrusionTop += layerExtrusionHeight

	def addLine( self, line ):
		"Add a line of text and a newline to the output."
		self.output.write( line + "\n" )

	def addOperatingOrbits( self ):
		"Add the orbits before the operating layers."
		if len( self.boundaryLoops ) < 1:
			print( 'This should never happen, there are no boundary loops on the first layer.' )
		largestLength = - 999999999.0
		largestLoop = None
		perimeterOutset = 0.4 * self.extrusionPerimeterWidth
		greaterThanPerimeterOutset = 1.1 * perimeterOutset
		for boundaryLoop in self.boundaryLoops:
			centers = intercircle.getCentersFromLoopDirection( True, boundaryLoop, greaterThanPerimeterOutset )
			for center in centers:
				outset = intercircle.getInsetFromClockwiseLoop( center, perimeterOutset )
				if euclidean.isLargeSameDirection( outset, center, perimeterOutset ):
					loopLength = euclidean.getPolygonLength( outset )
					if loopLength > largestLength:
						largestLength = loopLength
						largestLoop = outset
		lastZ = self.oldLocation.z
                lastZ += self.operatingJump
		for point in largestLoop:
			point.z = lastZ
		self.addOrbits( largestLoop, self.raftPreferences.temperatureChangeTimeNextLayers.value )

	def addOrbits( self, loop, temperatureChangeTime ):
		"Add orbits with the extruder off."
		if len( loop ) < 1:
			print( 'Zero length loop which was skipped over, this should never happen.' )
		if temperatureChangeTime < 0.1:
			return
		timeInOrbit = 0.0
		while timeInOrbit < temperatureChangeTime:
			for point in loop:
				self.addGcodeFromFeedrateMovement( 60.0 * self.feedratePerSecond, point )
			timeInOrbit += euclidean.getPolygonLength( loop ) / self.feedratePerSecond

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
		self.addLine( '(<layerStart> ' + euclidean.getRoundedToThreePlaces( self.extrusionTop ) + ' )' ) # Indicate that a new layer is starting.
		self.addOrbits( beginLoop, self.raftPreferences.temperatureChangeTimeRaft.value )
		for baseLayerIndex in range( self.raftPreferences.baseLayers.value ):
			self.addBaseLayer( baseExtrusionWidth, baseStep, stepBegin, stepEnd )
		for interfaceLayerIndex in range( self.raftPreferences.interfaceLayers.value ):
			self.addInterfaceLayer( interfaceExtrusionWidth, interfaceStep, stepBegin, stepEnd )
		self.operatingJump = self.extrusionTop - self.cornerLow.z + halfExtrusionHeight + halfExtrusionHeight * self.raftPreferences.operatingNozzleLiftOverHalfExtrusionHeight.value
		if extrudeRaft:
			self.addTemperature( self.raftPreferences.temperatureShapeFirstLayer.value )
			squareLoop = getSquareLoop( Vec3( stepBegin.real, stepBegin.imag, self.extrusionTop ), Vec3( stepEnd.real, stepEnd.imag, self.extrusionTop ) )
			self.addOrbits( squareLoop, self.raftPreferences.temperatureChangeTimeFirstLayer.value )

	def addTemperature( self, temperature ):
		"Add a line of temperature."
		self.addLine( 'M104 S' + euclidean.getRoundedToThreePlaces( temperature ) ) # Set temperature.

	def getGcodeFromFeedrateMovement( self, feedrateMinute, point ):
		"Get a gcode movement."
		xRounded = euclidean.getRoundedToThreePlaces( point.x )
		yRounded = euclidean.getRoundedToThreePlaces( point.y )
		return "G1 X%s Y%s Z%s F%s" % ( xRounded, yRounded, euclidean.getRoundedToThreePlaces( point.z ), euclidean.getRoundedToThreePlaces( feedrateMinute ) )

	def getRaftedLine( self, splitLine ):
		"Get elevated gcode line with operating feedrate."
		location = gcodec.getLocationFromSplitLine( self.oldLocation, splitLine )
		self.oldLocation = Vec3().getFromVec3( location )
		location.z += self.operatingJump
		return self.getGcodeFromFeedrateMovement( 60.0 * self.feedratePerSecond, location )

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
		self.lines = gcodec.getTextLines( gcodeText )
		self.parseInitialization()
		if raftPreferences.addRaft.value:
			self.addRaft()
		self.addTemperature( raftPreferences.temperatureShapeFirstLayer.value )
                # Turn extruder on early. 
                # FIXME: This should be configurable. kintel 20080723
		self.addLine( "M101" )
		if self.operatingJump: print( self.operatingJump )
		for line in self.lines[ self.lineIndex : ]:
			self.parseLine( line )

	def parseInitialization( self ):
		"Parse gcode initialization and store the parameters."
		for self.lineIndex in range( len( self.lines ) ):
			line = self.lines[ self.lineIndex ]
			splitLine = line.split( ' ' )
			firstWord = ''
			if len( splitLine ) > 0:
				firstWord = splitLine[ 0 ]
			if firstWord == '(<extrusionDiameter>':
				self.extrusionDiameter = float( splitLine[ 1 ] )
				self.addFlowrate()
			elif firstWord == '(<extrusionHeight>':
				self.extrusionHeight = float( splitLine[ 1 ] )
			elif firstWord == '(<extrusionPerimeterWidth>':
				self.extrusionPerimeterWidth = float( splitLine[ 1 ] )
			elif firstWord == '(<extrusionWidth>':
				self.extrusionWidth = float( splitLine[ 1 ] )
			elif firstWord == '(<extrusionStart>':
				self.addLine( '(<procedureDone> raft )' )
				self.addLine( line )
				self.lineIndex += 1
				return
			self.addLine( line )

	def parseLine( self, line ):
		"Parse a gcode line and add it to the raft skein."
		splitLine = line.split( ' ' )
		if len( splitLine ) < 1:
			return
		firstWord = splitLine[ 0 ]
		if firstWord == 'G1':
			line = self.getRaftedLine( splitLine )
		elif firstWord == '(<boundaryPoint>':
			self.boundaryLoop.append( gcodec.getLocationFromSplitLine( None, splitLine ) )
		elif firstWord == '(<layerStart>':
			self.layerIndex += 1
			if self.operatingJump != None:
				line = '(<layerStart> ' + euclidean.getRoundedToThreePlaces( self.extrusionTop + float( splitLine[ 1 ] ) ) + ' )'
			if self.layerIndex == 1:
				self.addOperatingOrbits()
			self.boundaryLoop = None
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
		self.addRaft = preferences.BooleanPreference().getFromValue( 'Add Raft, Elevate Nozzle, Orbit and Set Altitude:', True )
		self.baseInfillDensity = preferences.FloatPreference().getFromValue( 'Base Infill Density (ratio):', 0.5 )
		self.baseLayerHeightOverExtrusionHeight = preferences.FloatPreference().getFromValue( 'Base Layer Height over Extrusion Height:', 2.0 )
		self.baseLayers = preferences.IntPreference().getFromValue( 'Base Layers (integer):', 1 )
		self.baseNozzleLiftOverHalfBaseExtrusionHeight = preferences.FloatPreference().getFromValue( 'Base Nozzle Lift over Half Base Extrusion Height (ratio):', 0.75 )
		self.bottomAltitude = preferences.FloatPreference().getFromValue( 'Bottom Altitude:', 0.0 )
		self.feedratePerSecond = preferences.FloatPreference().getFromValue( 'Feedrate (mm/s):', 16.0 )
		flowrateRadio = []
		self.flowrateDoNotAddFlowratePreference = preferences.RadioLabel().getFromRadioLabel( 'Do Not Add Flowrate', 'Flowrate Choice:', flowrateRadio, False )
		self.flowrateMetricPreference = preferences.Radio().getFromRadio( 'Metric', flowrateRadio, False )
		self.flowratePWMPreference = preferences.Radio().getFromRadio( 'PWM Setting', flowrateRadio, True )
		self.flowratePWMSetting = preferences.FloatPreference().getFromValue( 'Flowrate PWM Setting (if PWM Setting is Chosen):', 210.0 )
		self.infillOverhang = preferences.FloatPreference().getFromValue( 'Infill Overhang (ratio):', 0.1 )
		self.interfaceInfillDensity = preferences.FloatPreference().getFromValue( 'Interface Infill Density (ratio):', 0.5 )
		self.interfaceLayerHeightOverExtrusionHeight = preferences.FloatPreference().getFromValue( 'Interface Layer Height over Extrusion Height:', 1.0 )
		self.interfaceLayers = preferences.IntPreference().getFromValue( 'Interface Layers (integer):', 2 )
		self.interfaceNozzleLiftOverHalfInterfaceExtrusionHeight = preferences.FloatPreference().getFromValue( 'Interface Nozzle Lift over Half Interface Extrusion Height (ratio):', 1.0 )
		self.material = preferences.LabelDisplay().getFromName( 'Material: ' + materialName )
		self.operatingNozzleLiftOverHalfExtrusionHeight = preferences.FloatPreference().getFromValue( 'Operating Nozzle Lift over Half Extrusion Height (ratio):', 1.0 )
		self.raftOutsetRadiusOverExtrusionWidth = preferences.FloatPreference().getFromValue( 'Raft Outset Radius over Extrusion Width (ratio):', 15.0 )
		self.temperatureChangeTimeRaft = preferences.FloatPreference().getFromValue( 'Temperature Change Time of Raft (seconds):', 120.0 )
		self.temperatureChangeTimeFirstLayer = preferences.FloatPreference().getFromValue( 'Temperature Change Time of First Layer (seconds):', 120.0 )
		self.temperatureChangeTimeNextLayers = preferences.FloatPreference().getFromValue( 'Temperature Change Time of Next Layers (seconds):', 120.0 )
		self.temperatureRaft = preferences.FloatPreference().getFromValue( 'Temperature of Raft (Celcius):', 200.0 )
		self.temperatureShapeFirstLayer = preferences.FloatPreference().getFromValue( 'Temperature of Shape First Layer (Celcius):', 215.0 )
		self.temperatureShapeNextLayers = preferences.FloatPreference().getFromValue( 'Temperature of Shape Next Layers (Celcius):', 230.0 )
		self.filenameInput = preferences.Filename().getFromFilename( [ ( 'GNU Triangulated Surface text files', '*.gts' ), ( 'Gcode text files', '*.gcode' ) ], 'Open File to be Rafted', '' )
		#Create the archive, title of the execute button, title of the dialog & preferences filename.
		self.archive = [
			self.addRaft,
			self.baseNozzleLiftOverHalfBaseExtrusionHeight,
			self.baseLayerHeightOverExtrusionHeight,
			self.baseLayers,
			self.bottomAltitude,
			self.feedratePerSecond,
			self.filenameInput,
			self.flowrateDoNotAddFlowratePreference,
			self.flowrateMetricPreference,
			self.flowratePWMPreference,
			self.flowratePWMSetting,
			self.interfaceNozzleLiftOverHalfInterfaceExtrusionHeight,
			self.interfaceLayerHeightOverExtrusionHeight,
			self.interfaceLayers,
			self.material,
			self.operatingNozzleLiftOverHalfExtrusionHeight,
			self.raftOutsetRadiusOverExtrusionWidth,
			self.temperatureChangeTimeRaft,
			self.temperatureChangeTimeFirstLayer,
			self.temperatureChangeTimeNextLayers,
			self.temperatureRaft,
			self.temperatureShapeFirstLayer,
			self.temperatureShapeNextLayers ]
		self.executeTitle = 'Raft'
		self.filenamePreferences = preferences.getPreferencesFilePath( 'raft_' + materialName + '.csv' )
		self.filenameHelp = 'raft.html'
		self.title = 'Raft Preferences'

	def execute( self ):
		"Raft button has been clicked."
		filenames = multifile.getFileOrGNUUnmodifiedGcodeDirectory( self.filenameInput.value, self.filenameInput.wasCancelled )
		for filename in filenames:
			raftChainFile( filename )


def main( hashtable = None ):
        if len(sys.argv) > 1: raftChainFile(sys.argv[1])
        else:
            "Display the raft dialog."
            preferences.displayDialog( RaftPreferences() )

if __name__ == "__main__":
	main()

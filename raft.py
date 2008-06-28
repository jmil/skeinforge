"""
Raft is a script to raft the threads to partially compensate for filament shrinkage when extruded.

The important value for the raft preferences is "Maximum Raft Over Half Extrusion Width (ratio)" which is the ratio of the
maximum amount the thread will be rafted compared to half of the extrusion width. The default is 0.3, if you do not want to
use raft, set the value to zero.  With a value of one or more, the script might raft a couple of threads in opposite directions
so much that they overlap.  In theory this would be because they'll contract back to the desired places, but in practice they might
not.  The optimal value of raft will be different for different materials, so the default value of 0.3 is chosen because it will
counter the contraction a bit, but not enough to cause overlap trouble.

In general, raft will widen holes and push corners out.  The algorithm works by checking at each turning point on the
extrusion path what the direction of the thread is at a distance of "Raft from Distance over Extrusion Width (ratio)" times the
extrusion width, on both sides, and moves the thread in the opposite direction.  The magnitude of the raft increases with the
amount that the direction of the two threads is similar and by the "Maximum Raft Over Half Extrusion Width (ratio)".  The
script then also raftes the thread at two locations on the path on close to the turning points.  In practice the filament
contraction will be similar but different from the algorithm, so even once the optimal parameters are determined, the raft
script will not be able to eliminate the inaccuracies caused by contraction, but it should reduce them.  To run raft, in a shell
type:
> python strectch.py

To run raft, install python 2.x on your machine, which is avaliable from http://www.python.org/download/

To use the preferences dialog you'll also need Tkinter, which probably came with the python installation.  If it did not, look for it at:
www.tcl.tk/software/tcltk/

To export a GNU Triangulated Surface file from Art of Illusion, you can use the Export GNU Triangulated Surface script at:
http://members.axion.net/~enrique/Export%20GNU%20Triangulated%20Surface.bsh

To bring it into Art of Illusion, drop it into the folder ArtOfIllusion/Scripts/Tools/.

The GNU Triangulated Surface format is supported by Mesh Viewer, and it is described at:
http://gts.sourceforge.net/reference/gts-surfaces.html#GTS-SURFACE-WRITE

To turn an STL file into filled, rafted gcode, first import the file using the STL import plugin in the import submenu of the file menu
of Art of Illusion.  Then from the Scripts submenu in the Tools menu, choose Export GNU Triangulated Surface and select the
imported STL shape.  Then type 'python slice.py' in a shell in the folder which slice & raft are in and when the dialog pops up, set
the parameters and click 'Save Preferences'.  Then type 'python fill.py' in a shell in the folder which fill is in and when the dialog
pops up, set the parameters and click 'Save Preferences'.  Then type 'python comb.py' in a shell and when the dialog pops up,
change the parameters if you wish but the default 'Comb Hair' is fine.  Then type 'python raft.py' in a shell and when the dialog pops up,
change the parameters if you wish but the default is fine to start.  Then click 'Raft', choose the file which you exported in
Export GNU Triangulated Surface and the filled & rafted file will be saved with the suffix '_raft'.  Once you've made a shape, then
you can decide what the optimal value of "Maximum Raft Over Half Extrusion Width (ratio)" is for that material.

To write documentation for this program, open a shell in the raft.py directory, then type 'pydoc -w raft', then open 'raft.html' in
a browser or click on the '?' button in the dialog.  To write documentation for all the python scripts in the directory, type 'pydoc -w ./'.
To use other functions of raft, type 'python' in a shell to run the python interpreter, then type 'import raft' to import this program.

The computation intensive python modules will use psyco if it is available and run about twice as fast.  Psyco is described at:
http://psyco.sourceforge.net/index.html

The psyco download page is:
http://psyco.sourceforge.net/download.html

The following examples raft the files Hollow Square.gcode & Hollow Square.gts.  The examples are run in a terminal in the folder which contains
Hollow Square.gcode, Hollow Square.gts and raft.py.  The raft function will raft if 'Comb Hair' is true, which can be set in the dialog or by changing
the preferences file 'raft.csv' with a text editor or a spreadsheet program set to separate tabs.  The functions raftChainFile and
getRaftChainGcode check to see if the text has been rafted, if not they call the getFillChainGcode in fill.py to fill the text; once they
have the filled text, then they raft.


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
HDPE.raft_temp = 200
HDPE.first_layer_temp = 240
HDPE.layer_temp = 220

PCL.raft_temp = 0 // no raft
PCL.first_layer_temp = 130
PCL.layer_temp = 120

ABS.raft_temp = 200
ABS.first_layer_temp = 215
ABS.layer_temp = 230

PLA.raft_temp = 0
PLA.first_layer_temp = 180
PLA.layer_temp = 160


"""

from vec3 import Vec3
import comb
import cStringIO
import euclidean
import gcodec
import intercircle
import material
import math
import multifile
import preferences
import time
import vectorwrite


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


#initial orbit
#maybe cool for a minute
#interface pattern
#operating temperature
#interface orbit
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
	Depending on the preferences, either arcPoint, arcRadius, arcSegment, bevel or do nothing.
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
	"""Raft a gcode linear move file.  Depending on the preferences, either arcPoint, arcRadius, arcSegment, bevel or do nothing.
	If no filename is specified, raft the first unmodified gcode file in this folder."""
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
		self.cornerHigh = Vec3( - 999999999.0, - 999999999.0, - 999999999.0 )
		self.cornerLow = Vec3( 999999999.0, 999999999.0, 999999999.0 )
		self.extrusionDiameter = 0.6
		self.extrusionWidth = 0.6
		self.feedratePerSecond = 16.0
		self.layer = None
		self.layers = []
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
		print( 'addBaseLayer' )
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
		feedrateMinute = 60.0 * self.feedratePerSecond / self.baseLayerHeightOverExtrusionHeight / self.baseLayerHeightOverExtrusionHeight
		print( path )
		self.addLine( '(<layerStart> ' + euclidean.getRoundedToThreePlaces( zCenter ) + ' )' ) # Indicate that a new layer is starting.
		self.addGcodeFromFeedrateThread( feedrateMinute, path )
		self.extrusionTop += baseExtrusionHeight

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
		xRounded = euclidean.getRoundedToThreePlaces( point.x )
		yRounded = euclidean.getRoundedToThreePlaces( point.y )
		self.addLine( "G1 X%s Y%s Z%s F%s" % ( xRounded, yRounded, euclidean.getRoundedToThreePlaces( point.z ), euclidean.getRoundedToThreePlaces( feedrateMinute ) ) )

	def addLine( self, line ):
		"Add a line of text and a newline to the output."
		self.output.write( line + "\n" )

	def addOrbits( self, loop ):
		"Add orbits with the extruder off."
		if len( loop ) < 1:
			print( 'Zero length loop which was skipped over, this should never happen.' )
		temperatureChangeTime = self.raftPreferences.temperatureChangeTime.value
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
		interfaceExtrusionWidth = self.extrusionWidth * self.raftPreferences.interfaceLayerHeightOverExtrusionHeight.value
		interfaceStep = interfaceExtrusionWidth / self.raftPreferences.interfaceInfillDensity.value
		self.setCornersZ()
		halfExtrusionHeight = 0.5 * self.extrusionHeight
		self.complexHigh = complexRadius + self.cornerHigh.dropAxis( 2 )
		self.complexLow = self.cornerLow.dropAxis( 2 ) - complexRadius
		extent = self.complexHigh - self.complexLow
		extentStepX = interfaceExtrusionWidth + 2.0 * interfaceStep * math.ceil( 0.5 * ( extent.real - interfaceStep ) / interfaceStep )
		extentStepY = baseExtrusionWidth + 2.0 * baseStep * math.ceil( 0.5 * ( extent.imag - baseStep ) / baseStep )
		center = 0.5 * ( self.complexHigh + self.complexLow )
		print( self.complexLow )
		print( self.complexHigh )
		print( 'center' )
		print( center )
		extentStep = complex( extentStepX, extentStepY )
		print( extentStep )
		stepBegin = center - 0.5 * extentStep
		stepEnd = stepBegin + extentStep
		print( stepBegin )
		print( stepBegin )
		zBegin = self.extrusionTop + self.extrusionHeight
		beginLoop = getSquareLoop( Vec3( self.cornerLow.x, self.cornerLow.y, zBegin ), Vec3( self.cornerHigh.x, self.cornerHigh.y, zBegin ) )
		self.addTemperature( self.raftPreferences.temperatureRaft.value )
		self.addLine( '(<layerStart> ' + euclidean.getRoundedToThreePlaces( self.extrusionTop ) + ' )' ) # Indicate that a new layer is starting.
		self.addOrbits( beginLoop )
		for baseLayerIndex in range( self.raftPreferences.baseLayers.value ):
			self.addBaseLayer( baseExtrusionWidth, baseStep, stepBegin, stepEnd )
		self.addTemperature( self.raftPreferences.temperatureShapeFirstLayer.value )
		squareLoop = getSquareLoop( Vec3( stepBegin.real, stepBegin.imag, self.extrusionTop ), Vec3( stepEnd.real, stepEnd.imag, self.extrusionTop ) )
		self.addOrbits( squareLoop )
		self.operatingJump = self.extrusionTop - self.cornerLow.z + halfExtrusionHeight + halfExtrusionHeight * self.raftPreferences.operatingNozzleLiftOverHalfExtrusionHeight.value

	def addTemperature( self, temperature ):
		"Add a line of temperature."
		self.addLine( 'M104 S' + euclidean.getRoundedToThreePlaces( temperature ) ) # Set temperature.

	def getRaftedLine( self, splitLine ):
		"Get elevated gcode line with operating feedrate."
		line = 'G1'
		indexOfX = gcodec.indexOfStartingWithSecond( 'X', splitLine )
		if indexOfX > 0:
			line += ' X' + euclidean.getRoundedToThreePlaces( gcodec.getDoubleAfterFirstLetter( splitLine[ indexOfX ] ) )
		indexOfY = gcodec.indexOfStartingWithSecond( 'Y', splitLine )
		if indexOfY > 0:
			line += ' Y' + euclidean.getRoundedToThreePlaces( gcodec.getDoubleAfterFirstLetter( splitLine[ indexOfY ] ) )
		indexOfZ = gcodec.indexOfStartingWithSecond( 'Z', splitLine )
		if indexOfZ > 0:
			z = gcodec.getDoubleAfterFirstLetter( splitLine[ indexOfZ ] )
			if self.operatingJump != None:
				z += self.operatingJump
			line += ' Z' + euclidean.getRoundedToThreePlaces( z )
		return line + ' F' + euclidean.getRoundedToThreePlaces( 60.0 * self.feedratePerSecond )

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
		print( raftPreferences )
		if not raftPreferences.addRaft.value:
			print( 'raftPreferences.self.addRaft.value' )
		self.addTemperature( raftPreferences.temperatureShapeFirstLayer.value )
		for line in self.lines[ self.lineIndex : ]:
			self.parseLine( line )
#		print( self.output.getvalue() )

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
				roundedFlowrate = euclidean.getRoundedToThreePlaces( math.pi * self.extrusionDiameter * self.extrusionDiameter / 4.0 * self.feedratePerSecond )
				print( 'The operating flowrate is %s mm3/s.' % roundedFlowrate )
				self.addLine( 'M108 S' + euclidean.getRoundedToThreePlaces( self.raftPreferences.extruderSpeed.value ) + ' S' + roundedFlowrate )
			elif firstWord == '(<extrusionHeight>':
				self.extrusionHeight = float( splitLine[ 1 ] )
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
		elif firstWord == '(<layerStart>':
			if self.operatingJump != None:
				line = '(<layerStart> ' + euclidean.getRoundedToThreePlaces( self.extrusionTop + float( splitLine[ 1 ] ) ) + ' )'
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
		#Set the default preferences.
		self.addRaft = preferences.BooleanPreference().getFromValue( 'Add Raft, Elevate Nozzle, Orbit and Set Altitude:', True )
		self.baseInfillDensity = preferences.FloatPreference().getFromValue( 'Base Infill Density (ratio):', 0.5 )
		self.baseLayerHeightOverExtrusionHeight = preferences.FloatPreference().getFromValue( 'Base Layer Height over Extrusion Height:', 2.0 )
		self.baseLayers = preferences.IntPreference().getFromValue( 'Base Layers (integer):', 1 )
		self.baseNozzleLiftOverHalfBaseExtrusionHeight = preferences.FloatPreference().getFromValue( 'Base Nozzle Lift over Half Base Extrusion Height (ratio):', 0.75 )
		self.bottomAltitude = preferences.FloatPreference().getFromValue( 'Bottom Altitude:', 0.0 )
		self.extruderSpeed = preferences.FloatPreference().getFromValue( 'Extruder Speed:', 210.0 )
		self.feedratePerSecond = preferences.FloatPreference().getFromValue( 'Operating Feedrate (mm/s):', 16.0 )
		self.infillOverhang = preferences.FloatPreference().getFromValue( 'infill Overhang (ratio):', 0.1 )
		self.interfaceInfillDensity = preferences.FloatPreference().getFromValue( 'Interface Infill Density (ratio):', 0.5 )
		self.interfaceLayerHeightOverExtrusionHeight = preferences.FloatPreference().getFromValue( 'Interface Layer Height over Extrusion Height:', 1.0 )
		self.interfaceLayers = preferences.IntPreference().getFromValue( 'Interface Layers (integer):', 2 )
		self.interfaceNozzleLiftOverHalfBaseExtrusionHeight = preferences.FloatPreference().getFromValue( 'Interface Nozzle Lift over Half Base Extrusion Height (ratio):', 1.0 )
		self.operatingNozzleLiftOverHalfExtrusionHeight = preferences.FloatPreference().getFromValue( 'Operating Nozzle Lift over Half Extrusion Height (ratio):', 1.0 )
		self.raftOutsetRadiusOverExtrusionWidth = preferences.FloatPreference().getFromValue( 'Raft Outset Radius over Extrusion Width (ratio):', 15.0 )
		self.temperatureChangeTime = preferences.FloatPreference().getFromValue( 'Temperature Change Time (seconds):', 120.0 )
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
			self.extruderSpeed,
			self.feedratePerSecond,
			self.interfaceNozzleLiftOverHalfBaseExtrusionHeight,
			self.interfaceLayerHeightOverExtrusionHeight,
			self.interfaceLayers,
			self.operatingNozzleLiftOverHalfExtrusionHeight,
			self.raftOutsetRadiusOverExtrusionWidth,
			self.temperatureChangeTime,
			self.temperatureRaft,
			self.temperatureShapeFirstLayer,
			self.temperatureShapeNextLayers,
			self.filenameInput ]
		self.executeTitle = 'Raft'
		materialName = material.getSelectedMaterial()
		self.filenamePreferences = preferences.getPreferencesFilePath( 'raft_' + materialName + '.csv' )
		self.filenameHelp = 'raft.html'
		self.title = 'Raft Preferences'

	def execute( self ):
		"Raft button has been clicked."
		filenames = multifile.getFileOrGNUUnmodifiedGcodeDirectory( self.filenameInput.value, self.filenameInput.wasCancelled )
		for filename in filenames:
			raftChainFile( filename )


def main( hashtable = None ):
	"Display the raft dialog."
	preferences.displayDialog( RaftPreferences() )

if __name__ == "__main__":
	main()

#! /usr/bin/env python
"""
Preface is a script to convert an svg file into a prefaced gcode file.

Preface converts the svg slices into gcode extrusion layers, optionally prefaced with some gcode commands.

If "Add M110 GCode for Compatibility with Nophead's Code" is chosen, then preface will add an M110 line for compatibility with
Nophead's parser, the default is off.  If "Set Positioning to Absolute" is chosen, preface will add the G90 command to set positioning to
absolute, the default is on.  If "Set Units to Millimeters" is chosen, preface will add the G21 command to set the units to millimeters, the
default is on.  If the "Start at Home" preference is selected, the G28 go to home gcode will be added at the beginning of the file, the
default is off.  If the "Turn Extruder Off at Shut Down" preference is selected, the M103 turn extruder off gcode will be added at the end
of the file, the default is on.  If the "Turn Extruder Off at Start Up" preference is selected, the M103 turn extruder off gcode will be added
at the beginning of the file, the default is on.

Preface also gives the option of using Adrian's extruder distance E value in the gcode lines, as described at:
http://blog.reprap.org/2009/05/4d-printing.html

and in Erik de Bruijn's conversion script page at:
http://objects.reprap.org/wiki/3D-to-5D-Gcode.php

The extrusion distance format is either "Do Not Add Extrusion Distance", which gives standard XYZ & Feed Rate gcode, this is the
default choice.  If "Extrusion Distance Absolute" is chosen, the extrusion distance output will be the total extrusion distance to that gcode
line.  If "Extrusion Distance Relative" is chosen, the extrusion distance output will be the extrusion distance from the last gcode line.

When preface is generating the code, if there is a file with the name of the "Name of Start File" setting, the default being start.txt, it will be
added that to the very beginning of the gcode.  If there is a file with the name of the "Name of End File" setting, the default being end.txt,
it will be added to the very end.  Preface does not care if the text file names are capitalized, but some file systems do not handle file
name cases properly, so to be on the safe side you should give them lower case names.  Preface looks for those files in the alterations
folder in the .skeinforge folder in the home directory. If it doesn't find the file it then looks in the alterations folder in the skeinforge_tools
folder.  If it doesn't find anything there it looks in the craft_plugins folder.

The following examples preface the files Screw Holder Bottom.gcode & Screw Holder Bottom.stl.  The examples are run in a terminal in
the folder which contains Screw Holder Bottom.stl and preface.py.


> python preface.py
This brings up the dialog, after clicking 'Preface', the following is printed:
File Screw Holder Bottom.stl is being chain prefaced.
The prefaced file is saved as Screw Holder Bottom_preface.gcode


> python
Python 2.5.1 (r251:54863, Sep 22 2007, 01:43:31)
[GCC 4.2.1 (SUSE Linux)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import preface
>>> preface.main()
File Screw Holder Bottom.stl is being prefaced.
The prefaced file is saved as Screw Holder Bottom_preface.gcode
It took 3 seconds to preface the file.


>>> preface.writeOutput()
File Screw Holder Bottom.stl is being prefaced.
The prefaced file is saved as Screw Holder Bottom_preface.gcode
It took 3 seconds to preface the file.

"""

from __future__ import absolute_import
try:
	import psyco
	psyco.full()
except:
	pass
#Init has to be imported first because it has code to workaround the python bug where relative imports don't work if the module is imported as a main module.
import __init__

from skeinforge_tools.skeinforge_utilities import consecution
from skeinforge_tools.skeinforge_utilities import euclidean
from skeinforge_tools.skeinforge_utilities import gcodec
from skeinforge_tools.skeinforge_utilities import intercircle
from skeinforge_tools.skeinforge_utilities import interpret
from skeinforge_tools.skeinforge_utilities import preferences
from skeinforge_tools.skeinforge_utilities.vector3 import Vector3
from skeinforge_tools import polyfile
import os
import sys


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/28/04 $"
__license__ = "GPL 3.0"


def getCraftedText( fileName, text = '', prefacePreferences = None ):
	"Preface and convert an svg file or text."
	return getCraftedTextFromText( gcodec.getTextIfEmpty( fileName, text ), prefacePreferences )

def getCraftedTextFromText( text, prefacePreferences = None ):
	"Preface and convert an svg text."
	if gcodec.isProcedureDoneOrFileIsEmpty( text, 'preface' ):
		return text
	if prefacePreferences == None:
		prefacePreferences = preferences.getReadPreferences( PrefacePreferences() )
	return PrefaceSkein().getCraftedGcode( prefacePreferences, text )

def getDisplayedPreferences():
	"Get the displayed preferences."
	return preferences.getDisplayedDialogFromConstructor( PrefacePreferences() )

def writeOutput( fileName = '' ):
	"Preface the carving of a gcode file.  If no fileName is specified, preface the first unmodified gcode file in this folder."
	fileName = interpret.getFirstTranslatorFileNameUnmodified( fileName )
	if fileName == '':
		return
	consecution.writeChainText( fileName, ' is being chain prefaced.', 'The prefaced file is saved as ', 'preface' )


class PrefacePreferences:
	"A class to handle the preface preferences."
	def __init__( self ):
		"Set the default preferences, execute title & preferences fileName."
		#Set the default preferences.
		self.archive = []
		#Create the archive, title of the execute button, title of the dialog & preferences fileName.
		self.addM110GCodeForCompatibilityWithNopheadsCode = preferences.BooleanPreference().getFromValue( "Add M110 GCode for Compatibility with Nophead's Code", False )
		self.archive.append( self.addM110GCodeForCompatibilityWithNopheadsCode )
		self.fileNameInput = preferences.Filename().getFromFilename( interpret.getGNUTranslatorGcodeFileTypeTuples(), 'Open File to be Prefaced', '' )
		self.archive.append( self.fileNameInput )
		extrusionDistanceFormatRadio = []
		self.extrusionDistanceFormatChoiceLabel = preferences.LabelDisplay().getFromName( 'Extrusion Distance Format Choice: ' )
		self.archive.append( self.extrusionDistanceFormatChoiceLabel )
		self.extrusionDistanceDoNotAddPreference = preferences.Radio().getFromRadio( 'Do Not Add Extrusion Distance', extrusionDistanceFormatRadio, True )
		self.archive.append( self.extrusionDistanceDoNotAddPreference )
		self.extrusionDistanceAbsolutePreference = preferences.Radio().getFromRadio( 'Extrusion Distance Absolute', extrusionDistanceFormatRadio, False )
		self.archive.append( self.extrusionDistanceAbsolutePreference )
		self.extrusionDistanceRelativePreference = preferences.Radio().getFromRadio( 'Extrusion Distance Relative', extrusionDistanceFormatRadio, False )
		self.archive.append( self.extrusionDistanceRelativePreference )
		self.nameOfEndFile = preferences.StringPreference().getFromValue( 'Name of End File:', 'end.txt' )
		self.archive.append( self.nameOfEndFile )
		self.nameOfStartFile = preferences.StringPreference().getFromValue( 'Name of Start File:', 'start.txt' )
		self.archive.append( self.nameOfStartFile )
		self.setPositioningToAbsolute = preferences.BooleanPreference().getFromValue( 'Set Positioning to Absolute', True )
		self.archive.append( self.setPositioningToAbsolute )
		self.setUnitsToMillimeters = preferences.BooleanPreference().getFromValue( 'Set Units to Millimeters', True )
		self.archive.append( self.setUnitsToMillimeters )
		self.startAtHome = preferences.BooleanPreference().getFromValue( 'Start at Home', False )
		self.archive.append( self.startAtHome )
		self.turnExtruderOffAtShutDown = preferences.BooleanPreference().getFromValue( 'Turn Extruder Off at Shut Down', True )
		self.archive.append( self.turnExtruderOffAtShutDown )
		self.turnExtruderOffAtStartUp = preferences.BooleanPreference().getFromValue( 'Turn Extruder Off at Start Up', True )
		self.archive.append( self.turnExtruderOffAtStartUp )
		#Create the archive, title of the execute button, title of the dialog & preferences fileName.
		self.executeTitle = 'Preface'
		self.saveTitle = 'Save Preferences'
		preferences.setHelpPreferencesFileNameTitleWindowPosition( self, 'skeinforge_tools.craft_plugins.preface.html' )

	def execute( self ):
		"Preface button has been clicked."
		fileNames = polyfile.getFileOrDirectoryTypesUnmodifiedGcode( self.fileNameInput.value, interpret.getImportPluginFilenames(), self.fileNameInput.wasCancelled )
		for fileName in fileNames:
			writeOutput( fileName )


class PrefaceSkein:
	"A class to preface a skein of extrusions."
	def __init__( self ):
		self.boundary = None
		self.distanceFeedRate = gcodec.DistanceFeedRate()
		self.extruderActive = False
		self.lineIndex = 0
		self.oldLocation = None
		self.rotatedBoundaryLayers = []

	def addFromUpperLowerFile( self, fileName ):
		"Add lines of text from the fileName or the lowercase fileName, if there is no file by the original fileName in the directory."
		fileText = preferences.getFileInGivenPreferencesDirectory( os.path.dirname( __file__ ), fileName )
		fileLines = gcodec.getTextLines( fileText )
		self.distanceFeedRate.addLines( fileLines )

	def addGcodeFromLoop( self, loop, z ):
		"Add the remainder of the loop which does not overlap the alreadyFilledArounds loops."
		euclidean.addSurroundingLoopBeginning( loop, self, z )
		self.distanceFeedRate.addPerimeterBlock( loop, z )
		self.distanceFeedRate.addLine( '(</surroundingLoop>)' )

	def addInitializationToOutput( self ):
		"Add initialization gcode to the output."
		self.addFromUpperLowerFile( self.prefacePreferences.nameOfStartFile.value ) # Add a start file if it exists.
		self.distanceFeedRate.addTagBracketedLine( 'creator', 'skeinforge ' ) # GCode formatted comment
		versionText = gcodec.getFileText( gcodec.getVersionFileName() )
		self.distanceFeedRate.addTagBracketedLine( 'version', versionText ) # GCode formatted comment
		if self.prefacePreferences.addM110GCodeForCompatibilityWithNopheadsCode.value:
			self.distanceFeedRate.addLine( 'M110' ) # GCode for compatibility with Nophead's code.
		self.distanceFeedRate.addLine( '(<extruderInitialization>)' ) # GCode formatted comment
		if self.prefacePreferences.setPositioningToAbsolute.value:
			self.distanceFeedRate.addLine( 'G90' ) # Set positioning to absolute.
		if self.prefacePreferences.setUnitsToMillimeters.value:
			self.distanceFeedRate.addLine( 'G21' ) # Set units to millimeters.
		if self.prefacePreferences.startAtHome.value:
			self.distanceFeedRate.addLine( 'G28' ) # Start at home.
		if self.prefacePreferences.turnExtruderOffAtStartUp.value:
			self.distanceFeedRate.addLine( 'M103' ) # Turn extruder off.
		self.distanceFeedRate.addTagBracketedLine( 'decimalPlacesCarried', self.distanceFeedRate.decimalPlacesCarried )
		if self.prefacePreferences.extrusionDistanceAbsolutePreference.value:
			self.distanceFeedRate.extrusionDistanceFormat = 'absolute'
		if self.prefacePreferences.extrusionDistanceRelativePreference.value:
			self.distanceFeedRate.extrusionDistanceFormat = 'relative'
		if self.distanceFeedRate.extrusionDistanceFormat != '':
			self.distanceFeedRate.addTagBracketedLine( 'extrusionDistanceFormat', self.distanceFeedRate.extrusionDistanceFormat )
		self.distanceFeedRate.addTagBracketedLine( 'layerThickness', self.distanceFeedRate.getRounded( self.layerThickness ) )
		self.distanceFeedRate.addTagBracketedLine( 'perimeterWidth', self.distanceFeedRate.getRounded( self.perimeterWidth ) )
		self.distanceFeedRate.addTagBracketedLine( 'procedureDone', 'carve' )
		self.distanceFeedRate.addTagBracketedLine( 'procedureDone', 'preface' )
		self.distanceFeedRate.addLine( '(</extruderInitialization>)' ) # Initialization is finished, extrusion is starting.
		self.distanceFeedRate.addLine( '(<extrusion>)' ) # Initialization is finished, extrusion is starting.

	def addPathData( self, line ):
		"Add the data from the path line."
		line = line.replace( '"', ' ' )
		splitLine = line.split()
		if splitLine[ 1 ] != 'transform=':
			return
		line = line.lower()
		line = line.replace( 'm', ' ' )
		line = line.replace( 'l', ' ' )
		line = line.replace( '/>', ' ' )
		splitLine = line.split()
		if 'd=' not in splitLine:
			return
		splitLine = splitLine[ splitLine.index( 'd=' ) + 1 : ]
		pathSequence = []
		for word in splitLine:
			if word == 'z':
				loop = []
				for pathSequenceIndex in xrange( 0, len( pathSequence ), 2 ):
					coordinate = complex( pathSequence[ pathSequenceIndex ], pathSequence[ pathSequenceIndex + 1 ] )
					loop.append( coordinate )
				self.rotatedBoundaryLayer.loops.append( loop )
				pathSequence = []
			else:
				pathSequence.append( float( word ) )

	def addPreface( self, rotatedBoundaryLayer ):
		"Add preface to the carve layer."
		self.distanceFeedRate.addLine( '(<layer> %s )' % rotatedBoundaryLayer.z ) # Indicate that a new layer is starting.
		if rotatedBoundaryLayer.rotation != None:
			self.distanceFeedRate.addLine( '(<bridgeDirection> ' + str( rotatedBoundaryLayer.rotation ) + ' </bridgeDirection>)' ) # Indicate the bridge direction.
		for loop in rotatedBoundaryLayer.loops:
			self.addGcodeFromLoop( loop, rotatedBoundaryLayer.z )
		self.distanceFeedRate.addLine( '(</layer>)' )

	def addRotatedLoopLayer( self, z ):
		"Add rotated loop layer."
		self.rotatedBoundaryLayer = euclidean.RotatedLoopLayer( z )
		self.rotatedBoundaryLayers.append( self.rotatedBoundaryLayer )

	def addShutdownToOutput( self ):
		"Add shutdown gcode to the output."
		self.distanceFeedRate.addLine( '(</extrusion>)' ) # GCode formatted comment
		if self.prefacePreferences.turnExtruderOffAtShutDown.value:
			self.distanceFeedRate.addLine( 'M103' ) # Turn extruder motor off.
		self.addFromUpperLowerFile( self.prefacePreferences.nameOfEndFile.value ) # Add an end file if it exists.

	def addTextData( self, line ):
		"Add the data from the text line."
		if line.find( 'layerThickness' ) != - 1:
			return
		line = line.replace( '>', ' ' )
		line = line.replace( '<', ' ' )
		line = line.replace( ',', ' ' )
		splitLine = line.split()
		if 'Layer' not in splitLine:
			return
		splitLine = splitLine[ splitLine.index( 'Layer' ) + 1 : ]
		if 'z' not in splitLine:
			return
		zIndex = splitLine.index( 'z' )
		self.addRotatedLoopLayer( float( splitLine[ zIndex + 1 ] ) )

	def getCraftedGcode( self, prefacePreferences, gcodeText ):
		"Parse gcode text and store the bevel gcode."
		self.prefacePreferences = prefacePreferences
		gcodeText = gcodeText.replace( '\t', ' ' )
		gcodeText = gcodeText.replace( ';', ' ' )
		self.lines = gcodec.getTextLines( gcodeText )
		self.parseInitialization()
		self.addInitializationToOutput()
		for lineIndex in xrange( self.lineIndex, len( self.lines ) ):
			self.parseLine( lineIndex )
		for rotatedBoundaryLayer in self.rotatedBoundaryLayers:
			self.addPreface( rotatedBoundaryLayer )
		self.addShutdownToOutput()
		return self.distanceFeedRate.output.getvalue()

	def parseInitialization( self ):
		"Parse gcode initialization and store the parameters."
		for self.lineIndex in xrange( len( self.lines ) ):
			line = self.lines[ self.lineIndex ].lstrip()
			splitLine = gcodec.getWithoutBracketsEqualTab( line ).split()
			firstWord = gcodec.getFirstWord( splitLine )
			self.distanceFeedRate.parseSplitLine( firstWord, splitLine )
			if firstWord == 'layerThickness':
				self.layerThickness = float( splitLine[ 1 ] )
			elif firstWord == 'extrusionStart':
				return
			elif firstWord == 'perimeterWidth':
				self.perimeterWidth = float( splitLine[ 1 ] )

	def parseLine( self, lineIndex ):
		"Parse a gcode line and add it to the preface skein."
		line = self.lines[ lineIndex ].lstrip()
		splitLine = line.split()
		if len( splitLine ) < 1:
			return
		firstWord = splitLine[ 0 ]
		if firstWord == '(<bridgeDirection>' or firstWord == '<!--bridgeDirection-->':
			secondWordWithoutBrackets = splitLine[ 1 ].replace( '(', '' ).replace( ')', '' )
			self.rotatedBoundaryLayer.rotation = complex( secondWordWithoutBrackets )
		elif firstWord == '<path':
			self.addPathData( line )
		elif firstWord == '<text':
			self.addTextData( line )


def main():
	"Display the preface dialog."
	if len( sys.argv ) > 1:
		writeOutput( ' '.join( sys.argv[ 1 : ] ) )
	else:
		getDisplayedPreferences().root.mainloop()

if __name__ == "__main__":
	main()

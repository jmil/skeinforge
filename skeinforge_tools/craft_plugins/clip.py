"""
Clip is a script to clip loop ends.

The default 'Activate Clip' checkbox is on.  When it is on, the functions described below will work, when it is off, the functions
will not be called.

Clip clips the ends of loops to prevent bumps from forming.  The "Clip Over Extrusion Width (ratio)" is the ratio of the amount
each end of the loop is clipped over the extrusion width.  The total gap will therefore be twice the clip.  If the ratio is too high
loops will have a gap, if the ratio is too low there will be a bulge at the loop ends.  To run clip, in a shell type:
> python clip.py

The following examples clip the files Screw Holder Bottom.gcode & Screw Holder Bottom.stl.  The examples are run in a terminal in the
folder which contains Screw Holder Bottom.gcode, Screw Holder Bottom.stl and clip.py.  The clip function will clip if 'Activate Clip' is true,
which can be set in the dialog or by changing the preferences file 'clip.csv' in the '.skeinforge' folder in your home directory
with a text editor or a spreadsheet program set to separate tabs.  The functions writeOutput and getChainGcode check
to see if the text has been clipped, if not they call getChainGcode in comb.py to comb the text; once they have the
combed text, then they clip.


> python clip.py
This brings up the dialog, after clicking 'Clip', the following is printed:
File Screw Holder Bottom.stl is being chain clipped.
The clipped file is saved as Screw Holder Bottom_clip.gcode


> python clip.py Screw Holder Bottom.stl
File Screw Holder Bottom.stl is being chain clipped.
The clipped file is saved as Screw Holder Bottom_clip.gcode


> python
Python 2.5.1 (r251:54863, Sep 22 2007, 01:43:31)
[GCC 4.2.1 (SUSE Linux)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import clip
>>> clip.main()
This brings up the clip dialog.


>>> clip.writeOutput()
Screw Holder Bottom.stl
File Screw Holder Bottom.stl is being chain clipped.
The clipped file is saved as Screw Holder Bottom_clip.gcode

"""

from __future__ import absolute_import
#Init has to be imported first because it has code to workaround the python bug where relative imports don't work if the module is imported as a main module.
import __init__

from skeinforge_tools.skeinforge_utilities import consecution
from skeinforge_tools.skeinforge_utilities import euclidean
from skeinforge_tools.skeinforge_utilities import gcodec
from skeinforge_tools.skeinforge_utilities import intercircle
from skeinforge_tools.skeinforge_utilities import preferences
from skeinforge_tools.skeinforge_utilities import interpret
from skeinforge_tools import polyfile
import math
import sys


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


def getCraftedText( fileName, text, clipPreferences = None ):
	"Clip a gcode linear move file or text."
	return getCraftedTextFromText( gcodec.getTextIfEmpty( fileName, text ), clipPreferences )

def getCraftedTextFromText( gcodeText, clipPreferences = None ):
	"Clip a gcode linear move text."
	if gcodec.isProcedureDoneOrFileIsEmpty( gcodeText, 'clip' ):
		return gcodeText
	if clipPreferences == None:
		clipPreferences = preferences.getReadPreferences( ClipPreferences() )
	if not clipPreferences.activateClip.value:
		return gcodeText
	return ClipSkein().getCraftedGcode( clipPreferences, gcodeText )

def getDisplayedPreferences():
	"Get the displayed preferences."
	return preferences.getDisplayedDialogFromConstructor( ClipPreferences() )

def writeOutput( fileName = '' ):
	"Clip a gcode linear move file.  Chain clip the gcode if it is not already clipped.  If no fileName is specified, clip the first unmodified gcode file in this folder."
	fileName = interpret.getFirstTranslatorFileNameUnmodified( fileName )
	if fileName == '':
		return
	consecution.writeChainText( fileName, ' is being chain clipped.', 'The clipped file is saved as ', 'clip' )


class ClipPreferences:
	"A class to handle the clip preferences."
	def __init__( self ):
		"Set the default preferences, execute title & preferences fileName."
		#Set the default preferences.
		self.archive = []
		self.activateClip = preferences.BooleanPreference().getFromValue( 'Activate Clip', True )
		self.archive.append( self.activateClip )
		self.clipOverExtrusionWidth = preferences.FloatPreference().getFromValue( 'Clip Over Extrusion Width (ratio):', 0.15 )
		self.archive.append( self.clipOverExtrusionWidth )
		self.fileNameInput = preferences.Filename().getFromFilename( interpret.getGNUTranslatorGcodeFileTypeTuples(), 'Open File to be Clipped', '' )
		self.archive.append( self.fileNameInput )
		#Create the archive, title of the execute button, title of the dialog & preferences fileName.
		self.executeTitle = 'Clip'
		self.saveTitle = 'Save Preferences'
		preferences.setHelpPreferencesFileNameTitleWindowPosition( self, 'skeinforge_tools.craft_plugins.clip.html' )

	def execute( self ):
		"Clip button has been clicked."
		fileNames = polyfile.getFileOrDirectoryTypesUnmodifiedGcode( self.fileNameInput.value, interpret.getImportPluginFilenames(), self.fileNameInput.wasCancelled )
		for fileName in fileNames:
			writeOutput( fileName )


class ClipSkein:
	"A class to clip a skein of extrusions."
	def __init__( self ):
		self.distanceFeedRate = gcodec.DistanceFeedRate()
		self.feedrateMinute = None
		self.isLoopPerimeter = False
		self.loopPath = None
		self.lineIndex = 0
		self.oldLocation = None

	def addGcodeFromThreadZ( self, thread, z ):
		"Add a gcode thread to the output."
		if len( thread ) > 0:
			self.distanceFeedRate.addGcodeMovementZWithFeedRate( self.travelFeedratePerMinute, thread[ 0 ], z )
		else:
			print( "zero length vertex positions array which was skipped over, this should never happen" )
		if len( thread ) < 2:
			print( "thread of only one point in clip, this should never happen" )
			print( thread )
			return
		self.distanceFeedRate.addLine( 'M101' )
		for point in thread[ 1 : ]:
			self.distanceFeedRate.addGcodeMovementZWithFeedRate( self.feedrateMinute, point, z )

	def addTailoredLoopPath( self ):
		"Add a clipped and jittered loop path."
		if self.clipLength > 0.0:
			self.loopPath.path = euclidean.getClippedLoopPath( self.clipLength, self.loopPath.path )
			self.loopPath.path = euclidean.getSimplifiedPath( self.loopPath.path, self.perimeterWidth )
		self.addGcodeFromThreadZ( self.loopPath.path, self.loopPath.z )
		self.loopPath = None

	def getCraftedGcode( self, clipPreferences, gcodeText ):
		"Parse gcode text and store the clip gcode."
		self.lines = gcodec.getTextLines( gcodeText )
		self.parseInitialization( clipPreferences )
		for self.lineIndex in xrange( self.lineIndex, len( self.lines ) ):
			line = self.lines[ self.lineIndex ]
			self.parseLine( line )
		return self.distanceFeedRate.output.getvalue()

	def isNextExtruderOn( self ):
		"Determine if there is an extruder on command before a move command."
		line = self.lines[ self.lineIndex ]
		splitLine = line.split()
		for afterIndex in xrange( self.lineIndex + 1, len( self.lines ) ):
			line = self.lines[ afterIndex ]
			splitLine = line.split()
			firstWord = gcodec.getFirstWord( splitLine )
			if firstWord == 'G1' or firstWord == 'M103':
				return False
			elif firstWord == 'M101':
				return True
		return False

	def linearMove( self, splitLine ):
		"Add to loop path if this is a loop or path."
		location = gcodec.getLocationFromSplitLine( self.oldLocation, splitLine )
		self.feedrateMinute = gcodec.getFeedrateMinute( self.feedrateMinute, splitLine )
		if self.isLoopPerimeter:
			if self.isNextExtruderOn():
				self.loopPath = euclidean.PathZ( location.z )
		if self.loopPath != None:
			self.loopPath.path.append( location.dropAxis( 2 ) )
		self.oldLocation = location

	def parseInitialization( self, clipPreferences ):
		"Parse gcode initialization and store the parameters."
		for self.lineIndex in xrange( len( self.lines ) ):
			line = self.lines[ self.lineIndex ]
			splitLine = line.split()
			firstWord = gcodec.getFirstWord( splitLine )
			self.distanceFeedRate.parseSplitLine( firstWord, splitLine )
			if firstWord == '(</extruderInitialization>)':
				self.distanceFeedRate.addLine( '(<procedureDone> clip </procedureDone>)' )
				return
			elif firstWord == '(<perimeterWidth>':
				self.perimeterWidth = float( splitLine[ 1 ] )
				self.clipLength = clipPreferences.clipOverExtrusionWidth.value * self.perimeterWidth
			elif firstWord == '(<travelFeedratePerSecond>':
				self.travelFeedratePerMinute = 60.0 * float( splitLine[ 1 ] )
			self.distanceFeedRate.addLine( line )

	def parseLine( self, line ):
		"Parse a gcode line and add it to the clip skein."
		splitLine = line.split()
		if len( splitLine ) < 1:
			return
		firstWord = splitLine[ 0 ]
		if firstWord == 'G1':
			self.linearMove( splitLine )
		elif firstWord == 'M103':
			self.isLoopPerimeter = False
			if self.loopPath != None:
				self.addTailoredLoopPath()
		if firstWord == '(<loop>)' or firstWord == '(<perimeter>)':
			self.isLoopPerimeter = True
		if self.loopPath == None:
			self.distanceFeedRate.addLine( line )


def main():
	"Display the clip dialog."
	if len( sys.argv ) > 1:
		writeOutput( ' '.join( sys.argv[ 1 : ] ) )
	else:
		getDisplayedPreferences().root.mainloop()

if __name__ == "__main__":
	main()

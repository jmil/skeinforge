"""
Raftless is a script to prepare a gcode file for raftless printing.

The Raftless script has been written by Eberhard Rensch (http://www.pleasantsoftware.com/developer/3d) and is based on the skeinforge tool chain by Enrique Perez (perez_enrique@yahoo.com).

In order to install the Raftless script within the skeinforge tool chain, put raftless.py in the skeinforge_tool/craft_plugins folder. Then edit  skeinforge_tool/profile_plugins/extrusion.py and add the Raftless script to the tool chain sequence by inserting 'raftless' into the tool sequence  in getCraftSequence(). The best place is at the end of the sequence, right before 'export'.

==Operation==
The default 'Activate Raftless' checkbox is off, since the mutually exclusive 'Raft' script is activated by default.
In order to use the Raftless script, you want to deactivate the Raft script first. If both scripts, Raft and Raftless, are activated, the Raftless script (which runs after the Raft script) automatically detects the already created raft. In this case, the Raftless script is skipped and a warning message is printed to the console.

==Settings==
===1st Perimeter Feed Rate over Feed Rate===
The "1st Perimeter Feed Rate over Feed Rate" preference defines the feed rate during the extrusion of the 1st layer's perimeter lines. The preference is a ratio of the normal extrusion feed rate as configured in the 'Speed' script. The default value is .5, which means half the normal feed rate.

===1st Perimeter Flow Rate over Flow Rate===
The "1st Perimeter Flow Rate over Flow Rate" preference is the ratio of the filament feedrate during the extrusion of the 1st layer's perimeter lines. Since the feed rate is slower than normal, you might want to reduce also the flow rate in this case. This preference is a ratio of the normal flow rate (as configured in the 'Speed' script). The default is 1. (same flow rate as normal).

===Add Extrusion Intro===
If "Add Extrusion Intro" is on, an additional straight extrusion line is added to the start of the first perimeter.
This line starts at the coordinates 'Extrusion Intro Max X Absolute'/'Extrusion Intro Max Y Absolute'. However, these both values are absolute values. The script automatically negates one or both of these values, according to the location of the first regualar extrusion.
Please note, that Add Extrusion Intro doesn't check for collisions with the perimeter lines. If necessary, you want to change the max X/Y values manually.


The following examples raftless the file Screw Holder Bottom.stl.  The examples are run in a terminal in the folder which contains Screw Holder Bottom.stl and raftless.py.


> python raftless.py
This brings up the raftless dialog.


> python raftless.py Screw Holder Bottom.stl
The raftless tool is parsing the file:
Screw Holder Bottom.stl
..
The raftless tool has created the file:
Screw Holder Bottom_raftless.gcode


> python
Python 2.5.1 (r251:54863, Sep 22 2007, 01:43:31)
[GCC 4.2.1 (SUSE Linux)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import raftless
>>> raftless.main()
This brings up the raftless dialog.


>>> raftless.writeOutput( 'Screw Holder Bottom.stl' )
Screw Holder Bottom.stl
The raftless tool is parsing the file:
Screw Holder Bottom.stl
..
The raftless tool has created the file:
Screw Holder Bottom_raftless.gcode

"""


from __future__ import absolute_import
#Init has to be imported first because it has code to workaround the python bug where relative imports don't work if the module is imported as a main module.
import __init__

from skeinforge_tools import profile
from skeinforge_tools.meta_plugins import polyfile
from skeinforge_tools.skeinforge_utilities import consecution
from skeinforge_tools.skeinforge_utilities import euclidean
from skeinforge_tools.skeinforge_utilities import gcodec
from skeinforge_tools.skeinforge_utilities import interpret
from skeinforge_tools.skeinforge_utilities import settings
import sys

__author__ = "Eberhard Rensch (eberhard@pleasantsoftware.com)"
__date__ = "$Date: 2010/02/17 $"
__license__ = "GPL 3.0"


def getCraftedText( fileName, text = '', repository = None ):
	"Raftless the file or text."
	return getCraftedTextFromText( gcodec.getTextIfEmpty( fileName, text ), repository )

def getCraftedTextFromText( gcodeText, repository = None ):
	"Raftless a gcode linear move text."
	if gcodec.isProcedureDoneOrFileIsEmpty( gcodeText, 'raft' ):
		print( 'The gcode contains already a raft. Skipping raftless tool.' )
		return gcodeText
	if gcodec.isProcedureDoneOrFileIsEmpty( gcodeText, 'raftless' ):
		return gcodeText
	if repository == None:
		repository = settings.getReadRepository( RaftlessRepository() )
	if not repository.activateRaftless.value:
		return gcodeText
	return RaftlessSkein().getCraftedGcode( gcodeText, repository )

#def getRepositoryConstructor():
#	"Get the repository constructor."
#	return RaftlessRepository()

def getNewRepository():
	"Get the repository constructor."
	return RaftlessRepository()

def writeOutput( fileName = '' ):
	"Raftless a gcode linear move file."
	fileName = interpret.getFirstTranslatorFileNameUnmodified( fileName )
	if fileName == '':
		return
	consecution.writeChainTextWithNounMessage( fileName, 'raftless' )


class RaftlessRepository:
	"A class to handle the raftless settings."
	def __init__( self ):
		"Set the default settings, execute title & settings fileName."
		profile.addListsToCraftTypeRepository( 'skeinforge_tools.craft_plugins.raftless.html', self )
		self.fileNameInput = settings.FileNameInput().getFromFileName( interpret.getGNUTranslatorGcodeFileTypeTuples(), 'Open File for Raftless', self, '' )
		self.activateRaftless = settings.BooleanSetting().getFromValue( 'Activate Raftless', self, False )
		# ( min_value, 'Parameter Description:', self, max_value, default_value )
		self.firstPerimeterFeedrateOverFeedrate = settings.FloatSpin().getFromValue( 0.1, '1st Perimeter Feed Rate over Feed Rate (ratio):', self, 3.0, 0.5 )
		self.firstPerimeterFlowrateOverFlowrate = settings.FloatSpin().getFromValue( 0.1, '1st Perimeter Flow Rate over Flow Rate (ratio):', self, 3.0, 1.0 )
		self.addExtrusionIntro = settings.BooleanSetting().getFromValue( 'Add Extrusion Intro:', self, True )
		self.absMaxXIntro = settings.FloatSpin().getFromValue( 0.0, 'Extrusion Intro Max X Absolute (mm):', self, 100.0, 40.0 )
		self.absMaxYIntro = settings.FloatSpin().getFromValue( 0.0, 'Extrusion Intro Max Y Absolute (mm):', self, 100.0, 40.0 )
		#Create the archive, title of the execute button, title of the dialog & settings fileName.
		self.executeTitle = 'Raftless'

	def execute( self ):
		"Raftless button has been clicked."
		fileNames = polyfile.getFileOrDirectoryTypesUnmodifiedGcode( self.fileNameInput.value, interpret.getImportPluginFilenames(), self.fileNameInput.wasCancelled )
		for fileName in fileNames:
			writeOutput( fileName )
			
			

class RaftlessSkein:
	"A class to raftless a skein of extrusions."
	def __init__( self ):
		self.distanceFeedRate = gcodec.DistanceFeedRate()
		self.feedRateMinute = 900.
		self.currentLayer = 0
		self.firstLinearGcodeMovement = None;
		self.firstPerimeterFlowrateString = None
		self.isExtruderActive = False
		self.isSurroundingLoop = False
		self.lineIndex = 0
		self.lines = None
		self.operatingFlowrateString = None
		self.wantsExtrusionIntro = False
		
	def addExtrusionIntro( self, line ):
		"Adds the additional linear gcode movement for the extrusion intro."
		splitG1Line = self.firstLinearGcodeMovement.split()
		firstMovementLocation = gcodec.getLocationFromSplitLine(None, splitG1Line)
		firstMovementFeedrate = gcodec.getFeedRateMinute(self.feedRateMinute/self.repository.firstPerimeterFeedrateOverFeedrate.value, splitG1Line)
		introX = abs( self.repository.absMaxXIntro.value )
		introY = abs( self.repository.absMaxYIntro.value )
		xAxisFirst=False
		if abs( firstMovementLocation.x ) < abs( firstMovementLocation.y ):
			xAxisFirst=True	
		if (xAxisFirst and firstMovementLocation.x > 0) or (not xAxisFirst and firstMovementLocation.x < 0):
			introX = -introX;
		if (xAxisFirst and firstMovementLocation.y < 0) or (not xAxisFirst and firstMovementLocation.y > 0):
			introY = -introY;
		introLine = self.deriveIntroLine(self.firstLinearGcodeMovement, splitG1Line, introX, introY, firstMovementFeedrate)
		self.distanceFeedRate.addLine(introLine)
		self.distanceFeedRate.addLine( line )
		if xAxisFirst:
			introLine = self.deriveIntroLine(self.firstLinearGcodeMovement, splitG1Line, firstMovementLocation.x, introY, self.feedRateMinute)
		else:
			introLine = self.deriveIntroLine(self.firstLinearGcodeMovement, splitG1Line, introX, firstMovementLocation.y, self.feedRateMinute)
		self.distanceFeedRate.addLine(introLine)
		introLine = self.getRaftlessSpeededLine(self.firstLinearGcodeMovement, splitG1Line)
		self.distanceFeedRate.addLine(introLine)
		self.wantsExtrusionIntro = False
		
	def deriveIntroLine( self, line, splitG1Line, introX, introY, introFeed ):
		"Creates a new linear gcode movement, derived from self.firstLinearGcodeMovement."
		roundedXString = 'X' + self.distanceFeedRate.getRounded( introX )
		roundedYString = 'Y' + self.distanceFeedRate.getRounded( introY )
		roundedFString = 'F' + self.distanceFeedRate.getRounded( introFeed )
		indexOfX = gcodec.indexOfStartingWithSecond( 'X', splitG1Line )
		introLine = line
		if indexOfX == -1:
			introLine = introLine + ' ' + roundedXString;
		else:
			word = splitG1Line[ indexOfX ]
			introLine = introLine.replace( word, roundedXString )
		indexOfY = gcodec.indexOfStartingWithSecond( 'Y', splitG1Line )
		if indexOfY == -1:
			introLine = introLine + ' ' + roundedYString;
		else:
			word = splitG1Line[ indexOfY ]
			introLine = introLine.replace( word, roundedYString )
		indexOfF = gcodec.indexOfStartingWithSecond( 'F', splitG1Line )
		if indexOfF == -1:
			introLine = introLine + ' ' + roundedFString;
		else:
			word = splitG1Line[ indexOfF ]
			introLine = introLine.replace( word, roundedFString )
		return introLine;	
									  
	def getCraftedGcode( self, gcodeText, repository ):
		"Parse gcode text and store the raftless gcode."
		self.repository = repository
		self.wantsExtrusionIntro=self.repository.addExtrusionIntro.value
		self.lines = gcodec.getTextLines( gcodeText )
		self.parseInitialization()
		for line in self.lines[ self.lineIndex : ]:
			self.parseLine( line )
		return self.distanceFeedRate.output.getvalue()

	def getRaftlessSpeededLine( self, line, splitLine ):
		"Get gcode line with raftless feed rate."
		roundedFString = 'F' + self.distanceFeedRate.getRounded( self.feedRateMinute )
		indexOfF = gcodec.indexOfStartingWithSecond( 'F', splitLine )
		if indexOfF == - 1:
			return line + ' ' + roundedFString
		word = splitLine[ indexOfF ]
		return line.replace( word, roundedFString )

	def parseInitialization( self ):
		"Parse gcode initialization and store the parameters."
		for self.lineIndex in xrange( len( self.lines ) ):
			line = self.lines[ self.lineIndex ]
			splitLine = line.split()
			firstWord = gcodec.getFirstWord( splitLine )
			self.distanceFeedRate.parseSplitLine( firstWord, splitLine )
			if firstWord == 'M108':
				self.setOperatingFlowString( splitLine )
			elif firstWord == '(<operatingFeedRatePerSecond>':
				self.feedRateMinute = 60.0 * float( splitLine[ 1 ] ) * self.repository.firstPerimeterFeedrateOverFeedrate.value
			elif firstWord == '(</extruderInitialization>)':
				self.distanceFeedRate.addLine( '(<procedureDone> raftless </procedureDone>)' )
				return
			self.distanceFeedRate.addLine( line )

	def parseLine( self, line ):
		"Parse a gcode line and add it to the raftless skein."
		splitLine = line.split()
		if len( splitLine ) < 1:
			return
		firstWord = splitLine[ 0 ]
		if firstWord == '(<layer>':
			self.currentLayer=self.currentLayer+1
		elif firstWord == '(<surroundingLoop>)':
			self.isSurroundingLoop = True
		elif firstWord == '(</surroundingLoop>)':
			self.isSurroundingLoop = False
		elif firstWord == 'M108':
			self.setOperatingFlowString( splitLine )
		elif firstWord == 'G1':
		    if self.wantsExtrusionIntro and self.firstLinearGcodeMovement == None:
		    	 self.firstLinearGcodeMovement = line
		    	 return
		    if self.currentLayer==1 and self.isSurroundingLoop and self.isExtruderActive:
		    	line = self.getRaftlessSpeededLine( line, splitLine )
		elif firstWord == 'M101':
			if self.currentLayer==1 and self.isSurroundingLoop and self.firstPerimeterFlowrateString and self.firstPerimeterFlowrateString != self.operatingFlowrateString:
				self.distanceFeedRate.addLine( 'M108 S' + self.firstPerimeterFlowrateString )
			self.isExtruderActive = True
			if self.wantsExtrusionIntro and self.firstLinearGcodeMovement != None:
				self.addExtrusionIntro(line)
				return
		elif firstWord == 'M103':
			self.distanceFeedRate.addLine( line )
			self.isExtruderActive = False
			self.restorePreviousFlowrateIfNecessary()
			return
		self.distanceFeedRate.addLine( line )
		
	def restorePreviousFlowrateIfNecessary( self ):
		if self.operatingFlowrateString != None and self.firstPerimeterFlowrateString != self.operatingFlowrateString:
			self.distanceFeedRate.addLine( 'M108 S' + self.operatingFlowrateString )
		
	def setOperatingFlowString( self, splitLine ):
		"Set the operating flow string from the split line."
		self.operatingFlowrateString = splitLine[ 1 ][ 1 : ]
		self.firstPerimeterFlowrateString = self.distanceFeedRate.getRounded( float( self.operatingFlowrateString ) * self.repository.firstPerimeterFlowrateOverFlowrate.value )

def main():
	"Display the raftless dialog."
	if len( sys.argv ) > 1:
		writeOutput( ' '.join( sys.argv[ 1 : ] ) )
	else:
		settings.startMainLoopFromConstructor( getRepositoryConstructor() )

if __name__ == "__main__":
	main()

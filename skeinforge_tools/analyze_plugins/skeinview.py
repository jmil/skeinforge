"""
Skeinview is a script to display each layer of a gcode file.

Skeinview is derived from Nophead's preview script.  The extruded lines are in the resistor colors red, orange, yellow, green,
blue, purple & brown.  When the extruder is off, the travel line is grey.  Skeinview is useful for a detailed view of the extrusion,
behold is better to see the orientation of the shape.  To get an initial overview of the skein, when the skeinview display window
appears, click the Soar button.

The default 'Activate Skeinview' checkbox is on.  When it is on, the functions described below will work when called from the
skeinforge toolchain, when it is off, the functions will not be called from the toolchain.  The functions will still be called, whether
or not the 'Activate Skeinview' checkbox is on, when skeinview is run directly.  Skeinview has trouble separating the layers
when it reads gcode without comments.

If "Draw Arrows" is selected, arrows will be drawn at the end of each line segment, the default is on.  If "Go Around Extruder
Off Travel" is selected, the display will include the travel when the extruder is off, which means it will include the nozzle wipe
path if any.  The "Pixels over Extrusion Width" preference is the scale of the image, the higher the number, the greater the
size of the display.  The "Screen Horizontal Inset" determines how much the display will be inset in the horizontal direction
from the edge of screen, the higher the number the more it will be inset and the smaller it will be, the default is one hundred.
The "Screen Vertical Inset" determines how much the display will be inset in the vertical direction from the edge of screen, the
default is fifty.  The "Slide Show Rate" determines how fast the layer index changes when soar or dive is operating.

On the skeinview display window, the Up button increases the layer index shown by one, and the Down button decreases the
layer index by one.  When the index displayed in the index field is changed then "<return>" is hit, the layer index shown will
be set to the index field, to a mimimum of zero and to a maximum of the highest index layer.  The Soar button increases the
layer index at the "Slide Show Rate", and the Dive button decreases the layer index at the slide show rate.  The soaring and
diving stop when return is hit in the index field, or when the up or down button is hit, or when the top or bottom layer is
reached.  When the mouse is clicked, the line closest to the mouse pointer will be printed in the console.  If 'Display Line Text
when Mouse Moves' is selected, then the line closest to the mouse pointer will be displayed above the mouse pointer.

An explanation of the gcodes is at:
http://reprap.org/bin/view/Main/Arduino_GCode_Interpreter

and at:
http://reprap.org/bin/view/Main/MCodeReference

A gode example is at:
http://forums.reprap.org/file.php?12,file=565

This example displays a skein view for the gcode file Screw Holder.gcode.  This example is run in a terminal in the folder which
contains Screw Holder.gcode and skeinview.py.


> python skeinview.py
This brings up the skeinview dialog.


> python skeinview.py Screw Holder.gcode
This brings up a skein window to view each layer of a gcode file.


> python
Python 2.5.1 (r251:54863, Sep 22 2007, 01:43:31)
[GCC 4.2.1 (SUSE Linux)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import skeinview
>>> skeinview.main()
This brings up the skeinview dialog.


>>> skeinview.displayFile()
This brings up a skein window to view each layer of a gcode file.

"""

from __future__ import absolute_import
#Init has to be imported first because it has code to workaround the python bug where relative imports don't work if the module is imported as a main module.
import __init__

from skeinforge_tools.skeinforge_utilities.vector3 import Vector3
from skeinforge_tools.skeinforge_utilities import euclidean
from skeinforge_tools.skeinforge_utilities import gcodec
from skeinforge_tools.skeinforge_utilities import preferences
from skeinforge_tools import polyfile
import sys
import threading

__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


def displayFile( fileName ):
	"Display a gcode file in a skeinview window."
	gcodeText = gcodec.getFileText( fileName )
	displayFileGivenText( gcodeText )

def displayFileGivenText( gcodeText, skeinviewPreferences = None ):
	"Display a gcode file in a skeinview window given the text."
	if gcodeText == '':
		return
	if skeinviewPreferences == None:
		skeinviewPreferences = SkeinviewPreferences()
		preferences.getReadPreferences( skeinviewPreferences )
	displayFileGivenTextPreferences( gcodeText, skeinviewPreferences )

def displayFileGivenTextPreferences( gcodeText, skeinviewPreferences ):
	"Display a gcode file in a skeinview window given the text and preferences."
	skein = SkeinviewSkein()
	skein.parseGcode( gcodeText, skeinviewPreferences )
	SkeinWindow( skein, skeinviewPreferences )

def getPreferencesConstructor():
	"Get the preferences constructor."
	return SkeinviewPreferences()

def writeOutput( fileName, gcodeText = '' ):
	"Display a skeinviewed gcode file for a skeinforge gcode file, if 'Activate Skeinview' is selected."
	skeinviewPreferences = SkeinviewPreferences()
	preferences.getReadPreferences( skeinviewPreferences )
	if skeinviewPreferences.activateSkeinview.value:
		gcodeText = gcodec.getTextIfEmpty( fileName, gcodeText )
		displayFileGivenText( gcodeText, skeinviewPreferences )


class ColoredLine:
	"A colored line."
	def __init__( self, colorName, complexBegin, complexEnd, line, lineIndex, width ):
		"Set the color name and corners."
		self.colorName = colorName
		self.complexBegin = complexBegin
		self.complexEnd = complexEnd
		self.line = line
		self.lineIndex = lineIndex
		self.width = width
	
	def __repr__( self ):
		"Get the string representation of this colored line."
		return '%s, %s, %s, %s' % ( self.colorName, self.complexBegin, self.complexEnd, self.line, self.lineIndex, self.width )


class SkeinviewPreferences:
	"A class to handle the skeinview preferences."
	def __init__( self ):
		"Set the default preferences, execute title & preferences fileName."
		#Set the default preferences.
		self.archive = []
		self.phoenixPreferenceTable = {}
		self.updatePreferences = []
		self.activateSkeinview = preferences.BooleanPreference().getFromValue( 'Activate Skeinview', True )
		self.archive.append( self.activateSkeinview )
		self.displayLineTextWhenMouseMoves = preferences.BooleanPreference().getFromValue( 'Display Line Text when Mouse Moves', False )
		self.addToArchivePhoenixUpdate( self.displayLineTextWhenMouseMoves )
		self.drawArrows = preferences.BooleanPreference().getFromValue( 'Draw Arrows', True )
		self.addToArchiveUpdate( self.drawArrows )
		self.fileNameInput = preferences.Filename().getFromFilename( [ ( 'Gcode text files', '*.gcode' ) ], 'Open File to Skeinview', '' )
		self.archive.append( self.fileNameInput )
		self.goAroundExtruderOffTravel = preferences.BooleanPreference().getFromValue( 'Go Around Extruder Off Travel', False )
		self.addToArchivePhoenixUpdate( self.goAroundExtruderOffTravel )
		self.pixelsPerMillimeter = preferences.FloatPreference().getFromValue( 'Pixels per Millimeter (ratio):', 15.0 )
		self.addToArchivePhoenixUpdate( self.pixelsPerMillimeter )
		self.screenHorizontalInset = preferences.IntPreference().getFromValue( 'Screen Horizontal Inset (pixels):', 100 )
		self.addToArchivePhoenixUpdate( self.screenHorizontalInset )
		self.screenVerticalInset = preferences.IntPreference().getFromValue( 'Screen Vertical Inset (pixels):', 50 )
		self.addToArchivePhoenixUpdate( self.screenVerticalInset )
		self.slideShowRate = preferences.FloatPreference().getFromValue( 'Slide Show Rate (layers/second):', 1.0 )
		self.addToArchiveUpdate( self.slideShowRate )
		self.windowPositionSkeinviewDynamicPreferences = preferences.WindowPosition().getFromValue( 'windowPositionSkeinview Dynamic Preferences', '0+0' )
		self.addToArchiveUpdate( self.windowPositionSkeinviewDynamicPreferences )
		#Create the archive, title of the execute button, title of the dialog & preferences fileName.
		self.executeTitle = 'Skeinview'
		self.saveCloseTitle = 'Save and Close'
		preferences.setHelpPreferencesFileNameTitleWindowPosition( self, 'skeinforge_tools.analyze_plugins.skeinview.html' )
		self.windowPositionPreferences.windowPositionName = None
		self.updateFunction = None

	def addToArchiveUpdate( self, archivablePreference ):
		"Add preference to the archive and the update preferences."
		self.archive.append( archivablePreference )
		self.updatePreferences.append( archivablePreference )

	def addToArchivePhoenixUpdate( self, archivablePreference ):
		"Add preference to the archive, the phoenix preferences, and the update preferences."
		self.addToArchiveUpdate( archivablePreference )
		self.phoenixPreferenceTable[ archivablePreference ] = None

	def displayImmediateUpdateDialog( self ):
		"Display the immediate update dialog."
		self.executeTitle = None
		self.saveCloseTitle = None
		self.title = 'Skeinview Dynamic Preferences'
		oldArchive = self.archive
		self.archive = self.updatePreferences
		self.lowerName = 'skeinview dynamic'
		preferences.getDisplayedDialogFromConstructor( self )
		self.archive = oldArchive

	def execute( self ):
		"Write button has been clicked."
		fileNames = polyfile.getFileOrGcodeDirectory( self.fileNameInput.value, self.fileNameInput.wasCancelled )
		for fileName in fileNames:
			displayFile( fileName )

	def setUpdateFunction( self, updateFunction ):
		"Set the update function of the update preferences."
		self.updateFunction = updateFunction
		for updatePreference in self.updatePreferences:
			updatePreference.setUpdateFunction( self.setToDisplaySaveUpdate )

	def setToDisplaySaveUpdate( self, event = None ):
		"Set the preference values to the display, save the new values, then call the update function."
		for updatePreference in self.updatePreferences:
			updatePreference.setToDisplay()
		preferences.writePreferences( self )
		if self.updateFunction != None:
			self.updateFunction()


class SkeinviewSkein:
	"A class to write a get a scalable vector graphics text for a gcode skein."
	def __init__( self ):
		self.extrusionNumber = 0
		self.isThereALayerStartWord = False
		self.oldZ = - 999999999999.0
		self.skeinPane = None
		self.skeinPanes = []

	def addToPath( self, line, location ):
		"Add a point to travel and maybe extrusion."
		if self.oldLocation == None:
			return
		beginningComplex = complex( self.oldLocation.x, self.cornerImaginaryTotal - self.oldLocation.y )
		endComplex = complex( location.x, self.cornerImaginaryTotal - location.y )
		colorName = 'gray'
		width = 1
		if self.extruderActive:
			colorName = self.colorNames[ self.extrusionNumber % len( self.colorNames ) ]
			width = 2
		coloredLine = ColoredLine( colorName, self.scale * beginningComplex - self.marginCornerLow, self.scale * endComplex - self.marginCornerLow, line, self.lineIndex, width )
		self.skeinPane.append( coloredLine )

	def initializeActiveLocation( self ):
		"Set variables to default."
		self.extruderActive = False
		self.oldLocation = None

	def isLayerStart( self, firstWord, splitLine ):
		"Parse a gcode line and add it to the vector output."
		if self.isThereALayerStartWord:
			return firstWord == '(<layer>'
		if firstWord != 'G1' and firstWord != 'G2' and firstWord != 'G3':
			return False
		location = gcodec.getLocationFromSplitLine( self.oldLocation, splitLine )
		if location.z - self.oldZ > 0.1:
			self.oldZ = location.z
			return True
		return False

	def linearCorner( self, splitLine ):
		"Update the bounding corners."
		location = gcodec.getLocationFromSplitLine( self.oldLocation, splitLine )
		if self.extruderActive or self.goAroundExtruderOffTravel:
			self.cornerHigh = euclidean.getPointMaximum( self.cornerHigh, location )
			self.cornerLow = euclidean.getPointMinimum( self.cornerLow, location )
		self.oldLocation = location

	def linearMove( self, line, splitLine ):
		"Get statistics for a linear move."
		if self.skeinPane == None:
			return
		location = gcodec.getLocationFromSplitLine( self.oldLocation, splitLine )
		self.addToPath( line, location )
		self.oldLocation = location

	def parseCorner( self, line ):
		"Parse a gcode line and use the location to update the bounding corners."
		splitLine = line.split()
		if len( splitLine ) < 1:
			return
		firstWord = splitLine[ 0 ]
		if firstWord == 'G1':
			self.linearCorner( splitLine )
		elif firstWord == 'M101':
			self.extruderActive = True
		elif firstWord == 'M103':
			self.extruderActive = False

	def parseGcode( self, gcodeText, skeinviewPreferences ):
		"Parse gcode text and store the vector output."
		self.gcodeText = gcodeText
		self.initializeActiveLocation()
		self.cornerHigh = Vector3( - 999999999.0, - 999999999.0, - 999999999.0 )
		self.cornerLow = Vector3( 999999999.0, 999999999.0, 999999999.0 )
		self.goAroundExtruderOffTravel = skeinviewPreferences.goAroundExtruderOffTravel.value
		self.lines = gcodec.getTextLines( gcodeText )
		self.isThereALayerStartWord = gcodec.isThereAFirstWord( '(<layer>', self.lines, 1 )
		for line in self.lines:
			self.parseCorner( line )
		self.scale = skeinviewPreferences.pixelsPerMillimeter.value
		self.scaleCornerHigh = self.scale * self.cornerHigh.dropAxis( 2 )
		self.scaleCornerLow = self.scale * self.cornerLow.dropAxis( 2 )
		print( "The lower left corner of the skeinview window is at %s, %s" % ( self.cornerLow.x, self.cornerLow.y ) )
		print( "The upper right corner of the skeinview window is at %s, %s" % ( self.cornerHigh.x, self.cornerHigh.y ) )
		self.cornerImaginaryTotal = self.cornerHigh.y + self.cornerLow.y
		margin = complex( 5.0, 5.0 )
		self.marginCornerLow = self.scaleCornerLow - margin
		self.scaleSize = margin + self.scaleCornerHigh - self.marginCornerLow
		self.initializeActiveLocation()
		self.colorNames = [ 'brown', 'red', 'orange', 'yellow', 'green', 'blue', 'purple' ]
		for self.lineIndex in xrange( len( self.lines ) ):
			line = self.lines[ self.lineIndex ]
			self.parseLine( line )

	def parseLine( self, line ):
		"Parse a gcode line and add it to the vector output."
		splitLine = line.split()
		if len( splitLine ) < 1:
			return
		firstWord = splitLine[ 0 ]
		if self.isLayerStart( firstWord, splitLine ):
			self.extrusionNumber = 0
			self.skeinPane = []
			self.skeinPanes.append( self.skeinPane )
		if firstWord == 'G1':
			self.linearMove( line, splitLine )
		elif firstWord == 'M101':
			self.extruderActive = True
			self.extrusionNumber += 1
		elif firstWord == 'M103':
			self.extruderActive = False


class SkeinWindow:
	def __init__( self, skein, skeinviewPreferences ):
		screenHorizontalInset = skeinviewPreferences.screenHorizontalInset.value
		screenVerticalInset = skeinviewPreferences.screenVerticalInset.value
		title = 'Skeinview Viewer from Hydraraptor'
		self.index = 0
		self.movementTextID = None
		self.skein = skein
		self.skeinPanes = skein.skeinPanes
		self.root = preferences.Tkinter.Tk()
		self.root.title( title )
		self.skeinviewPreferences = skeinviewPreferences
		for phoenixPreferenceTableKey in skeinviewPreferences.phoenixPreferenceTable.keys():
			skeinviewPreferences.phoenixPreferenceTable[ phoenixPreferenceTableKey ] = phoenixPreferenceTableKey.value
		skeinviewPreferences.slideShowRate.value = max( skeinviewPreferences.slideShowRate.value, 0.01 )
		skeinviewPreferences.slideShowRate.value = min( skeinviewPreferences.slideShowRate.value, 85.0 )
		self.timerID = None
		fileHelpMenuBar = preferences.FileHelpMenuBar( self.root )
		fileHelpMenuBar.helpMenu.add_command( label = 'Skeinview', command = preferences.HelpPage().getOpenFromDocumentationSubName( 'skeinforge_tools.analyze_plugins.skeinview.html' ) )
		fileHelpMenuBar.completeMenu( self.root.destroy, skeinviewPreferences.lowerName )
		frame = preferences.Tkinter.Frame( self.root )
		xScrollbar = preferences.Tkinter.Scrollbar( self.root, orient = preferences.Tkinter.HORIZONTAL )
		yScrollbar = preferences.Tkinter.Scrollbar( self.root )
		canvasHeight = min( int( skein.scaleSize.imag ), self.root.winfo_screenheight() - screenHorizontalInset )
		canvasWidth = min( int( skein.scaleSize.real ), self.root.winfo_screenwidth() - screenVerticalInset )
		self.canvas = preferences.Tkinter.Canvas( self.root, width = canvasWidth, height = canvasHeight, scrollregion = ( 0, 0, int( skein.scaleSize.real ), int( skein.scaleSize.imag ) ) )
		self.canvas.grid( row = 0, rowspan = 98, column = 0, columnspan = 99, sticky = preferences.Tkinter.W )
		xScrollbar.grid( row = 98, column = 0, columnspan = 99, sticky = preferences.Tkinter.E + preferences.Tkinter.W )
		xScrollbar.config( command = self.canvas.xview )
		yScrollbar.grid( row = 0, rowspan = 98, column = 99, sticky = preferences.Tkinter.N + preferences.Tkinter.S )
		yScrollbar.config( command = self.canvas.yview )
		self.canvas[ 'xscrollcommand' ] = xScrollbar.set
		self.canvas[ 'yscrollcommand' ] = yScrollbar.set
		self.diveButton = preferences.Tkinter.Button( self.root, activebackground = 'black', activeforeground = 'purple', command = self.dive, text = 'Dive \\/\\/' )
		self.diveButton.grid( row = 99, column = 1, sticky = preferences.Tkinter.W )
		self.downButton = preferences.Tkinter.Button( self.root, activebackground = 'black', activeforeground = 'purple', command = self.down, text = 'Down \\/' )
		self.downButton.grid( row = 99, column = 2, sticky = preferences.Tkinter.W )
		preferences.CloseListener( title.lower(), self ).listenToWidget( self.downButton )
		self.upButton = preferences.Tkinter.Button( self.root, activebackground = 'black', activeforeground = 'purple', command = self.up, text = 'Up /\\' )
		self.upButton.grid( row = 99, column = 4, sticky = preferences.Tkinter.W )
		self.soarButton = preferences.Tkinter.Button( self.root, activebackground = 'black', activeforeground = 'purple', command = self.soar, text = 'Soar /\\/\\' )
		self.soarButton.grid( row = 99, column = 5, sticky = preferences.Tkinter.W )
		self.indexEntry = preferences.Tkinter.Entry( self.root )
		self.indexEntry.bind( '<Return>', self.indexEntryReturnPressed )
		self.indexEntry.grid( row = 99, column = 6, columnspan = 10, sticky = preferences.Tkinter.W )
		self.exitButton = preferences.Tkinter.Button( self.root, text = 'Exit', activebackground = 'black', activeforeground = 'red', command = self.destroyAllDialogWindows, fg = 'red' )
		self.exitButton.grid( row = 99, column = 95, columnspan = 5, sticky = preferences.Tkinter.W )
		self.showPreferencesButton = preferences.Tkinter.Button( self.root, activebackground = 'black', activeforeground = 'purple', command = self.showPreferences, text = 'Show Preferences' )
		self.showPreferencesButton.grid( row = 99, column = 0, sticky = preferences.Tkinter.W )
		self.canvas.bind( '<Button-1>', self.buttonOneClicked )
		if skeinviewPreferences.displayLineTextWhenMouseMoves.value:
			self.canvas.bind( '<Leave>', self.leave )
			self.canvas.bind( '<Motion>', self.motion )
		self.update()
		self.showPreferences()

	def buttonOneClicked( self, event ):
		"Print the line clicked."
		x = self.canvas.canvasx( event.x )
		y = self.canvas.canvasy( event.y )
		print( 'The line clicked is: ' + self.getTagsGivenXY( x, y ) )

	def cancelTimer( self ):
		"Cancel the timer and set it to none."
		if self.timerID != None:
			self.canvas.after_cancel ( self.timerID )
			self.timerID = None

	def destroyAllDialogWindows( self ):
		"Destroy all the dialog windows."
		if self.showPreferencesButton[ 'state' ] == preferences.Tkinter.DISABLED:
			self.skeinviewPreferences.preferencesDialog.root.destroy()
		self.root.destroy()

	def destroyMovementText( self ):
		'Destroy the movement text.'
		self.canvas.delete( self.movementTextID )
		self.movementTextID = None

	def dive( self ):
		"Dive, go down periodically."
		self.cancelTimer()
		self.index -= 1
		self.update()
		if self.index < 1:
			return
		self.timerID = self.canvas.after( self.getSlideShowDelay(), self.dive )

	def down( self ):
		self.cancelTimer()
		self.index -= 1
		self.update()

	def getSlideShowDelay( self ):
		"Get the slide show delay in milliseconds."
		slideShowDelay = int( round( 1000.0 / self.skeinviewPreferences.slideShowRate.value ) )
		return max( slideShowDelay, 1 )

	def getTagsGivenXY( self, x, y ):
		"Get the tag for the x and y."
		if self.movementTextID != None:
			self.destroyMovementText()
		tags = self.canvas.itemcget( self.canvas.find_closest( x, y ), 'tags' )
		currentEnd = ' current'
		if tags.find( currentEnd ) != - 1:
			return tags[ : - len( currentEnd ) ]
		return tags

	def indexEntryReturnPressed( self, event ):
		self.cancelTimer()
		self.index = int( self.indexEntry.get() )
		self.index = max( 0, self.index )
		self.index = min( len( self.skeinPanes ) - 1, self.index )
		self.update()

	def leave( self, event ):
		"The mouse left the canvas."
		self.destroyMovementText()

	def motion( self, event ):
		"The mouse moved."
		x = self.canvas.canvasx( event.x )
		y = self.canvas.canvasy( event.y )
		tags = self.getTagsGivenXY( x, y )
		if tags != '':
			self.movementTextID = self.canvas.create_text ( x, y, anchor = preferences.Tkinter.SW, text = 'The line is: ' + tags )

	def preferencesDestroyed( self, event ):
		"Enable the show preferences button because the dynamic preferences were destroyed."
		try:
			self.showPreferencesButton.config( state = preferences.Tkinter.NORMAL )
		except:
			pass

	def showPreferences( self ):
		"Show the dynamic preferences."
		self.skeinviewPreferences.displayImmediateUpdateDialog()
		self.skeinviewPreferences.setUpdateFunction( self.update  )
		self.skeinviewPreferences.drawArrows.checkbutton.bind( '<Destroy>', self.preferencesDestroyed )
		self.showPreferencesButton.config( state = preferences.Tkinter.DISABLED )

	def soar( self ):
		"Soar, go up periodically."
		self.cancelTimer()
		self.index += 1
		self.update()
		if self.index > len( self.skeinPanes ) - 2:
			return
		self.timerID = self.canvas.after( self.getSlideShowDelay(), self.soar )

	def up( self ):
		"Go up a layer."
		self.cancelTimer()
		self.index += 1
		self.update()

	def update( self ):
		if len( self.skeinPanes ) < 1:
			return
		for phoenixPreferenceTableKey in self.skeinviewPreferences.phoenixPreferenceTable.keys():
			if self.skeinviewPreferences.phoenixPreferenceTable[ phoenixPreferenceTableKey ] != phoenixPreferenceTableKey.value:
				self.destroyAllDialogWindows()
				displayFileGivenTextPreferences( self.skein.gcodeText, self.skeinviewPreferences )
				return
		self.arrowType = None
		if self.skeinviewPreferences.drawArrows.value:
			self.arrowType = 'last'
		skeinPane = self.skeinPanes[ self.index ]
		self.canvas.delete( preferences.Tkinter.ALL )
		for coloredLine in skeinPane:
			complexBegin = coloredLine.complexBegin
			complexEnd = coloredLine.complexEnd
			self.canvas.create_line(
				complexBegin.real,
				complexBegin.imag,
				complexEnd.real,
				complexEnd.imag,
				fill = coloredLine.colorName,
				arrow = self.arrowType,
				tags = '%s %s' % ( coloredLine.lineIndex, coloredLine.line ),
				width = coloredLine.width )
		if self.index < len( self.skeinPanes ) - 1:
			self.soarButton.config( state = preferences.Tkinter.NORMAL )
			self.upButton.config( state = preferences.Tkinter.NORMAL )
		else:
			self.soarButton.config( state = preferences.Tkinter.DISABLED )
			self.upButton.config( state = preferences.Tkinter.DISABLED )
		if self.index > 0:
			self.downButton.config( state = preferences.Tkinter.NORMAL )
			self.diveButton.config( state = preferences.Tkinter.NORMAL )
		else:
			self.downButton.config( state = preferences.Tkinter.DISABLED )
			self.diveButton.config( state = preferences.Tkinter.DISABLED )
		self.indexEntry.delete( 0, preferences.Tkinter.END )
		self.indexEntry.insert( 0, str( self.index ) )


def main():
	"Display the skeinview dialog."
	if len( sys.argv ) > 1:
		displayFile( ' '.join( sys.argv[ 1 : ] ) )
	else:
		preferences.startMainLoopFromConstructor( getPreferencesConstructor() )

if __name__ == "__main__":
	main()

"""
Behold is a script to display each layer of a gcode file.

The default 'Activate Behold' checkbox is on.  When it is on, the functions described below will work when called from the
skeinforge toolchain, when it is off, the functions will not be called from the toolchain.  The functions will still be called, whether
or not the 'Activate Behold' checkbox is on, when behold is run directly.  Behold has trouble separating the layers
when it reads gcode without comments.

If "Draw Arrows" is selected, arrows will be drawn at the end of each line segment, the default is on.  If "Go Around Extruder
Off Travel" is selected, the display will include the travel when the extruder is off, which means it will include the nozzle wipe
path if any.  The "Pixels over Extrusion Width" preference is the scale of the image, the higher the number, the greater the
size of the display.  The "Screen Horizontal Inset" determines how much the display will be inset in the horizontal direction
from the edge of screen, the higher the number the more it will be inset and the smaller it will be, the default is one hundred.
The "Screen Vertical Inset" determines how much the display will be inset in the vertical direction from the edge of screen,
the default is fifty.

On the behold display window, the up button increases the layer index shown by one, and the down button decreases the
layer index by one.  When the index displayed in the index field is changed then "<return>" is hit, the layer index shown will
be set to the index field, to a mimimum of zero and to a maximum of the highest index layer.

To run behold, in a shell in the folder which behold is in type:
> python behold.py

An explanation of the gcodes is at:
http://reprap.org/bin/view/Main/Arduino_GCode_Interpreter

and at:
http://reprap.org/bin/view/Main/MCodeReference

A gode example is at:
http://forums.reprap.org/file.php?12,file=565

This example displays a skein view for the gcode file Screw Holder.gcode.  This example is run in a terminal in the folder which
contains Screw Holder.gcode and behold.py.


> python behold.py
This brings up the behold dialog.


> python behold.py Screw Holder.gcode
This brings up a skein window to view each layer of a gcode file.


> python
Python 2.5.1 (r251:54863, Sep 22 2007, 01:43:31)
[GCC 4.2.1 (SUSE Linux)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import behold
>>> behold.main()
This brings up the behold dialog.


>>> behold.beholdFile()
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
import cStringIO
import math
import sys


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


def displayBeholdFileGivenText( gcodeText, beholdPreferences = None ):
	"Display a beholded gcode file for a gcode file."
	if gcodeText == '':
		return ''
	if beholdPreferences == None:
		beholdPreferences = BeholdPreferences()
		preferences.readPreferences( beholdPreferences )
	skein = BeholdSkein()
	skein.parseGcode( gcodeText, beholdPreferences )
	SkeinWindow( skein.arrowType, beholdPreferences, skein.screenSize, skein.skeinPanes )

def beholdFile( fileName = '' ):
	"Behold a gcode file.  If no fileName is specified, behold the first gcode file in this folder that is not modified."
	if fileName == '':
		unmodified = gcodec.getUnmodifiedGCodeFiles()
		if len( unmodified ) == 0:
			print( "There are no unmodified gcode files in this folder." )
			return
		fileName = unmodified[ 0 ]
	gcodeText = gcodec.getFileText( fileName )
	displayBeholdFileGivenText( gcodeText )

def writeOutput( fileName, gcodeText = '' ):
	"Write a beholded gcode file for a skeinforge gcode file, if 'Activate Behold' is selected."
	beholdPreferences = BeholdPreferences()
	preferences.readPreferences( beholdPreferences )
	if beholdPreferences.activateBehold.value:
		if gcodeText == '':
			gcodeText = gcodec.getFileText( fileName )
		displayBeholdFileGivenText( gcodeText, beholdPreferences )


class ColoredLine:
	"A colored line."
	def __init__( self, colorName, complexBegin, complexEnd, line, lineIndex, width, begin, end ):
		"Set the color name and corners."
		self.begin = begin
		self.colorName = colorName
		self.complexBegin = complexBegin
		self.complexEnd = complexEnd
		self.end = end
		self.line = line
		self.lineIndex = lineIndex
		self.width = width
	
	def __repr__( self ):
		"Get the string representation of this colored line."
		return '%s, %s, %s, %s' % ( self.colorName, self.complexBegin, self.complexEnd, self.line, self.lineIndex, self.width )


class BeholdPreferences:
	"A class to handle the behold preferences."
	def __init__( self ):
		"Set the default preferences, execute title & preferences fileName."
		#Set the default preferences.
		self.archive = []
		self.activateBehold = preferences.BooleanPreference().getFromValue( 'Activate Behold', True )
		self.archive.append( self.activateBehold )
		self.drawArrows = preferences.BooleanPreference().getFromValue( 'Draw Arrows', True )
		self.archive.append( self.drawArrows )
		self.fileNameInput = preferences.Filename().getFromFilename( [ ( 'Gcode text files', '*.gcode' ) ], 'Open File to Behold', '' )
		self.archive.append( self.fileNameInput )
		self.goAroundExtruderOffTravel = preferences.BooleanPreference().getFromValue( 'Go Around Extruder Off Travel', False )
		self.archive.append( self.goAroundExtruderOffTravel )
		self.pixelsWidthExtrusion = preferences.FloatPreference().getFromValue( 'Pixels over Extrusion Width (ratio):', 10.0 )
		self.archive.append( self.pixelsWidthExtrusion )
		self.screenHorizontalInset = preferences.IntPreference().getFromValue( 'Screen Horizontal Inset (pixels):', 100 )
		self.archive.append( self.screenHorizontalInset )
		self.screenVerticalInset = preferences.IntPreference().getFromValue( 'Screen Vertical Inset (pixels):', 50 )
		self.archive.append( self.screenVerticalInset )
		self.viewpointLatitude = preferences.FloatPreference().getFromValue( 'Viewpoint Latitude (degrees):', 45.0 )
		self.archive.append( self.viewpointLatitude )
		self.viewpointLongtitude = preferences.FloatPreference().getFromValue( 'Viewpoint Longtitude (degrees):', 20.0 )
		self.archive.append( self.viewpointLongtitude )
		self.viewXAxisLongtitude = preferences.FloatPreference().getFromValue( 'View X Axis Longtitude (degrees):', 60.0 )
		self.archive.append( self.viewXAxisLongtitude )
		#Create the archive, title of the execute button, title of the dialog & preferences fileName.
		self.executeTitle = 'Behold'
		self.fileNamePreferences = preferences.getPreferencesFilePath( 'behold.csv' )
		self.fileNameHelp = 'skeinforge_tools.analyze_plugins.behold.html'
		self.saveTitle = 'Save Preferences'
		self.title = 'Behold Preferences'

	def execute( self ):
		"Write button has been clicked."
		fileNames = polyfile.getFileOrGcodeDirectory( self.fileNameInput.value, self.fileNameInput.wasCancelled )
		for fileName in fileNames:
			beholdFile( fileName )


class BeholdSkein:
	"A class to write a get a scalable vector graphics text for a gcode skein."
	def __init__( self ):
		self.extrusionNumber = 0
		self.extrusionWidth = 0.6
		self.isThereALayerStartWord = False
		self.oldZ = - 999999999999.0
		self.skeinPanes = []

	def addToPath( self, line, location ):
		"Add a point to travel and maybe extrusion."
		if self.oldLocation == None:
			return
		beginningComplex = complex( self.oldLocation.x, self.cornerImaginaryTotal - self.oldLocation.y )
		endComplex = complex( location.x, self.cornerImaginaryTotal - location.y )
		begin = self.scale * self.oldLocation - self.scaleCenterBottom
		end = self.scale * location - self.scaleCenterBottom
		colorName = 'gray'
		width = 1
		if self.extruderActive:
			colorName = self.colorNames[ self.extrusionNumber % len( self.colorNames ) ]
			width = 2
		coloredLine = ColoredLine( colorName, self.scale * beginningComplex - self.marginCornerLow, self.scale * endComplex - self.marginCornerLow, line, self.lineIndex, width, begin, end )
		self.skeinPane.append( coloredLine )

	def initializeActiveLocation( self ):
		"Set variables to default."
		self.extruderActive = False
		self.oldLocation = None

	def isLayerStart( self, firstWord, splitLine ):
		"Parse a gcode line and add it to the vector output."
		if self.isThereALayerStartWord:
			return firstWord == '(<layerStart>'
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
		elif firstWord == '(<extrusionWidth>':
			self.extrusionWidth = float( splitLine[ 1 ] )

	def parseGcode( self, gcodeText, beholdPreferences ):
		"Parse gcode text and store the vector output."
		self.arrowType = None
		if beholdPreferences.drawArrows.value:
			self.arrowType = 'last'
		self.initializeActiveLocation()
		self.cornerHigh = Vector3( - 999999999.0, - 999999999.0, - 999999999.0 )
		self.cornerLow = Vector3( 999999999.0, 999999999.0, 999999999.0 )
		self.goAroundExtruderOffTravel = beholdPreferences.goAroundExtruderOffTravel.value
		self.lines = gcodec.getTextLines( gcodeText )
		self.isThereALayerStartWord = gcodec.isThereAFirstWord( '(<layerStart>', self.lines, 1 )
		for line in self.lines:
			self.parseCorner( line )
		self.centerComplex = 0.5 * ( self.cornerHigh.dropAxis( 2 ) + self.cornerLow.dropAxis( 2 ) )
		self.centerBottom = Vector3( self.centerComplex.real, self.centerComplex.imag, self.cornerLow.z )
		self.scale = beholdPreferences.pixelsWidthExtrusion.value / self.extrusionWidth
		self.scaleCenterBottom = self.scale * self.centerBottom
		self.scaleCornerHigh = self.scale * self.cornerHigh.dropAxis( 2 )
		self.scaleCornerLow = self.scale * self.cornerLow.dropAxis( 2 )
		print( "The lower left corner of the behold window is at %s, %s" % ( self.cornerLow.x, self.cornerLow.y ) )
		print( "The upper right corner of the behold window is at %s, %s" % ( self.cornerHigh.x, self.cornerHigh.y ) )
		self.cornerImaginaryTotal = self.cornerHigh.y + self.cornerLow.y
		margin = complex( 5.0, 5.0 )
		self.marginCornerLow = self.scaleCornerLow - margin
		self.screenSize = margin + 2.0 * ( self.scaleCornerHigh - self.marginCornerLow )
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
	def __init__( self, arrowType, beholdPreferences, size, skeinPanes ):
		self.arrowType = arrowType
		self.beholdPreferences = beholdPreferences
		self.center = 0.5 * size
		self.index = 0
		self.skeinPanes = skeinPanes
		self.root = preferences.Tkinter.Tk()
		self.root.title( "Behold from HydraRaptor" )
		frame = preferences.Tkinter.Frame( self.root )
		xScrollbar = preferences.Tkinter.Scrollbar( self.root, orient = preferences.Tkinter.HORIZONTAL )
		yScrollbar = preferences.Tkinter.Scrollbar( self.root )
		canvasHeight = min( int( size.imag ), self.root.winfo_screenheight() - beholdPreferences.screenHorizontalInset.value )
		canvasWidth = min( int( size.real ), self.root.winfo_screenwidth() - beholdPreferences.screenVerticalInset.value )
		self.canvas = preferences.Tkinter.Canvas( self.root, width = canvasWidth, height = canvasHeight, scrollregion = ( 0, 0, int( size.real ), int( size.imag ) ) )
		self.canvas.grid( row = 0, rowspan = 98, column = 0, columnspan = 99, sticky = preferences.Tkinter.W )
		xScrollbar.grid( row = 98, column = 0, columnspan = 99, sticky = preferences.Tkinter.E + preferences.Tkinter.W )
		xScrollbar.config( command = self.canvas.xview )
		yScrollbar.grid( row = 0, rowspan = 98, column = 99, sticky = preferences.Tkinter.N + preferences.Tkinter.S )
		yScrollbar.config( command = self.canvas.yview )
		self.canvas[ 'xscrollcommand' ] = xScrollbar.set
		self.canvas[ 'yscrollcommand' ] = yScrollbar.set
		self.exitButton = preferences.Tkinter.Button( self.root, text = 'Exit', activebackground = 'black', activeforeground = 'red', command = self.root.quit, fg = 'red' )
		self.exitButton.grid( row = 99, column = 95, columnspan = 5, sticky = preferences.Tkinter.W )
		self.indexEntry = preferences.Tkinter.Entry( self.root )
		self.indexEntry.bind( '<Return>', self.indexEntryReturnPressed )
		self.indexEntry.grid( row = 99, column = 2, columnspan = 10, sticky = preferences.Tkinter.W )
		self.canvas.bind('<Button-1>', self.buttonOneClicked )
		self.update()
		if preferences.globalIsMainLoopRunning:
			return
		preferences.globalIsMainLoopRunning = True
		self.root.mainloop()
		preferences.globalIsMainLoopRunning = False

	def buttonOneClicked( self, event ):
		x = self.canvas.canvasx( event.x )
		y = self.canvas.canvasx( event.y )
		tags = self.canvas.itemcget( self.canvas.find_closest( x, y ), 'tags' )
		currentEnd = ' current'
		if tags.find( currentEnd ) != - 1:
			tags = tags[ : - len( currentEnd ) ]
		if len( tags ) > 0:
			print( tags )

	def drawColoredLines( self, coloredLines ):
		"Draw colored lines."
		for coloredLine in coloredLines:
			complexBegin = self.getScreenComplex( coloredLine.begin )
			complexEnd = self.getScreenComplex( coloredLine.end )
			self.canvas.create_line(
				complexBegin.real,
				complexBegin.imag,
				complexEnd.real,
				complexEnd.imag,
				fill = coloredLine.colorName,
				arrow = self.arrowType,
				tags = 'The line clicked is: %s %s' % ( coloredLine.lineIndex, coloredLine.line ),
				width = coloredLine.width )

	def getScreenComplex( self, point ):
		"Get the point in screen perspective."
		screenComplexX = point.dot( self.viewVectorX )
		screenComplexY = point.dot( self.viewVectorY )
		screenComplex = complex( screenComplexX, - screenComplexY )
		screenComplex += self.center
		return screenComplex

	def indexEntryReturnPressed( self, event ):
		self.index = int( self.indexEntry.get() )
		self.index = max( 0, self.index )
		self.index = min( len( self.skeinPanes ) - 1, self.index )
		self.update()

	def update( self ):
		if len( self.skeinPanes ) < 1:
			return
		self.canvas.delete( preferences.Tkinter.ALL )
		viewpointComplexLongtitude = euclidean.getPolar( math.radians( self.beholdPreferences.viewpointLongtitude.value ) )
		viewpointVectorLongtitude = Vector3( viewpointComplexLongtitude.real, viewpointComplexLongtitude.imag, 0.0 )
		self.beholdPreferences.viewpointLatitude.value = max( 0.1, self.beholdPreferences.viewpointLatitude.value )
		self.beholdPreferences.viewpointLatitude.value = min( 179.9, self.beholdPreferences.viewpointLatitude.value )
		viewpointLatitudeRatio = euclidean.getPolar( math.radians( self.beholdPreferences.viewpointLatitude.value ) )
		viewpointVectorLatitude = Vector3( viewpointLatitudeRatio.imag * viewpointComplexLongtitude.real, viewpointLatitudeRatio.imag * viewpointComplexLongtitude.imag, viewpointLatitudeRatio.real )
		self.viewVectorY = viewpointVectorLatitude.cross( viewpointVectorLongtitude )
		self.viewVectorY.normalize()
		self.viewVectorX = viewpointVectorLatitude.cross( self.viewVectorY )
		self.viewVectorX.normalize()
		for skeinPane in self.skeinPanes:
			self.drawColoredLines( skeinPane )
#		self.indexEntry.delete( 0, preferences.Tkinter.END )
#		self.indexEntry.insert( 0, str( self.index ) )


def main():
	"Display the behold dialog."
	if len( sys.argv ) > 1:
		beholdFile( ' '.join( sys.argv[ 1 : ] ) )
	else:
		preferences.displayDialog( BeholdPreferences() )

if __name__ == "__main__":
	main()

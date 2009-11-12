"""
Tableau has a couple of base classes for analyze viewers.

"""

from __future__ import absolute_import
#Init has to be imported first because it has code to workaround the python bug where relative imports don't work if the module is imported as a main module.
import __init__

from skeinforge_tools.analyze_plugins.analyze_utilities import zoom_in
from skeinforge_tools.analyze_plugins.analyze_utilities import zoom_out
from skeinforge_tools.skeinforge_utilities import gcodec
from skeinforge_tools.skeinforge_utilities import preferences
import os

__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


class TableauRepository:
	"The viewer base repository class."
	def activateMouseModeToolUpdate( self ):
		"Call the activateMouseModeTool function."
		self.setToDisplaySave()
		if self.activateMouseModeTool != None:
			self.activateMouseModeTool()

	def setNewMouseToolUpdate( self, getNewMouseToolFunction, mouseTool ):
		"Set the getNewMouseTool function and the update function."
		mouseTool.constructorFunction = getNewMouseToolFunction
		mouseTool.setUpdateFunction( self.activateMouseModeToolUpdate )

	def setToDisplaySave( self, event = None ):
		"Set the preference values to the display, save the new values."
		for menuEntity in self.menuEntities:
			if menuEntity in self.archive:
				menuEntity.setToDisplay()
		preferences.writePreferences( self )

	def setToDisplaySavePhoenixUpdate( self, event = None ):
		"Set the preference values to the display, save the new values, then call the update function."
		self.setToDisplaySave()
		if self.phoenixUpdateFunction != None:
			self.phoenixUpdateFunction()

	def setToDisplaySaveUpdate( self, event = None ):
		"Set the preference values to the display, save the new values, then call the update function."
		self.setToDisplaySave()
		if self.updateFunction != None:
			self.updateFunction()

	def initializeUpdateFunctionsToNone( self ):
		"Initialize all the update functions to none."
		self.activateMouseModeTool = None
		self.phoenixUpdateFunction = None
		self.updateFunction = None


class TableauWindow:
	def activateMouseModeTool( self ):
		"Activate the mouse mode tool."
		self.destroyMouseToolRaiseMouseButtons()
		for menuRadio in self.repository.mouseMode.menuRadios:
			if menuRadio.value:
				self.mouseTool = menuRadio.mouseTool
				menuRadio.mouseButton[ 'relief' ] = preferences.Tkinter.SUNKEN

	def addMouseInstantTool( self, fileName, mouseInstantTool ):
		"Add the mouse instant tool and derived photo button."
		mouseInstantTool.getReset( self )
		photoButton = self.getPhotoButtonGridIncrement( mouseInstantTool.click, fileName )
		mouseInstantTool.mouseButton = photoButton
		self.mouseInstantButtons.append( photoButton )

	def button1( self, event ):
		"The button was clicked."
		self.mouseTool.button1( event )

	def buttonRelease1( self, event ):
		"The button was released."
		self.mouseTool.buttonRelease1( event )

	def cancelTimer( self, event = None ):
		"Cancel the timer and set it to none."
		if self.timerID != None:
			self.canvas.after_cancel ( self.timerID )
			self.timerID = None

	def cancelTimerResetButtons( self ):
		"Cancel the timer and set it to none."
		self.cancelTimer()
		self.resetPeriodicButtonsText()

	def centerUpdateSetWindowGeometryShowPreferences( self, center ):
		"Center the scroll region, update, set the window geometry, and show the preferences."
		self.preferencesMenu = preferences.Tkinter.Menu( self.fileHelpMenuBar.menuBar, tearoff = 0 )
		self.fileHelpMenuBar.addMenuToMenuBar( "Preferences", self.preferencesMenu )
		preferences.addMenuEntitiesToMenu( self.preferencesMenu, self.repository.menuEntities )
		self.relayXview( preferences.Tkinter.MOVETO, center.real - self.canvasScreenCenterComplex.real )
		self.relayYview( preferences.Tkinter.MOVETO, center.imag - self.canvasScreenCenterComplex.imag )
		self.root.withdraw()
		self.root.update_idletasks()
		movedGeometryString = '%sx%s+%s' % ( self.root.winfo_reqwidth(), self.root.winfo_reqheight(), '0+0' )
		self.root.geometry( movedGeometryString )
		self.repository.activateMouseModeTool = self.activateMouseModeTool
		self.repository.phoenixUpdateFunction = self.phoenixUpdate
		self.repository.updateFunction = self.update

	def close( self, event = None ):
		"The dialog was closed."
		try:
			self.root.destroy()
		except:
			pass

	def destroyAllDialogWindows( self ):
		"Destroy all the dialog windows."
		for menuEntity in self.repository.menuEntities:
			lowerName = menuEntity.name.lower()
			if lowerName in preferences.globalRepositoryDialogListTable:
				globalRepositoryDialogValues = preferences.globalRepositoryDialogListTable[ lowerName ]
				for globalRepositoryDialogValue in globalRepositoryDialogValues:
					preferences.quitWindow( globalRepositoryDialogValue.root )

	def destroyMouseToolRaiseMouseButtons( self ):
		"Destroy the mouse tool and raise the mouse buttons."
		self.mouseTool.destroyEverything()
		for menuRadio in self.repository.mouseMode.menuRadios:
			menuRadio.mouseButton[ 'relief' ] = preferences.Tkinter.RAISED
		for mouseInstantButton in self.mouseInstantButtons:
			mouseInstantButton[ 'relief' ] = preferences.Tkinter.RAISED

	def dive( self ):
		"Dive, go up periodically."
		oldDiveButtonText = self.diveButton[ 'text' ]
		self.cancelTimerResetButtons()
		if oldDiveButtonText == 'stop':
			return
		self.diveCycle()

	def diveCycle( self ):
		"Start the dive cycle."
		self.cancelTimer()
		self.repository.layerIndex.value -= 1
		self.saveUpdate()
		if self.repository.layerIndex.value < 1:
			self.resetPeriodicButtonsText()
			return
		self.setButtonImageText( self.diveButton, 'stop' )
		self.timerID = self.canvas.after( self.getSlideShowDelay(), self.diveCycle )

	def down( self ):
		"Go down a layer."
		self.cancelTimerResetButtons()
		self.repository.layerIndex.value -= 1
		self.saveUpdate()

	def export( self ):
		"Export the canvas as a postscript file."
		postscriptFileName = gcodec.getFilePathWithUnderscoredBasename( self.skein.fileName, self.suffix )
		boundingBox = self.canvas.bbox( preferences.Tkinter.ALL ) # tuple (w, n, e, s)
		boxW = boundingBox[ 0 ]
		boxN = boundingBox[ 1 ]
		boxWidth = boundingBox[ 2 ] - boxW
		boxHeight = boundingBox[ 3 ] - boxN
		print( 'Exported postscript file saved as ' + postscriptFileName )
		self.canvas.postscript( file = postscriptFileName, height = boxHeight, width = boxWidth, pageheight = boxHeight, pagewidth = boxWidth, x = boxW, y = boxN )
		fileExtension = self.repository.exportFileExtension.value
		postscriptProgram = self.repository.exportPostscriptProgram.value
		if postscriptProgram == '':
			return
		postscriptFilePath = '"' + os.path.normpath( postscriptFileName ) + '"' # " to send in file name with spaces
		shellCommand = postscriptProgram + ' ' + postscriptFilePath
		print( '' )
		if fileExtension == '':
			print( 'Sending the shell command:' )
			print( shellCommand )
			commandResult = os.system( shellCommand )
			if commandResult != 0:
				print( 'It may be that the system could not find the %s program.' % postscriptProgram )
				print( 'If so, try installing the %s program or look for another one, like the Gnu Image Manipulation Program (Gimp) which can be found at:' % postscriptProgram )
				print( 'http://www.gimp.org/' )
			return
		convertedFileName = gcodec.getFilePathWithUnderscoredBasename( postscriptFilePath, '.' + fileExtension + '"' )
		shellCommand += ' ' + convertedFileName
		print( 'Sending the shell command:' )
		print( shellCommand )
		commandResult = os.system( shellCommand )
		if commandResult != 0:
			print( 'The %s program could not convert the postscript to the %s file format.' % ( postscriptProgram, fileExtension ) )
			print( 'Try installing the %s program or look for another one, like Image Magick which can be found at:' % postscriptProgram )
			print( 'http://www.imagemagick.org/script/index.php' )

	def getPhotoButtonGridIncrement( self, commandFunction, fileName ):
		"Get a PhotoImage button, grid the button and increment the grid position."
		photoImage = None
		try:
			photoImage = preferences.Tkinter.PhotoImage( file = os.path.join( self.imagesDirectoryPath, fileName ), master = self.root )
		except:
			print( 'Image %s was not found in the images directory, so a text button will be substituted.' % fileName )
		untilDotFileName = gcodec.getUntilDot( fileName )
		self.photoImages[ untilDotFileName ] = photoImage
		photoButton = preferences.Tkinter.Button( self.root, activebackground = 'black', activeforeground = 'white', command = commandFunction, text = untilDotFileName )
		if photoImage != None:
			photoButton[ 'image' ] = photoImage
		photoButton.grid( row = self.row, column = self.column, sticky = preferences.Tkinter.W )
		self.column += 1
		return photoButton

	def getScrollPaneCenter( self ):
		"Get the center of the scroll pane."
		return complex( self.canvas.canvasx( self.canvasCenterComplex.real ) / float( self.screenSize.real ), self.canvas.canvasy( self.canvasCenterComplex.imag ) / float( self.screenSize.imag ) )

	def getSlideShowDelay( self ):
		"Get the slide show delay in milliseconds."
		slideShowDelay = int( round( 1000.0 / self.repository.slideShowRate.value ) )
		return max( slideShowDelay, 1 )

	def indexEntryReturnPressed( self, event ):
		"The index entry return was pressed."
		self.cancelTimerResetButtons()
		self.repository.layerIndex.value = int( self.indexEntry.get() )
		self.limitIndex()
		self.saveUpdate()

	def limitIndex( self ):
		"Limit the index so it is not below zero or above the top."
		self.repository.layerIndex.value = max( 0, self.repository.layerIndex.value )
		self.repository.layerIndex.value = min( len( self.skeinPanes ) - 1, self.repository.layerIndex.value )

	def limitIndexSetArrowMouseDeleteCanvas( self ):
		"Limit the index, set the arrow type, set the mouse tool and delete all the canvas items."
		self.limitIndex()
		self.arrowType = None
		if self.repository.drawArrows.value:
			self.arrowType = 'last'
		self.canvas.delete( preferences.Tkinter.ALL )

	def motion( self, event ):
		"The mouse moved."
		self.mouseTool.motion( event )

	def phoenixUpdate( self ):
		"Update, and deiconify a new window and destroy the old."
		self.updateNewDestroyOld( self.getScrollPaneCenter() )

	def relayXview( self, *args ):
		"Relay xview changes."
		self.canvas.xview( *args )

	def relayYview( self, *args ):
		"Relay yview changes."
		self.canvas.yview( *args )

	def resetPeriodicButtonsText( self ):
		"Reset the text of the periodic buttons."
		self.setButtonImageText( self.diveButton, 'dive' )
		self.setButtonImageText( self.soarButton, 'soar' )

	def save( self ):
		"Set the preference values to the display, save the new values."
		self.repository.setToDisplaySave()

	def saveUpdate( self ):
		"Save and update."
		self.save()
		self.update()

	def scaleEntryReturnPressed( self, event ):
		"The scale entry return was pressed."
		self.repository.scale.value = float( self.scaleEntry.get() )
		self.save()
		self.phoenixUpdate()

	def setButtonImageText( self, button, text ):
		"Set the text of the e periodic buttons."
		photoImage = self.photoImages[ text ]
		if photoImage != None:
			button[ 'image' ] = photoImage
		button[ 'text' ] = text

	def setDisplayLayerIndex( self ):
		"Set the display of the layer index entry field and buttons."
		if self.repository.layerIndex.value < len( self.skeinPanes ) - 1:
			self.soarButton.config( state = preferences.Tkinter.NORMAL )
			self.upButton.config( state = preferences.Tkinter.NORMAL )
		else:
			self.soarButton.config( state = preferences.Tkinter.DISABLED )
			self.upButton.config( state = preferences.Tkinter.DISABLED )
		if self.repository.layerIndex.value > 0:
			self.downButton.config( state = preferences.Tkinter.NORMAL )
			self.diveButton.config( state = preferences.Tkinter.NORMAL )
		else:
			self.downButton.config( state = preferences.Tkinter.DISABLED )
			self.diveButton.config( state = preferences.Tkinter.DISABLED )
		preferences.setEntryText( self.indexEntry, self.repository.layerIndex.value )
		preferences.setEntryText( self.scaleEntry, self.repository.scale.value )

	def setMenuPanesPreferencesRootSkein( self, repository, skein, suffix ):
		"Set the menu bar, skein panes, tableau preferences, root and skein."
		self.column = 0
		self.imagesDirectoryPath = os.path.join( preferences.getSkeinforgeDirectoryPath(), 'images' )
		self.photoImages = {}
		self.row = 99
		self.movementTextID = None
		self.mouseInstantButtons = []
		self.repository = repository
		self.root = preferences.Tkinter.Tk()
		self.skein = skein
		self.skeinPanes = skein.skeinPanes
		self.suffix = suffix
		self.timerID = None
		self.fileHelpMenuBar = preferences.FileHelpMenuBar( self.root )
		self.fileHelpMenuBar.fileMenu.add_command( label = "Export", command = self.export )
		self.fileHelpMenuBar.fileMenu.add_separator()
		repository.slideShowRate.value = max( repository.slideShowRate.value, 0.01 )
		repository.slideShowRate.value = min( repository.slideShowRate.value, 85.0 )
		for menuRadio in repository.mouseMode.menuRadios:
			fileName = menuRadio.name.lower()
			fileName = fileName.replace( ' ', '_' ) + '.ppm'
			menuRadio.mouseButton = self.getPhotoButtonGridIncrement( menuRadio.invoke, fileName )

	def setMouseToolBindButtonMotion( self ):
		"Set the mouse tool and bind button one clicked, button one released and motion."
		self.canvasCenterComplex = complex( 0.5 * float( self.canvasWidth ), 0.5 * float( self.canvasHeight ) )
		self.canvasScreenCenterComplex = complex( self.canvasCenterComplex.real / float( self.screenSize.real ), self.canvasCenterComplex.imag / float( self.screenSize.imag ) )
		self.photoImages[ 'stop' ] = preferences.Tkinter.PhotoImage( file = os.path.join( self.imagesDirectoryPath, 'stop.ppm' ), master = self.root )
		self.diveButton = self.getPhotoButtonGridIncrement( self.dive, 'dive.ppm' )
		self.downButton = self.getPhotoButtonGridIncrement( self.down, 'down.ppm' )
		self.indexEntry = preferences.Tkinter.Entry( self.root )
		self.indexEntry.bind( '<Return>', self.indexEntryReturnPressed )
		self.indexEntry.grid( row = self.row, column = self.column, sticky = preferences.Tkinter.W )
		self.column += 1
		self.upButton = self.getPhotoButtonGridIncrement( self.up, 'up.ppm' )
		self.soarButton = self.getPhotoButtonGridIncrement( self.soar, 'soar.ppm' )
		for menuRadio in self.repository.mouseMode.menuRadios:
			menuRadio.mouseTool = menuRadio.constructorFunction().getReset( self )
			self.mouseTool = menuRadio.mouseTool
		self.activateMouseModeTool()
		self.addMouseInstantTool( 'zoom_in.ppm', zoom_in.getNewMouseTool() )
		self.scaleEntry = preferences.Tkinter.Entry( self.root )
		self.scaleEntry.bind( '<Return>', self.scaleEntryReturnPressed )
		self.scaleEntry.grid( row = self.row, column = self.column, sticky = preferences.Tkinter.W )
		self.column += 1
		self.addMouseInstantTool( 'zoom_out.ppm', zoom_out.getNewMouseTool() )
		self.canvas.bind( '<Button-1>', self.button1 )
		self.canvas.bind( '<ButtonRelease-1>', self.buttonRelease1 )
		self.canvas.bind( '<Motion>', self.motion )
		self.canvas.bind( '<Shift-ButtonRelease-1>', self.shiftButtonRelease1 )
		self.canvas.bind( '<Shift-Motion>', self.shiftMotion )
		self.indexEntry.bind( '<Destroy>', self.cancelTimer )
		self.resetPeriodicButtonsText()

	def shiftButtonRelease1( self, event ):
		"The button was released while the shift key was pressed."
		self.mouseTool.buttonRelease1( event, True )

	def shiftMotion( self, event ):
		"The mouse moved."
		self.mouseTool.motion( event, True )

	def soar( self ):
		"Soar, go up periodically."
		oldSoarButtonText = self.soarButton[ 'text' ]
		self.cancelTimerResetButtons()
		if oldSoarButtonText == 'stop':
			return
		self.soarCycle()

	def soarCycle( self ):
		"Start the soar cycle."
		self.cancelTimer()
		self.repository.layerIndex.value += 1
		self.saveUpdate()
		if self.repository.layerIndex.value > len( self.skeinPanes ) - 2:
			self.resetPeriodicButtonsText()
			return
		self.setButtonImageText( self.soarButton, 'stop' )
		self.timerID = self.canvas.after( self.getSlideShowDelay(), self.soarCycle )

	def up( self ):
		"Go up a layer."
		self.cancelTimerResetButtons()
		self.repository.layerIndex.value += 1
		self.saveUpdate()

	def updateDeiconify( self, center = complex( 0.5, 0.5 ) ):
		"Update and deiconify the window."
		self.centerUpdateSetWindowGeometryShowPreferences( center )
		self.update()
		self.root.deiconify()

	def updateNewDestroyOld( self, scrollPaneCenter ):
		"Update and deiconify a window and destroy the old."
		window = self.getCopy()
		window.index = self.repository.layerIndex.value
		window.updateDeiconify( scrollPaneCenter )
		self.root.destroy()

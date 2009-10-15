"""
Preferences is a collection of utilities to display, read & write preferences.

"""

from __future__ import absolute_import
#Init has to be imported first because it has code to workaround the python bug where relative imports don't work if the module is imported as a main module.
import __init__

from skeinforge_tools.skeinforge_utilities import gcodec
import cStringIO
import os
import shutil
import webbrowser
try:
	import Tkinter
except:
	print( 'You do not have Tkinter, which is needed for the graphical interface, you will only be able to use the command line.' )
	print( 'Information on how to download Tkinter is at:\nwww.tcl.tk/software/tcltk/' )


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/23/04 $"
__license__ = "GPL 3.0"

globalPreferencesDialogTable = {}
globalProfileSaveListenerTable = {}
globalCloseTables = [ globalPreferencesDialogTable, globalProfileSaveListenerTable ]
globalSpreadsheetSeparator = '\t'

def deleteDirectory( directory, subfolderName ):
	"Delete the directory if it exists."
	subDirectory = os.path.join( directory, subfolderName )
	if os.path.isdir( subDirectory ):
		shutil.rmtree( subDirectory )

def getArchiveText( archivablePreferences ):
	"Get the text representation of the archive."
	archiveWriter = cStringIO.StringIO()
	archiveWriter.write( 'Format is tab separated %s.\n' % archivablePreferences.title.lower() )
	archiveWriter.write( 'Name                          %sValue\n' % globalSpreadsheetSeparator )
	for preference in archivablePreferences.archive:
		preference.writeToArchiveWriter( archiveWriter )
	return archiveWriter.getvalue()

def getCraftTypeName( subName = '' ):
	"Get the craft type from the profile."
	profilePreferences = getReadProfilePreferences()
	craftTypeName = getSelectedPluginName( profilePreferences.craftRadios )
	if subName == '':
		return craftTypeName
	return os.path.join( craftTypeName, subName )

def getCraftTypePluginModule( craftTypeName = '' ):
	"Get the craft type plugin module."
	if craftTypeName == '':
		craftTypeName = getCraftTypeName()
	return gcodec.getModule( craftTypeName, 'profile_plugins', os.path.dirname( __file__ ) )

def getCraftTypeProfilesDirectoryPath( subfolder = '' ):
	"Get the craft type profiles directory path, which is the preferences directory joined with profiles, joined in turn with the craft type."
	craftTypeName = getCraftTypeName( subfolder )
	craftTypeProfileDirectory = getProfilesDirectoryPath( craftTypeName )
	return craftTypeProfileDirectory

def getDirectoryInAboveDirectory( directory ):
	"Get the directory in the above directory."
	aboveDirectory = os.path.dirname( os.path.dirname( os.path.abspath( __file__ ) ) )
	return os.path.join( aboveDirectory, directory )

def getDisplayedDialogFromConstructor( displayPreferences ):
	"Display the preferences dialog."
	getReadPreferences( displayPreferences )
	return PreferencesDialog( displayPreferences, Tkinter.Tk() )

def getDisplayToolButtons( directoryPath, importantFilenames, toolFileNames, visibleFilenames ):
	"Get the display tool buttons."
	displayToolButtons = []
	for toolFileName in toolFileNames:
		displayToolButton = DisplayToolButton().getFromFolderPath( directoryPath, toolFileName in importantFilenames, toolFileName, toolFileName in visibleFilenames )
		displayToolButtons.append( displayToolButton )
	return displayToolButtons

def getDocumentationPath( subName = '' ):
	"Get the documentation file path."
	numberOfLevelsDeepInPackageHierarchy = 2
	packageFilePath = os.path.abspath( __file__ )
	for level in xrange( numberOfLevelsDeepInPackageHierarchy + 1 ):
		packageFilePath = os.path.dirname( packageFilePath )
	documentationIndexPath = os.path.join( packageFilePath, 'documentation' )
	return os.path.join( documentationIndexPath, subName )

def getEachWordCapitalized( name ):
	"Get the capitalized name."
	withSpaces = name.lower().replace( '_', ' ' )
	words = withSpaces.split( ' ' )
	capitalizedStrings = []
	for word in words:
		capitalizedStrings.append( word.capitalize() )
	return ' '.join( capitalizedStrings )

def getFileInAlterationsOrGivenDirectory( directory, fileName ):
	"Get the file from the fileName or the lowercase fileName in the alterations directories, if there is no file look in the given directory."
	preferencesAlterationsDirectory = getPreferencesDirectoryPath( 'alterations' )
	makeDirectory( preferencesAlterationsDirectory )
	fileInPreferencesAlterationsDirectory = getFileInGivenDirectory( preferencesAlterationsDirectory, fileName )
	if fileInPreferencesAlterationsDirectory != '':
		return fileInPreferencesAlterationsDirectory
	alterationsDirectory = getDirectoryInAboveDirectory( 'alterations' )
	fileInAlterationsDirectory = getFileInGivenDirectory( alterationsDirectory, fileName )
	if fileInAlterationsDirectory != '':
		return fileInAlterationsDirectory
	if directory == '':
		directory = os.getcwd()
	return getFileInGivenDirectory( directory, fileName )

def getFileInGivenDirectory( directory, fileName ):
	"Get the file from the fileName or the lowercase fileName in the given directory."
	directoryListing = os.listdir( directory )
	lowerFilename = fileName.lower()
	for directoryFile in directoryListing:
		if directoryFile.lower() == lowerFilename:
			return getFileTextGivenDirectoryFileName( directory, directoryFile )
	return ''

def getFileTextGivenDirectoryFileName( directory, fileName ):
	"Get the entire text of a file with the given file name in the given directory."
	absoluteFilePath = os.path.join( directory, fileName )
	return gcodec.getFileText( absoluteFilePath )

def getFolders( directory ):
	"Get the folder list in a directory."
	makeDirectory( directory )
	directoryListing = []
	try:
		directoryListing = os.listdir( directory )
	except OSError:
		print( 'Skeinforge can not list the directory:' )
		print( directory )
		print( 'so give it read/write permission for that directory.' )
	folders = []
	for fileName in directoryListing:
		if os.path.isdir( os.path.join( directory, fileName ) ):
			folders.append( fileName )
	return folders

def getLowerNameSetHelpTitleWindowPosition( displayPreferences, fileNameHelp ):
	"Set the help & preferences file path, the title and the window position archiver."
	lastDotIndex = fileNameHelp.rfind( '.' )
	lowerName = fileNameHelp[ : lastDotIndex ]
	lastTruncatedDotIndex = lowerName.rfind( '.' )
	displayPreferences.lowerName = lowerName[ lastTruncatedDotIndex + 1 : ]
	displayPreferences.capitalizedName = displayPreferences.lowerName.replace( '_', ' ' ).capitalize()
	displayPreferences.title = displayPreferences.capitalizedName + ' Preferences'
	windowPositionName = 'windowPosition' + displayPreferences.title
	displayPreferences.windowPositionPreferences = WindowPosition().getFromValue( windowPositionName, '0+0' )
	displayPreferences.archive.append( displayPreferences.windowPositionPreferences )
	displayPreferences.fileNameHelp = fileNameHelp
	return displayPreferences.lowerName + '.csv'

def getPreferencesDirectoryPath( subfolder = '' ):
	"Get the preferences directory path, which is the home directory joined with .skeinforge."
	preferencesDirectory = os.path.join( os.path.expanduser( '~' ), '.skeinforge' )
	if subfolder == '':
		return preferencesDirectory
	return os.path.join( preferencesDirectory, subfolder )

def getProfilesDirectoryPath( subfolder = '' ):
	"Get the profiles directory path, which is the preferences directory joined with profiles."
	profilesDirectory = getPreferencesDirectoryPath( 'profiles' )
	if subfolder == '':
		return profilesDirectory
	return os.path.join( profilesDirectory, subfolder )

def getProfilesDirectoryInAboveDirectory( subName = '' ):
	"Get the profiles directory path in the above directory."
	aboveProfilesDirectory = getDirectoryInAboveDirectory( 'profiles' )
	if subName == '':
		return aboveProfilesDirectory
	return os.path.join( aboveProfilesDirectory, subName )

def getReadPreferences( archivablePreferences ):
	"Read and return preferences from a file."
	text = gcodec.getFileText( getProfilesDirectoryPath( archivablePreferences.baseName ), 'r', False )
	if text == '':
		print( 'The default %s will be written in the .skeinforge folder in the home directory.' % archivablePreferences.title.lower() )
		text = gcodec.getFileText( getProfilesDirectoryInAboveDirectory( archivablePreferences.baseName ), 'r', False )
		if text != '':
			readPreferencesFromText( archivablePreferences, text )
		writePreferences( archivablePreferences )
		return archivablePreferences
	readPreferencesFromText( archivablePreferences, text )
	return archivablePreferences

def getReadProfilePreferences():
	"Get the read profile preferences."
	return getReadPreferences( ProfilePreferences() )

def getSelectedPluginModuleFromPath( filePath, plugins ):
	"Get the selected plugin module."
	for plugin in plugins:
		if plugin.value:
			return gcodec.getModuleFromPath( plugin.name, filePath )
	return None

def getSelectedPluginName( plugins ):
	"Get the selected plugin name."
	for plugin in plugins:
		if plugin.value:
			return plugin.name
	return ''

def getSelectedCraftTypeProfile( craftTypeName = '' ):
	"Get the selected profile.getPreferencesConstructor"
	craftTypePreferences = getCraftTypePluginModule( craftTypeName ).getPreferencesConstructor()
	getReadPreferences( craftTypePreferences )
	return craftTypePreferences.profileListbox.value

def getSubfolderWithBasename( basename, directory ):
	"Get the subfolder in the directory with the basename."
	makeDirectory( directory )
	directoryListing = os.listdir( directory )
	for fileName in directoryListing:
		joinedFileName = os.path.join( directory, fileName )
		if os.path.isdir( joinedFileName ):
			if basename == fileName:
				return joinedFileName
	return None

def makeDirectory( directory ):
	"Make a directory if it does not already exist."
	if os.path.isdir( directory ):
		return
	try:
		os.makedirs( directory )
	except OSError:
		print( 'Skeinforge can not make the directory %s so give it read/write permission for that directory and the containing directory.' % directory )

def openWebPage( webPagePath ):
	"Open a web page in a browser."
	webPagePath = '"' + os.path.normpath( webPagePath ) + '"' # " to get around space in url bug
	try:
		os.startfile( webPagePath )#this is available on some python environments, but not all
		return
	except:
		pass
	webbrowserName = webbrowser.get().name
	if webbrowserName == '':
		print( 'Skeinforge was not able to open the documentation file in a web browser.  To see the documentation, open the following file in a web browser:' )
		print( webPagePath )
		return
	os.system( webbrowser.get().name + ' ' + webPagePath )#used this instead of webbrowser.open() to workaround webbrowser open() bug

def quitWindow( root ):
	"Quit a window."
	try:
		root.destroy()
	except:
		pass

def quitWindows():
	"Quit all windows."
	global globalPreferencesDialogTable
	globalPreferencesDialogValues = globalPreferencesDialogTable.values()
	for globalPreferencesDialogValue in globalPreferencesDialogValues:
		quitWindow( globalPreferencesDialogValue.root )

def readPreferencesFromText( archivablePreferences, text ):
	"Read preferences from a text."
	lines = gcodec.getTextLines( text )
	preferenceTable = {}
	for preference in archivablePreferences.archive:
		preference.addToPreferenceTable( preferenceTable )
	for lineIndex in xrange( len( lines ) ):
		setArchiveToLine( lineIndex, lines, preferenceTable )

def removeFromTable( hashtable, key ):
	"Remove an entry from a hashtable if it exists."
	if key in hashtable:
		del hashtable[ key ]

def setArchiveToLine( lineIndex, lines, preferenceTable ):
	"Set an archive to a preference line."
	line = lines[ lineIndex ]
	splitLine = line.split( globalSpreadsheetSeparator )
	if len( splitLine ) < 2:
		return
	filePreferenceName = splitLine[ 0 ]
	if filePreferenceName in preferenceTable:
		preferenceTable[ filePreferenceName ].setValueToSplitLine( lineIndex, lines, splitLine )

def setCraftProfileArchive( craftSequence, defaultProfile, displayPreferences, fileNameHelp ):
	"Set the craft profile archive."
	displayPreferences.archive = []
	displayPreferences.baseName = getLowerNameSetHelpTitleWindowPosition( displayPreferences, fileNameHelp )
	displayPreferences.profileList = ProfileList().getFromName( displayPreferences.lowerName, 'Profile List:' )
	displayPreferences.archive.append( displayPreferences.profileList )
	displayPreferences.profileListbox = ProfileListboxPreference().getFromListPreference( displayPreferences.profileList, 'Profile Selection:', defaultProfile )
	displayPreferences.archive.append( displayPreferences.profileListbox )
	displayPreferences.addListboxSelection = AddProfile().getFromProfileListboxPreference( displayPreferences.profileListbox )
	displayPreferences.archive.append( displayPreferences.addListboxSelection )
	displayPreferences.deleteListboxSelection = DeleteProfile().getFromProfileListboxPreference( displayPreferences.profileListbox )
	displayPreferences.archive.append( displayPreferences.deleteListboxSelection )
	#Create the archive, title of the dialog & preferences fileName.
	displayPreferences.executeTitle = None
	displayPreferences.saveCloseTitle = 'Save and Close'
	directoryName = getProfilesDirectoryPath()
	makeDirectory( directoryName )
	displayPreferences.windowPositionPreferences.value = '0+400'

def setHelpPreferencesFileNameTitleWindowPosition( displayPreferences, fileNameHelp ):
	"Set the help & preferences file path, the title and the window position archiver."
	baseName = getLowerNameSetHelpTitleWindowPosition( displayPreferences, fileNameHelp )
	craftTypeName = getCraftTypeName()
	selectedCraftTypeProfileBaseName  = os.path.join( getSelectedCraftTypeProfile( craftTypeName ), baseName )
	displayPreferences.baseName = os.path.join( craftTypeName, selectedCraftTypeProfileBaseName )
	dotsMinusOne = fileNameHelp.count( '.' ) - 1
	x = 0
	xAddition = 400
	for step in xrange( dotsMinusOne ):
		x += xAddition
		xAddition /= 2
	displayPreferences.windowPositionPreferences.value = '%s+0' % x

def startMainLoopFromConstructor( displayPreferences ):
	"Display the preferences dialog and start the main loop."
	getDisplayedDialogFromConstructor( displayPreferences ).root.mainloop()

def updateProfileSaveListeners():
	"Call the save function of all the update profile save listeners."
	global globalProfileSaveListenerTable
	for globalProfileSaveListeners in globalProfileSaveListenerTable.values():
		globalProfileSaveListeners.save()

def writePreferences( archivablePreferences ):
	"Write the preferences to a file."
	profilesDirectoryPath = getProfilesDirectoryPath( archivablePreferences.baseName )
	makeDirectory( os.path.dirname( profilesDirectoryPath ) )
	gcodec.writeFileText( profilesDirectoryPath, getArchiveText( archivablePreferences ) )


class AddListboxSelection:
	"A class to add the selection of a listbox preference."
	def addToDialog( self, preferencesDialog ):
		"Add this to the dialog."
		self.entry = Tkinter.Entry( preferencesDialog.root )
		self.entry.bind( '<Return>', self.addSelectionWithEvent )
		self.entry.grid( row = preferencesDialog.row, column = 1, columnspan = 3, sticky = Tkinter.W )
		self.addButton = Tkinter.Button( preferencesDialog.root, activebackground = 'black', activeforeground = 'white', text = 'Add Listbox Selection', command = self.addSelection )
		self.addButton.grid( row = preferencesDialog.row, column = 0 )
		preferencesDialog.row += 1

	def addSelection( self ):
		"Add the selection of a listbox preference."
		entryText = self.entry.get()
		if entryText == '':
			print( 'To add to the selection, enter the material name.' )
			return
		self.entry.delete( 0, Tkinter.END )
		self.listboxPreference.listPreference.value.append( entryText )
		self.listboxPreference.listPreference.value.sort()
		self.listboxPreference.value = entryText
		self.listboxPreference.setListboxItems()
		self.listboxPreference.setToDisplay()

	def addSelectionWithEvent( self, event ):
		"Add the selection of a listbox preference, given an event."
		self.addSelection()

	def addToPreferenceTable( self, preferenceTable ):
		"Do nothing because the add listbox selection is not archivable."
		pass

	def getFromListboxPreference( self, listboxPreference ):
		"Initialize."
		self.listboxPreference = listboxPreference
		return self

	def setToDisplay( self ):
		"Do nothing because the add listbox selection is not archivable."
		pass

	def writeToArchiveWriter( self, archiveWriter ):
		"Do nothing because the add listbox selection is not archivable."
		pass


class AddProfile:
	"A class to add a profile."
	def addToDialog( self, preferencesDialog ):
		"Add this to the dialog."
		self.entry = Tkinter.Entry( preferencesDialog.root )
		self.entry.bind( '<Return>', self.addSelectionWithEvent )
		self.entry.grid( row = preferencesDialog.row, column = 1, columnspan = 3, sticky = Tkinter.W )
		self.addButton = Tkinter.Button( preferencesDialog.root, activebackground = 'black', activeforeground = 'white', text = 'Add Profile', command = self.addSelection )
		self.addButton.grid( row = preferencesDialog.row, column = 0 )
		preferencesDialog.row += 1

	def addSelection( self ):
		"Add the selection of a listbox preference."
		entryText = self.entry.get()
		if entryText == '':
			print( 'To add to the profiles, enter the material name.' )
			return
		self.profileListboxPreference.listPreference.setValueToFolders()
		if entryText in self.profileListboxPreference.listPreference.value:
			print( 'There is already a profile by the name of %s, so no profile will be added.' % entryText )
			return
		self.entry.delete( 0, Tkinter.END )
		craftTypeProfileDirectory = getProfilesDirectoryPath( self.profileListboxPreference.listPreference.craftTypeName )
		destinationDirectory = os.path.join( craftTypeProfileDirectory, entryText )
		shutil.copytree( self.profileListboxPreference.getSelectedFolder(), destinationDirectory )
		self.profileListboxPreference.listPreference.setValueToFolders()
		self.profileListboxPreference.value = entryText
		self.profileListboxPreference.setListboxItems()

	def addSelectionWithEvent( self, event ):
		"Add the selection of a listbox preference, given an event."
		self.addSelection()

	def addToPreferenceTable( self, preferenceTable ):
		"Do nothing because the add listbox selection is not archivable."
		pass

	def getFromProfileListboxPreference( self, profileListboxPreference ):
		"Initialize."
		self.profileListboxPreference = profileListboxPreference
		return self

	def setToDisplay( self ):
		"Do nothing because the add listbox selection is not archivable."
		pass

	def writeToArchiveWriter( self, archiveWriter ):
		"Do nothing because the add listbox selection is not archivable."
		pass


class StringPreference:
	"A class to display, read & write a string."
	def __init__( self ):
		"Set the update function to none."
		self.updateFunction = None

	def addToDialog( self, preferencesDialog ):
		"Add this to the dialog."
		self.entry = Tkinter.Entry( preferencesDialog.root )
		self.setStateToValue()
		self.entry.grid( row = preferencesDialog.row, column = 3, columnspan = 2, sticky = Tkinter.W )
		self.label = Tkinter.Label( preferencesDialog.root, text = self.name )
		self.label.grid( row = preferencesDialog.row, column = 0, columnspan = 3, sticky = Tkinter.W )
		preferencesDialog.row += 1

	def addToPreferenceTable( self, preferenceTable ):
		"Add this to the preference table."
		preferenceTable[ self.name ] = self

	def getFromValue( self, name, value ):
		"Initialize."
		self.value = value
		self.name = name
		return self

	def setStateToValue( self ):
		"Set the entry to the value."
		try:
			self.entry.delete( 0, Tkinter.END )
			self.entry.insert( 0, self.value )
		except:
			pass

	def setToDisplay( self ):
		"Set the string to the entry field."
		try:
			valueString = self.entry.get()
			self.setValueToString( valueString )
		except:
			pass

	def setUpdateFunction( self, updateFunction ):
		"Set the update function."
		self.updateFunction = updateFunction

	def setValueToSplitLine( self, lineIndex, lines, splitLine ):
		"Set the value to the second word of a split line."
		self.setValueToString( splitLine[ 1 ] )

	def setValueToString( self, valueString ):
		"Set the string to the value string."
		self.value = valueString

	def writeToArchiveWriter( self, archiveWriter ):
		"Write tab separated name and value to the archive writer."
		archiveWriter.write( '%s%s%s\n' % ( self.name, globalSpreadsheetSeparator, self.value ) )


class BooleanPreference( StringPreference ):
	"A class to display, read & write a boolean."
	def addToDialog( self, preferencesDialog ):
		"Add this to the dialog."
		self.checkbutton = Tkinter.Checkbutton( preferencesDialog.root, command = self.toggleCheckbox, text = self.name )
#toggleCheckbox is being used instead of a Tkinter IntVar because there is a weird bug where it doesn't work properly if this preference is not on the first window.
		self.checkbutton.grid( row = preferencesDialog.row, columnspan = 5, sticky = Tkinter.W )
		self.setStateToValue()
		preferencesDialog.row += 1

	def setStateToValue( self ):
		"Set the checkbox to the boolean."
		try:
			if self.value:
				self.checkbutton.select()
			else:
				self.checkbutton.deselect()
		except:
			pass

	def setToDisplay( self ):
		"Do nothing because toggleCheckbox is handling the value."
		pass

	def setValueToString( self, valueString ):
		"Set the boolean to the string."
		self.value = ( valueString.lower() == 'true' )

	def toggleCheckbox( self ):
		"Workaround for Tkinter bug, toggle the value."
		self.value = not self.value
		self.setStateToValue()
		if self.updateFunction != None:
			self.updateFunction()


class CloseListener:
	"A class to listen to link a window to the globalPreferencesDialogTable."
	def __init__( self, lowerName, window ):
		"Add the root to the globalPreferencesDialogTable."
		self.lowerName = lowerName
		self.window = window
		self.shouldWasClosedBeBound = True
		global globalPreferencesDialogTable
		globalPreferencesDialogTable[ lowerName ] = window

	def listenToWidget( self, widget ):
		"Listen to the destroy message of the widget."
		if self.shouldWasClosedBeBound:
			self.shouldWasClosedBeBound = False
			widget.bind( '<Destroy>', self.wasClosed )

	def wasClosed( self, event ):
		"The dialog was closed."
		global globalCloseTables
		for globalCloseTable in globalCloseTables:
			removeFromTable( globalCloseTable, self.lowerName )


class DeleteListboxSelection( AddListboxSelection ):
	"A class to delete the selection of a listbox preference."
	def addToDialog( self, preferencesDialog ):
		"Add this to the dialog."
		self.deleteButton = Tkinter.Button( preferencesDialog.root, activebackground = 'black', activeforeground = 'white', text = "Delete Listbox Selection", command = self.deleteSelection )
		self.deleteButton.grid( row = preferencesDialog.row, column = 0 )
		preferencesDialog.row += 1

	def deleteSelection( self ):
		"Delete the selection of a listbox preference."
		self.listboxPreference.setToDisplay()
		if self.listboxPreference.value not in self.listboxPreference.listPreference.value:
			return
		self.listboxPreference.listPreference.value.remove( self.listboxPreference.value )
		self.listboxPreference.setListboxItems()
		self.listboxPreference.listbox.select_set( 0 )
		self.listboxPreference.setToDisplay()


class DeleteProfile( AddProfile ):
	"A class to delete the selection of a listbox profile."
	def addToDialog( self, preferencesDialog ):
		"Add this to the dialog."
		self.deleteButton = Tkinter.Button( preferencesDialog.root, activebackground = 'black', activeforeground = 'white', text = "Delete Profile", command = self.deleteSelection )
		self.deleteButton.grid( row = preferencesDialog.row, column = 0 )
		preferencesDialog.row += 1

	def deleteSelection( self ):
		"Delete the selection of a listbox preference."
		DeleteProfileDialog( self.profileListboxPreference, Tkinter.Tk() )


class DeleteProfileDialog:
	def __init__( self, profileListboxPreference, root ):
		"Display a delete dialog."
		self.profileListboxPreference = profileListboxPreference
		self.root = root
		self.row = 0
		root.title( 'Delete Warning' )
		self.label = Tkinter.Label( self.root, text = 'Do you want to delete the profile?' )
		self.label.grid( row = self.row, column = 0, columnspan = 3, sticky = Tkinter.W )
		self.row += 1
		columnIndex = 1
		deleteButton = Tkinter.Button( root, activebackground = 'black', activeforeground = 'red', command = self.delete, fg = 'red', text = 'Delete' )
		deleteButton.grid( row = self.row, column = columnIndex )
		columnIndex += 1
		noButton = Tkinter.Button( root, activebackground = 'black', activeforeground = 'darkgreen', command = self.no, fg = 'darkgreen', text = 'Do Nothing' )
		noButton.grid( row = self.row, column = columnIndex )

	def delete( self ):
		"Delete the selection of a listbox preference."
		self.profileListboxPreference.setToDisplay()
		self.profileListboxPreference.listPreference.setValueToFolders()
		if self.profileListboxPreference.value not in self.profileListboxPreference.listPreference.value:
			return
		lastSelectionIndex = 0
		currentSelectionTuple = self.profileListboxPreference.listbox.curselection()
		if len( currentSelectionTuple ) > 0:
			lastSelectionIndex = int( currentSelectionTuple[ 0 ] )
		else:
			print( 'No profile is selected, so no profile will be deleted.' )
			return
		deleteDirectory( getProfilesDirectoryPath( self.profileListboxPreference.listPreference.craftTypeName ), self.profileListboxPreference.value )
		deleteDirectory( getProfilesDirectoryInAboveDirectory( self.profileListboxPreference.listPreference.craftTypeName ), self.profileListboxPreference.value )
		self.profileListboxPreference.listPreference.setValueToFolders()
		if len( self.profileListboxPreference.listPreference.value ) < 1:
			defaultPreferencesDirectory = getProfilesDirectoryPath( os.path.join( self.profileListboxPreference.listPreference.craftTypeName, self.profileListboxPreference.defaultValue ) )
			makeDirectory( defaultPreferencesDirectory )
			self.profileListboxPreference.listPreference.setValueToFolders()
		lastSelectionIndex = min( lastSelectionIndex, len( self.profileListboxPreference.listPreference.value ) - 1 )
		self.profileListboxPreference.value = self.profileListboxPreference.listPreference.value[ lastSelectionIndex ]
		self.profileListboxPreference.setListboxItems()
		self.no()

	def no( self ):
		"The dialog was closed."
		self.root.destroy()


class DisplayToolButtonBesidePrevious:
	"A class to display the tool preferences dialog beside the previous preference dialog element."
	def addButtonBesidesPrevious( self, preferencesDialog ):
		"Add this to the dialog."
		self.createDisplayButton( preferencesDialog )
		self.displayButton.grid( row = preferencesDialog.row - 1, column = 3, columnspan = 2 )

	def addToDialog( self, preferencesDialog ):
		"Add this to the dialog."
		self.addButtonBesidesPrevious( preferencesDialog )

	def addToPreferenceTable( self, preferenceTable ):
		"Add this to the preference table."
		preferenceTable[ self.name + 'Button' ] = self

	def createDisplayButton( self, preferencesDialog ):
		"Create the display button."
		self.displayPreferencesLowerName = preferencesDialog.displayPreferences.lowerName
		self.displayButton = Tkinter.Button( preferencesDialog.root, activebackground = 'black', activeforeground = 'white', text = getEachWordCapitalized( self.name ), command = self.displayFunction )
		preferencesDialog.openDialogListeners.append( self )

	def getFromFolderPath( self, folderPath, important, name, value ):
		"Initialize."
		self.displayPreferencesLowerName = None
		self.displayFunction = ToolDialog().getDisplayFromFolderPath( folderPath, name )
		self.important = important
		self.name = name
		self.value = value
		return self

	def getLowerName( self ):
		"Get the lower case name."
		return self.name.lower()

	def openDialog( self ):
		"Create the display button."
		if self.value:
			self.displayFunction()

	def setToDisplay( self ):
		"Do nothing because the button does not have a state."
		pass

	def setValueToSplitLine( self, lineIndex, lines, splitLine ):
		"Set the value to the second word of a split line."
		self.setValueToString( splitLine[ 1 ] )

	def setValueToString( self, valueString ):
		"Set the string to the value string."
		self.value = ( valueString.lower() == 'true' )

	def writeToArchiveWriter( self, archiveWriter ):
		"Write tab separated name and value to the archive writer."
		global globalPreferencesDialogTable
		if self.displayPreferencesLowerName in globalPreferencesDialogTable:
			self.value = self.getLowerName() in globalPreferencesDialogTable
		archiveWriter.write( '%s%s%s\n' % ( self.name + 'Button', globalSpreadsheetSeparator, self.value ) )


class DisplayProfileButton( DisplayToolButtonBesidePrevious ):
	"A class to display the profile button."
	def addToDialog( self, preferencesDialog ):
		"Add this to the dialog."
		self.addButtonBesidesPrevious( preferencesDialog )
		preferencesDialog.saveListenerTable[ 'updateProfileSaveListeners' ] = updateProfileSaveListeners


class DisplayToolButton( DisplayToolButtonBesidePrevious ):
	"A class to display the tool preferences dialog, in a two column wide table."
	def addToDialog( self, preferencesDialog ):
		"Add this to the dialog."
		self.createDisplayButton( preferencesDialog )
		try:
			weightString = 'normal'
			if self.important:
				weightString = 'bold'
			splitFont = self.displayButton[ 'font' ].split()
			self.displayButton[ 'font' ] = ( splitFont[ 0 ], splitFont[ 1 ], weightString )
		except:
			pass
		if preferencesDialog.displayToolButtonStart:
			self.displayButton.grid( row = preferencesDialog.row, column = 0 )
			preferencesDialog.row += 1
			preferencesDialog.displayToolButtonStart = False
		else:
			self.displayButton.grid( row = preferencesDialog.row - 1, column = 3 )
			preferencesDialog.displayToolButtonStart = True


class FileHelpMenuBar:
	def __init__( self, root ):
		"Create a menu bar with a file and help menu."
		self.menuBar = Tkinter.Menu( root )
		root.config( menu = self.menuBar )
		self.fileMenu = Tkinter.Menu( self.menuBar, tearoff = 0 )
		self.menuBar.add_cascade( label = "File", menu = self.fileMenu )
		self.helpMenu = Tkinter.Menu( self.menuBar, tearoff = 0 )
		self.menuBar.add_cascade( label = "Help", menu = self.helpMenu )
		self.profilesMenu = Tkinter.Menu( self.menuBar, tearoff = 0 )
		self.menuBar.add_cascade( label = "Profiles", menu = self.profilesMenu )
		self.profileRadioVar = Tkinter.StringVar()
		self.toolsMenu = Tkinter.Menu( self.menuBar, tearoff = 0 )
		self.menuBar.add_cascade( label = "Tools", menu = self.toolsMenu )

	def addProfilePluginMenu( self, craftTypeName, profilePluginFilename ):
		"Add a profile plugin menu."
		pluginModule = getCraftTypePluginModule( profilePluginFilename )
		profilePluginPreferences = getReadPreferences( pluginModule.getPreferencesConstructor() )
		isSelected = ( craftTypeName == profilePluginFilename )
		profileSubmenu = Tkinter.Menu( self.profilesMenu, tearoff = 0 )
		self.profilesMenu.add_cascade( label = profilePluginFilename.capitalize(), menu = profileSubmenu )
		for profileName in profilePluginPreferences.profileList.value:
			ProfileMenuRadio( profilePluginFilename, profileSubmenu, profileName, self.profileRadioVar, isSelected and profileName == profilePluginPreferences.profileListbox.value )

	def addToolPluginMenu( self, directoryFolders, pluginFilename ):
		"Add a tool plugin menu."
		capitalizedPluginFilename = pluginFilename.capitalize()
		pluginFolderName = pluginFilename + '_plugins'
		if pluginFolderName in directoryFolders:
			self.addToolPluginSubmenus( capitalizedPluginFilename, pluginFilename, pluginFolderName )
		else:
			ToolDialog().addPluginToMenu( self.skeinforgeToolsPath, self.toolsMenu, pluginFilename )

	def addToolPluginSubmenu( self, pluginFolderPath, subDirectoryFolders, submenuFilename, toolSubmenu ):
		"Add a tool plugin submenu."
		submenuFolderName = submenuFilename + '_plugins'
		submenuFolderPath = os.path.join( pluginFolderPath, submenuFolderName )
		if submenuFolderName not in subDirectoryFolders:
			ToolDialog().addPluginToMenu( pluginFolderPath, toolSubmenu, submenuFilename )
			return
		capitalizedPluginSubmenuFilename = submenuFilename.capitalize()
		pluginSubmenu = Tkinter.Menu( toolSubmenu, tearoff = 0 )
		toolSubmenu.add_cascade( label = capitalizedPluginSubmenuFilename, menu = pluginSubmenu )
		ToolDialog().addPluginToMenu( self.skeinforgeToolsPath, pluginSubmenu, submenuFilename )
		pluginSubmenu.add_separator()
		pluginSubmenuFilenames = gcodec.getPluginFilenamesFromDirectoryPath( submenuFolderPath )
		for pluginSubmenuFilename in pluginSubmenuFilenames:
			ToolDialog().addPluginToMenu( submenuFolderPath, pluginSubmenu, pluginSubmenuFilename )

	def addToolPluginSubmenus( self, capitalizedPluginFilename, pluginFilename, pluginFolderName ):
		"Add a tool plugin submenus."
		toolSubmenu = Tkinter.Menu( self.toolsMenu, tearoff = 0 )
		self.toolsMenu.add_cascade( label = capitalizedPluginFilename, menu = toolSubmenu )
		ToolDialog().addPluginToMenu( self.skeinforgeToolsPath, toolSubmenu, pluginFilename )
		toolSubmenu.add_separator()
		pluginFolderPath = os.path.join( self.skeinforgeToolsPath, pluginFolderName )
		submenuFilenames = gcodec.getPluginFilenamesFromDirectoryPath( pluginFolderPath )
		subDirectoryFolders = getFolders( pluginFolderPath )
		for submenuFilename in submenuFilenames:
			self.addToolPluginSubmenu( pluginFolderPath, subDirectoryFolders, submenuFilename, toolSubmenu )

	def completeMenu( self, closeFunction, lowerName ):
		"Complete the menu."
		self.fileMenu.add_command( label = "Close", command = closeFunction )
		self.fileMenu.add_separator()
		self.fileMenu.add_command( label = "Quit", command = quitWindows )
		self.helpMenu.add_separator()
		self.forumsMenu = Tkinter.Menu( self.helpMenu, tearoff = 0 )
		self.helpMenu.add_cascade( label = "Forums", menu = self.forumsMenu )
		self.forumsMenu.add_command( label = 'Bits from Bytes Printing', command = HelpPage().getOpenFromAfterWWW( 'bitsfrombytes.com/fora/user/index.php?board=5.0' ) )
		self.forumsMenu.add_command( label = 'Bits from Bytes Software', command = HelpPage().getOpenFromAfterWWW( 'bitsfrombytes.com/fora/user/index.php?board=4.0' ) )
		self.forumsMenu.add_separator()
		self.forumsMenu.add_command( label = 'Skeinforge Contributions', command = HelpPage().getOpenFromAfterHTTP( 'dev.forums.reprap.org/read.php?12,27562' ) )
		self.forumsMenu.add_command( label = 'Skeinforge Powwow', command = HelpPage().getOpenFromAfterHTTP( 'dev.forums.reprap.org/read.php?12,20013' ) )
		self.forumsMenu.add_command( label = 'Skeinforge Settings', command = HelpPage().getOpenFromAfterHTTP( 'dev.forums.reprap.org/read.php?12,27434' ) )
		self.helpMenu.add_command( label = 'Index', command = HelpPage().getOpenFromDocumentationSubName( '' ) )
		self.helpMenu.add_command( label = 'Manual', command = HelpPage().getOpenFromAfterWWW( 'bitsfrombytes.com/wiki/index.php?title=Skeinforge' ) )
		self.helpMenu.add_command( label = 'Overview', command = HelpPage().getOpenFromDocumentationSubName( 'skeinforge.html' ) )
		self.skeinforgeUtilitiesPath = os.path.dirname( __file__ )
		self.skeinforgeToolsPath = os.path.dirname( self.skeinforgeUtilitiesPath )
		self.profilePluginFilenames = gcodec.getPluginFilenamesFromDirectoryPath( os.path.join( self.skeinforgeToolsPath, 'profile_plugins' ) )
		self.completeProfilesMenu()
		ToolDialog().addPluginToMenu( os.path.dirname( self.skeinforgeToolsPath ), self.toolsMenu, 'Skeinforge'  )
		pluginFilenames = gcodec.getPluginFilenamesFromDirectoryPath( self.skeinforgeToolsPath )
		directoryFolders = getFolders( self.skeinforgeToolsPath )
		for pluginFilename in pluginFilenames:
			self.addToolPluginMenu( directoryFolders, pluginFilename )
		global globalProfileSaveListenerTable
		globalProfileSaveListenerTable[ lowerName ] = self

	def completeProfilesMenu( self ):
		"Complete the menu."
		craftTypeName = getCraftTypeName()
		for profilePluginFilename in self.profilePluginFilenames:
			self.addProfilePluginMenu( craftTypeName, profilePluginFilename )

	def save( self ):
		"Profile has been saved and profile menu should be updated."
		lastMenuIndex = None
		try:
			lastMenuIndex = self.profilesMenu.index( Tkinter.END )
		except:
			return
		if lastMenuIndex == None:
			return
		self.profilesMenu.delete( 0, lastMenuIndex )
		self.completeProfilesMenu()


class Filename( StringPreference ):
	"A class to display, read & write a fileName."
	def addToDialog( self, preferencesDialog ):
		"Add this to the dialog."
		preferencesDialog.executables.append( self )

	def execute( self ):
		"Open the file picker."
		try:
			import tkFileDialog
			summarized = gcodec.getSummarizedFilename( self.value )
			initialDirectory = os.path.dirname( summarized )
			if len( initialDirectory ) > 0:
				initialDirectory += os.sep
			else:
				initialDirectory = "."
			fileName = tkFileDialog.askopenfilename( filetypes = self.getFilenameFirstTypes(), initialdir = initialDirectory, initialfile = os.path.basename( summarized ), title = self.name )
			self.setCancelledValue( fileName )
			return
		except:
			print( 'Could not get the old directory in preferences, so the file picker will be opened in the default directory.' )
		try:
			fileName = tkFileDialog.askopenfilename( filetypes = self.getFilenameFirstTypes(), initialdir = '.', initialfile = '', title = self.name )
			self.setCancelledValue( fileName )
		except:
			print( 'Error in execute in Filename in preferences, ' + self.name )

	def getFromFilename( self, fileTypes, name, value ):
		"Initialize."
		self.getFromValue( name, value )
		self.fileTypes = fileTypes
		self.wasCancelled = False
		return self

	def getFilenameFirstTypes( self ):
		"Get the file types with the file type of the fileName moved to the front of the list."
		try:
			basename = os.path.basename( self.value )
			splitFile = basename.split( '.' )
			allReadables = []
			if len( self.fileTypes ) > 1:
				for fileType in self.fileTypes:
					allReadable = ( ( 'All Readable', fileType[ 1 ] ) )
					allReadables.append( allReadable )
			if len( splitFile ) < 1:
				return self.fileTypes + allReadables
			baseExtension = splitFile[ - 1 ]
			for fileType in self.fileTypes:
				fileExtension = fileType[ 1 ].split( '.' )[ - 1 ]
				if fileExtension == baseExtension:
					fileNameFirstTypes = self.fileTypes[ : ]
					fileNameFirstTypes.remove( fileType )
					return [ fileType ] + fileNameFirstTypes + allReadables
			return self.fileTypes + allReadables
		except:
			return [ ( 'All', '*.*' ) ]

	def setCancelledValue( self, fileName ):
		"Set the value to the file name and wasCancelled true if a file was not picked."
		if ( str( fileName ) == '()' or str( fileName ) == '' ):
			self.wasCancelled = True
		else:
			self.value = fileName

	def setToDisplay( self ):
		"Do nothing because the file dialog is handling the value."
		pass


class FloatPreference( StringPreference ):
	"A class to display, read & write a float."
	def setStateToValue( self ):
		"Set the entry to the value."
		try:
			self.entry.delete( 0, Tkinter.END )
			self.entry.insert( 0, str( self.value ) )
		except:
			pass

	def setUpdateFunction( self, updateFunction ):
		"Set the update function."
		self.entry.bind( '<Return>', updateFunction )

	def setValueToString( self, valueString ):
		"Set the float to the string."
		try:
			self.value = float( valueString )
		except:
			print( 'Oops, can not read float' + self.name + ' ' + valueString )


class HelpPage:
	def getOpenFromAbsolute( self, hypertextAddress ):
		"Get the open help page function from the hypertext address."
		self.hypertextAddress = hypertextAddress
		return self.openPage

	def getOpenFromAfterHTTP( self, afterHTTP ):
		"Get the open help page function from the part of the address after the HTTP."
		self.hypertextAddress = 'http://' + afterHTTP
		return self.openPage

	def getOpenFromAfterWWW( self, afterWWW ):
		"Get the open help page function from the afterWWW of the address after the www."
		self.hypertextAddress = 'http://www.' + afterWWW
		return self.openPage

	def getOpenFromDocumentationSubName( self, subName = '' ):
		"Get the open help page function from the afterWWW of the address after the www."
		self.hypertextAddress = getDocumentationPath( subName )
		return self.openPage

	def openPage( self ):
		"Open the browser to the hypertext address."
		openWebPage( self.hypertextAddress )


class IntPreference( FloatPreference ):
	"A class to display, read & write an int."
	def setValueToString( self, valueString ):
		"Set the integer to the string."
		dotIndex = valueString.find( '.' )
		if dotIndex > - 1:
			valueString = valueString[ : dotIndex ]
		try:
			self.value = int( valueString )
		except:
			print( 'Oops, can not read integer ' + self.name + ' ' + valueString )


class LabelDisplay:
	"A class to add a label."
	def addToDialog( self, preferencesDialog ):
		"Add this to the dialog."
		self.label = Tkinter.Label( preferencesDialog.root, text = self.name )
		self.label.grid( row = preferencesDialog.row, column = 0, columnspan = 3, sticky = Tkinter.W )
		preferencesDialog.row += 1

	def addToPreferenceTable( self, preferenceTable ):
		"Do nothing because the label display is not archivable."
		pass

	def getFromName( self, name ):
		"Initialize."
		self.name = name
		return self

	def getName( self ):
		"Get name for key sorting."
		return self.name

	def setToDisplay( self ):
		"Do nothing because the label display is not archivable."
		pass

	def writeToArchiveWriter( self, archiveWriter ):
		"Do nothing because the label display is not archivable."
		pass


class ListPreference( StringPreference ):
	def addToDialog( self, preferencesDialog ):
		"Do nothing because the list preference does not have a graphical interface."
		pass

	def setToDisplay( self ):
		"Do nothing because the list preference does not have a graphical interface."
		pass

	def setValueToSplitLine( self, lineIndex, lines, splitLine ):
		"Set the value to the second and later words of a split line."
		self.value = splitLine[ 1 : ]

	def setValueToString( self, valueString ):
		"Do nothing because the list preference does not have a graphical interface."
		pass

	def writeToArchiveWriter( self, archiveWriter ):
		"Write tab separated name and list to the archive writer."
		archiveWriter.write( self.name + globalSpreadsheetSeparator )
		for item in self.value:
			archiveWriter.write( item )
			if item != self.value[ - 1 ]:
				archiveWriter.write( globalSpreadsheetSeparator )
		archiveWriter.write( '\n' )


class MenuButtonDisplay:
	"A class to add a menu button."
	def addToDialog( self, preferencesDialog ):
		"Do nothing because this will be added to the dialog with getMenuButton."
		self.menuButton = None
		self.preferencesDialog = preferencesDialog

	def addToPreferenceTable( self, preferenceTable ):
		"Do nothing because the label display is not archivable."
		pass

	def getFromName( self, name ):
		"Initialize."
		self.name = name
		return self

	def getMenuButton( self, name ):
		"Get the menu button."
		if self.menuButton != None:
			return self.menuButton
		self.optionList = [ name ]
		self.radioVar = Tkinter.StringVar()
		self.radioVar.set( self.optionList[ 0 ] )
		self.label = Tkinter.Label( self.preferencesDialog.root, text = self.name )
		self.label.grid( row = self.preferencesDialog.row, column = 0, columnspan = 3, sticky = Tkinter.W )
		self.menuButton = Tkinter.OptionMenu( self.preferencesDialog.root, self.radioVar, self.optionList )
		self.menuButton.grid( row = self.preferencesDialog.row, column = 3, columnspan = 2, sticky = Tkinter.W )
		self.menuButton.menu = Tkinter.Menu( self.menuButton, tearoff = 0 )
		self.menuButton[ 'menu' ]  =  self.menuButton.menu
		self.preferencesDialog.row += 1
		return self.menuButton

	def getName( self ):
		"Get name for key sorting."
		return self.name

	def setToDisplay( self ):
		"Do nothing because the label display is not archivable."
		pass

	def setUpdateFunction( self, updateFunction ):
		"Do nothing because the menu button display does not have a value."
		pass

	def writeToArchiveWriter( self, archiveWriter ):
		"Do nothing because the label display is not archivable."
		pass


class MenuRadio( BooleanPreference ):
	"A class to display, read & write a boolean with associated menu radio button."
	def addToDialog( self, preferencesDialog ):
		"Add this to the dialog."
		self.menuButtonDisplay.getMenuButton( self.name ).menu.add_radiobutton( label = self.name, command = self.clickRadio, value = self.name, variable = self.menuButtonDisplay.radioVar )
		self.menuLength = self.menuButtonDisplay.menuButton.menu.index( Tkinter.END )
		self.setDisplayState()

	def clickRadio( self ):
		"Workaround for Tkinter bug, invoke and set the value when clicked."
		if self.menuButtonDisplay.radioVar.get() == self.name:
			return
		self.invokeSetString()
		if self.updateFunction != None:
			self.updateFunction()

	def getFromMenuButtonDisplay( self, menuButtonDisplay, name, value ):
		"Initialize."
		self.getFromValue( name, value )
		self.menuButtonDisplay = menuButtonDisplay
		return self

	def invokeSetString( self ):
		"Workaround for Tkinter bug, invoke and set the value."
		self.menuButtonDisplay.radioVar.set( self.name )
		self.menuButtonDisplay.menuButton.menu.invoke( self.menuLength )

	def setToDisplay( self ):
		"Set the boolean to the checkbox."
		self.value = ( self.menuButtonDisplay.radioVar.get() == self.name )

	def setDisplayState( self ):
		"Set the checkbox to the boolean."
		if self.value:
			self.invokeSetString()


class ProfileList:
	"A class to list the profiles."
	def __init__( self ):
		"Set the update function to none."
		self.updateFunction = None

	def addToDialog( self, preferencesDialog ):
		"Do nothing because the profile list does not have a graphical interface."
		pass

	def addToPreferenceTable( self, preferenceTable ):
		"Do nothing because the profile list is not archivable."
		pass

	def getFromName( self, craftTypeName, name ):
		"Initialize."
		self.craftTypeName = craftTypeName
		self.name = name
		self.setValueToFolders()
		return self

	def getName( self ):
		"Get name for key sorting."
		return self.name

	def setToDisplay( self ):
		"Do nothing because the profile list is not archivable."
		pass

	def setValueToFolders( self ):
		"Set the value to the folders in the profiles directories."
		self.value = getFolders( getProfilesDirectoryPath( self.craftTypeName ) )
		defaultFolders = getFolders( getProfilesDirectoryInAboveDirectory( self.craftTypeName ) )
		for defaultFolder in defaultFolders:
			if defaultFolder not in self.value:
				self.value.append( defaultFolder )
		self.value.sort()

	def writeToArchiveWriter( self, archiveWriter ):
		"Do nothing because the profile list is not archivable."
		pass


class ProfileListboxPreference( StringPreference ):
	def addToDialog( self, preferencesDialog ):
		"Add this to the dialog."
#http://www.pythonware.com/library/tkinter/introduction/x5453-patterns.htm
		self.root = preferencesDialog.root
		frame = Tkinter.Frame( preferencesDialog.root )
		scrollbar = Tkinter.Scrollbar( frame, orient = Tkinter.VERTICAL )
		self.listbox = Tkinter.Listbox( frame, selectmode = Tkinter.SINGLE, yscrollcommand = scrollbar.set )
		self.listbox.bind( '<ButtonRelease-1>', self.buttonReleaseOne )
		preferencesDialog.root.bind( '<FocusIn>', self.focusIn )
		scrollbar.config( command = self.listbox.yview )
		scrollbar.pack( side = Tkinter.RIGHT, fill = Tkinter.Y )
		self.listbox.pack( side = Tkinter.LEFT, fill = Tkinter.BOTH, expand = 1 )
		self.setListboxItems()
		frame.grid( row = preferencesDialog.row, columnspan = 5, sticky = Tkinter.W )
		preferencesDialog.row += 1
		preferencesDialog.saveListenerTable[ 'updateProfileSaveListeners' ] = updateProfileSaveListeners

	def buttonReleaseOne( self, event ):
		"Button one released."
		self.setValueToIndex( self.listbox.nearest( event.y ) )

	def focusIn( self, event ):
		"The root has gained focus."
		self.setListboxItems()

	def getFromListPreference( self, listPreference, name, value ):
		"Initialize."
		self.getFromValue( name, value )
		self.defaultValue = value
		self.listPreference = listPreference
		return self

	def getSelectedFolder( self ):
		"Get the selected folder."
		preferenceProfileSubfolder = getSubfolderWithBasename( self.value, getProfilesDirectoryPath( self.listPreference.craftTypeName ) )
		if preferenceProfileSubfolder != None:
			return preferenceProfileSubfolder
		toolProfileSubfolder = getSubfolderWithBasename( self.value, getProfilesDirectoryInAboveDirectory( self.listPreference.craftTypeName ) )
		return toolProfileSubfolder

	def setListboxItems( self ):
		"Set the listbox items to the list preference."
		self.listbox.delete( 0, Tkinter.END )
		for item in self.listPreference.value:
			self.listbox.insert( Tkinter.END, item )
			if self.value == item:
				self.listbox.select_set( Tkinter.END )

	def setToDisplay( self ):
		"Set the selection value to the listbox selection."
		currentSelectionTuple = self.listbox.curselection()
		if len( currentSelectionTuple ) > 0:
			self.setValueToIndex( int( currentSelectionTuple[ 0 ] ) )

	def setValueToIndex( self, index ):
		"Set the selection value to the index."
		valueString = self.listbox.get( index )
		self.setValueToString( valueString )

	def setValueToString( self, valueString ):
		"Set the string to the value string."
		self.value = valueString
		if self.getSelectedFolder() == None:
			self.value = self.defaultValue
		if self.getSelectedFolder() == None:
			if len( self.listPreference.value ) > 0:
				self.value = self.listPreference.value[ 0 ]


class ProfileMenuRadio():
	"A class to display a profile menu radio button."
	def __init__( self, profilePluginFilename, menu, name, radioVar, value ):
		"Create a profile menu radio."
		self.activate = False
		self.menu = menu
		self.name = name
		self.profileJoinName = profilePluginFilename + '.& /' + name
		self.profilePluginFilename = profilePluginFilename
		self.radioVar = radioVar
		if value:
			self.radioVar.set( self.profileJoinName )
		menu.add_radiobutton( label = name, command = self.clickRadio, value = self.profileJoinName, variable = self.radioVar )
		self.menuLength = menu.index( Tkinter.END )
		if value:
			self.invokeSetString()
		self.activate = True

	def clickRadio( self ):
		"Workaround for Tkinter bug, invoke and set the value when clicked."
		if self.radioVar.get() != self.profileJoinName:
			self.radioVar.set( self.profileJoinName )
		if not self.activate:
			return
		pluginModule = getCraftTypePluginModule( self.profilePluginFilename )
		profilePluginPreferences = getReadPreferences( pluginModule.getPreferencesConstructor() )
		profilePluginPreferences.profileListbox.value = self.name
		writePreferences( profilePluginPreferences )
		profilePreferences = getReadProfilePreferences()
		plugins = profilePreferences.craftRadios
		for plugin in plugins:
			plugin.value = ( plugin.name == self.profilePluginFilename )
		writePreferences( profilePreferences )
		updateProfileSaveListeners()

	def invokeSetString( self ):
		"Workaround for Tkinter bug, invoke and set the value."
		self.radioVar.set( self.profileJoinName )
		self.menu.invoke( self.menuLength )


class Radio( BooleanPreference ):
	"A class to display, read & write a boolean with associated radio button."
	def addToDialog( self, preferencesDialog ):
		"Add this to the dialog."
		self.radiobutton = Tkinter.Radiobutton( preferencesDialog.root, command = self.clickRadio, text = self.name, value = preferencesDialog.row, variable = self.getIntVar() )
		self.radiobutton.grid( row = preferencesDialog.row, column = 0, columnspan = 3, sticky = Tkinter.W )
		self.setDisplayState( preferencesDialog.row )
		preferencesDialog.row += 1

	def clickRadio( self ):
		"Workaround for Tkinter bug, set the value."
		self.getIntVar().set( self.radiobutton[ 'value' ] )

	def getFromRadio( self, name, radio, value ):
		"Initialize."
		self.getFromValue( name, value )
		self.radio = radio
		return self

	def getIntVar( self ):
		"Get the IntVar for this radio button group."
		if len( self.radio ) == 0:
			self.radio.append( Tkinter.IntVar() )
		return self.radio[ 0 ]

	def setToDisplay( self ):
		"Set the boolean to the checkbox."
		self.value = ( self.getIntVar().get() == self.radiobutton[ 'value' ] )

	def setDisplayState( self, row ):
		"Set the checkbox to the boolean."
		if self.value:
			self.getIntVar().set( self.radiobutton[ 'value' ] )
			self.radiobutton.select()


class RadioCapitalized( Radio ):
	"A class to display, read & write a boolean with associated radio button."
	def addToDialog( self, preferencesDialog ):
		"Add this to the dialog."
		capitalizedName = getEachWordCapitalized( self.name )
		self.radiobutton = Tkinter.Radiobutton( preferencesDialog.root, command = self.clickRadio, text = capitalizedName, value = preferencesDialog.row, variable = self.getIntVar() )
		self.radiobutton.grid( row = preferencesDialog.row, column = 0, columnspan = 3, sticky = Tkinter.W )
		self.setDisplayState( preferencesDialog.row )
		preferencesDialog.row += 1

	def getLowerName( self ):
		"Get the lower case name."
		return self.name.lower()


class TextPreference( StringPreference ):
	"A class to display, read & write a text."
	def __init__( self ):
		"Set the update function to none."
		self.tokenConversions = [
			TokenConversion(),
			TokenConversion( 'carriageReturn', '\r' ),
			TokenConversion( 'doubleQuote', '"' ),
			TokenConversion( 'newline', '\n' ),
			TokenConversion( 'semicolon', ';' ),
			TokenConversion( 'singleQuote', "'" ),
			TokenConversion( 'tab', '\t' ) ]
		self.updateFunction = None

	def addToDialog( self, preferencesDialog ):
		"Add this to the dialog."
		self.label = Tkinter.Label( preferencesDialog.root, text = self.name )
		self.label.grid( row = preferencesDialog.row, column = 0, columnspan = 3, sticky = Tkinter.W )
		preferencesDialog.row += 1
		self.entry = Tkinter.Text( preferencesDialog.root )
		self.setStateToValue()
		self.entry.grid( row = preferencesDialog.row, column = 0, columnspan = 5, sticky = Tkinter.W )
		preferencesDialog.row += 1

	def setToDisplay( self ):
		"Set the string to the entry field."
		valueString = self.entry.get( 1.0, Tkinter.END )
		self.setValueToString( valueString )

	def setStateToValue( self ):
		"Set the entry to the value."
		try:
			self.entry.delete( 1.0, Tkinter.END )
			self.entry.insert( Tkinter.INSERT, self.value )
		except:
			pass

	def setValueToSplitLine( self, lineIndex, lines, splitLine ):
		"Set the value to the second word of a split line."
		replacedValue = splitLine[ 1 ]
		for tokenConversion in reversed( self.tokenConversions ):
			replacedValue = tokenConversion.getTokenizedString( replacedValue )
		self.setValueToString( replacedValue )

	def writeToArchiveWriter( self, archiveWriter ):
		"Write tab separated name and value to the archive writer."
		replacedValue = self.value
		for tokenConversion in self.tokenConversions:
			replacedValue = tokenConversion.getNamedString( replacedValue )
		archiveWriter.write( '%s%s%s\n' % ( self.name, globalSpreadsheetSeparator, replacedValue ) )


class TokenConversion:
	"A class to convert tokens in a string."
	def __init__( self, name = 'replaceToken', token = '___replaced___' ):
		"Set the name and token."
		self.replacedName = '___replaced___' + name
		self.token = token

	def getNamedString( self, text ):
		"Get a string with the tokens changed to names."
		return text.replace( self.token, self.replacedName )

	def getTokenizedString( self, text ):
		"Get a string with the names changed to tokens."
		return text.replace( self.replacedName, self.token )


class ToolDialog:
	"A class to display the tool preferences dialog."
	def addPluginToMenu( self, filePath, menu, name ):
		"Add the display command to the menu."
		self.getDisplayFromFolderPath( filePath, name )
		menu.add_command( label = name.capitalize(), command = self.display )

	def display( self ):
		"Display the tool preferences dialog."
		global globalPreferencesDialogTable
		if self.name.lower() in globalPreferencesDialogTable:
			toolPreferencesDialog = globalPreferencesDialogTable[ self.name.lower() ]
			toolPreferencesDialog.root.withdraw() # the withdraw & deiconify trick is here because lift does not work properly on my linux computer
			toolPreferencesDialog.root.lift() # probably not necessary, here in case the withdraw & deiconify trick does not work on some other computer
			toolPreferencesDialog.root.deiconify()
			toolPreferencesDialog.root.lift() # probably not necessary, here in case the withdraw & deiconify trick does not work on some other computer
			toolPreferencesDialog.root.update_idletasks()
			return
		pluginModule = gcodec.getModuleWithPath( self.name, self.filePath )
		if pluginModule != None:
			getDisplayedDialogFromConstructor( pluginModule.getPreferencesConstructor() )

	def getDisplayFromFolderPath( self, filePath, name ):
		"Initialize and return display function."
		self.filePath = filePath
		self.name = name
		return self.display


class WindowPosition( StringPreference ):
	"A class to display, read & write a window position."
	def addToDialog( self, preferencesDialog ):
		"Set the root to later get the geometry."
		self.root = preferencesDialog.root
		self.windowPositionName = 'windowPosition' + preferencesDialog.displayPreferences.title
#		self.setToDisplay()

	def setToDisplay( self ):
		"Set the string to the window position."
		if self.name != self.windowPositionName:
			return
		try:
			geometryString = self.root.geometry()
		except:
			return
		if geometryString == '1x1+0+0':
			return
		firstPlusIndexPlusOne = geometryString.find( '+' ) + 1
		self.value = geometryString[ firstPlusIndexPlusOne : ]

	def setWindowPosition( self ):
		"Set the window position."
		movedGeometryString = '%sx%s+%s' % ( self.root.winfo_reqwidth(), self.root.winfo_reqheight(), self.value )
		self.root.geometry( movedGeometryString )


class PreferencesDialog:
	def __init__( self, displayPreferences, root ):
		"Add display preferences to the dialog."
		self.closeListener = CloseListener( displayPreferences.lowerName, self )
		self.displayPreferences = displayPreferences
		self.displayToolButtonStart = True
		self.executables = []
		self.isFirst = ( len( globalPreferencesDialogTable.keys() ) == 0 )
		self.root = root
		self.openDialogListeners = []
		self.openHelpPage = HelpPage().getOpenFromDocumentationSubName( self.displayPreferences.fileNameHelp )
		self.row = 0
		self.saveListenerTable = {}
		displayPreferences.preferencesDialog = self
		root.title( displayPreferences.title )
		fileHelpMenuBar = FileHelpMenuBar( root )
		fileHelpMenuBar.fileMenu.add_command( label = "Save", command = self.save )
		fileHelpMenuBar.fileMenu.add_command( label = "Save and Close", command = self.saveClose )
		fileHelpMenuBar.helpMenu.add_command( label = displayPreferences.capitalizedName, command = self.openHelpPage )
		fileHelpMenuBar.completeMenu( self.close, displayPreferences.lowerName )
		if len( displayPreferences.archive ) > 25:
			self.addButtons( displayPreferences, root )
		for preference in displayPreferences.archive:
			preference.addToDialog( self )
		if self.row < 20:
			self.addEmptyRow()
		self.addButtons( displayPreferences, root )
		root.withdraw()
		root.update_idletasks()
		self.setWindowPositionDeiconify()
		root.deiconify()
		for openDialogListener in self.openDialogListeners:
			openDialogListener.openDialog()

	def addButtons( self, displayPreferences, root ):
		"Add buttons to the dialog."
		columnIndex = 0
		cancelTitle = 'Close'
		if displayPreferences.saveCloseTitle != None:
			cancelTitle = 'Cancel'
		if displayPreferences.executeTitle != None:
			executeButton = Tkinter.Button( root, activebackground = 'black', activeforeground = 'blue', text = displayPreferences.executeTitle, command = self.execute )
			executeButton.grid( row = self.row, column = columnIndex )
			columnIndex += 1
		self.helpButton = Tkinter.Button( root, activebackground = 'black', activeforeground = 'white', text = "?", command = self.openHelpPage )
		self.helpButton.grid( row = self.row, column = columnIndex )
		self.closeListener.listenToWidget( self.helpButton )
		columnIndex += 1
		cancelButton = Tkinter.Button( root, activebackground = 'black', activeforeground = 'red', command = self.close, fg = 'red', text = cancelTitle )
		cancelButton.grid( row = self.row, column = columnIndex )
		columnIndex += 1
		if displayPreferences.saveCloseTitle != None:
			saveCloseButton = Tkinter.Button( root, activebackground = 'black', activeforeground = 'orange', command = self.saveClose, fg = 'orange', text = displayPreferences.saveCloseTitle )
			saveCloseButton.grid( row = self.row, column = columnIndex )
			columnIndex += 1
		self.saveButton = Tkinter.Button( root, activebackground = 'black', activeforeground = 'darkgreen', command = self.save, fg = 'darkgreen', text = 'Save' )
		self.saveButton.grid( row = self.row, column = columnIndex )
		self.row += 1

	def addEmptyRow( self ):
		"Add an empty row."
		Tkinter.Label( self.root ).grid( row = self.row )
		self.row += 1

	def close( self ):
		"The dialog was closed."
		global globalPreferencesDialogTable
		if self.isFirst and len( globalPreferencesDialogTable.keys() ) > 1:
			self.root.iconify()
			print( 'The first window, %s, has been iconified.' % self.displayPreferences.title )
			return
		try:
			self.root.destroy()
		except:
			pass

	def closeIfNotFirstAndOnly( self ):
		"The dialog was closed."
		global globalPreferencesDialogTable
		if self.isFirst and len( globalPreferencesDialogTable.keys() ) > 1:
			self.root.withdraw()
		else:
			self.root.destroy()

	def execute( self ):
		"The execute button was clicked."
		for executable in self.executables:
			executable.execute()
		self.save()
		self.displayPreferences.execute()
		self.close()

	def save( self ):
		"Set the preferences to the dialog then write them."
		for preference in self.displayPreferences.archive:
			preference.setToDisplay()
		writePreferences( self.displayPreferences )
		for saveListener in self.saveListenerTable.values():
			saveListener()
		print( self.displayPreferences.title.lower().capitalize() + ' have been saved.' )

	def saveClose( self ):
		"Set the preferences to the dialog, write them, then destroy the window."
		self.save()
		self.close()

	def setWindowPositionDeiconify( self ):
		"Set the window position if that preference exists."
		windowPositionName = 'windowPosition' + self.displayPreferences.title
		for preference in self.displayPreferences.archive:
			if isinstance( preference, WindowPosition ):
				if preference.name == windowPositionName:
					preference.setWindowPosition()
					return


class ProfilePreferences:
	"A class to handle the profile preferences."
	def __init__( self ):
		"Set the default preferences, execute title & preferences fileName."
		#Set the default preferences.
		profilePluginsDirectoryPath = gcodec.getAbsoluteFolderPath( os.path.dirname( __file__ ), 'profile_plugins' )
		self.archive = []
		self.craftTypeLabel = LabelDisplay().getFromName( 'Craft Types: ' )
		self.archive.append( self.craftTypeLabel )
		craftTypeFilenames = gcodec.getPluginFilenamesFromDirectoryPath( profilePluginsDirectoryPath )
		craftTypeRadio = []
		self.craftRadios = []
		for craftTypeFilename in craftTypeFilenames:
			craftRadio = RadioCapitalized().getFromRadio( craftTypeFilename, craftTypeRadio, craftTypeFilename == 'extrusion' )
			self.craftRadios.append( craftRadio )
		self.craftRadios.sort( key = RadioCapitalized.getLowerName )
		for craftRadio in self.craftRadios:
			self.archive.append( craftRadio )
			self.archive.append( DisplayProfileButton().getFromFolderPath( profilePluginsDirectoryPath, False, craftRadio.name, craftRadio.getLowerName() == 'extrusion' ) )
		#Create the archive, title of the dialog & preferences fileName.
		self.executeTitle = None
		self.saveCloseTitle = 'Save and Close'
		directoryName = getProfilesDirectoryPath()
		makeDirectory( directoryName )
		self.baseName = getLowerNameSetHelpTitleWindowPosition( self, 'skeinforge_tools.profile.html' )
		self.windowPositionPreferences.value = '0+200'

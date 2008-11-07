"""
Preferences is a collection of utilities to display, read & write preferences.

"""

from __future__ import absolute_import
#Init has to be imported first because it has code to workaround the python bug where relative imports don't work if the module is imported as a main module.
import __init__

import cStringIO
from skeinforge_tools.skeinforge_utilities import gcodec
import os
import webbrowser
try:
	import Tkinter
except:
	print( 'You do not have Tkinter, which is needed for the graphical interface, you will only be able to use the command line.' )
	print( 'Information on how to download Tkinter is at:\nwww.tcl.tk/software/tcltk/' )


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/23/04 $"
__license__ = "GPL 3.0"

globalIsMainLoopRunning = False
globalSpreadsheetSeparator = '\t'

def displayDialog( displayPreferences ):
	"Display the preferences dialog."
	readPreferences( displayPreferences )
	root = Tkinter.Tk()
	preferencesDialog = PreferencesDialog( displayPreferences, root )
	global globalIsMainLoopRunning
#	print( globalIsMainLoopRunning )
	if globalIsMainLoopRunning:
		return
	globalIsMainLoopRunning = True
	root.mainloop()
	globalIsMainLoopRunning = False

def getArchiveText( preferences ):
	"Get the text representation of the archive."
	archiveWriter = cStringIO.StringIO()
	archiveWriter.write( 'Format is tab separated preferences.\n' )
	for preference in preferences.archive:
		preference.writeToArchiveWriter( archiveWriter )
	return archiveWriter.getvalue()

def getPreferencesDirectoryPath():
	"Get the preferences directory path, which is the home directory joined with .skeinforge."
	return os.path.join( os.path.expanduser( '~' ), '.skeinforge' )

def getPreferencesFilePath( filename ):
	"Get the preferences file path, which is the home directory joined with .skeinforge and filename."
	directoryName = getPreferencesDirectoryPath()
	try:
		os.mkdir( directoryName )
	except OSError:
		pass
	return os.path.join( directoryName, filename )

def readPreferences( preferences ):
	"Set an archive to the preferences read from a file."
	text = gcodec.getFileText( preferences.filenamePreferences )
	if text == '':
		print( 'Since the preferences file:' )
		print( preferences.filenamePreferences )
		print( 'does not exist, the default preferences will be written to that file.' )
		text = gcodec.getFileText( os.path.join( 'defaults', os.path.basename( preferences.filenamePreferences ) ) )
		if text != '':
			readPreferencesFromText( preferences, text )
		writePreferences( preferences )
		return
	readPreferencesFromText( preferences, text )

def readPreferencesFromText( preferences, text ):
	"Set an archive to the preferences read from a text."
	lines = gcodec.getTextLines( text )
	preferenceTable = {}
	for preference in preferences.archive:
		preference.addToPreferenceTable( preferenceTable )
	for lineIndex in range( len( lines ) ):
		setArchiveToLine( lineIndex, lines, preferenceTable )

def setArchiveToLine( lineIndex, lines, preferenceTable ):
	"Set an archive to a preference line."
	line = lines[ lineIndex ]
	splitLine = line.split( globalSpreadsheetSeparator )
	if len( splitLine ) < 2:
		return
	filePreferenceName = splitLine[ 0 ]
	if filePreferenceName in preferenceTable:
		preferenceTable[ filePreferenceName ].setValueToSplitLine( lineIndex, lines, splitLine )

def writePreferences( preferences ):
	"Write the preferences to a file."
	gcodec.writeFileText( preferences.filenamePreferences, getArchiveText( preferences ) )


class AddListboxSelection:
	"A class to add the selection of a listbox preference."
	def addToDialog( self, preferencesDialog ):
		"Add this to the dialog."
		self.entry = Tkinter.Entry( preferencesDialog.master )
		self.entry.bind( '<Return>', self.addSelectionWithEvent )
		self.entry.grid( row = preferencesDialog.row, column = 1, columnspan = 2, sticky = Tkinter.W )
		self.addButton = Tkinter.Button( preferencesDialog.master, text = 'Add Listbox Selection', command = self.addSelection )
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
		self.listboxPreference.listbox.delete( 0, Tkinter.END )
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


class BooleanPreference:
	"A class to display, read & write a boolean."
	def addToDialog( self, preferencesDialog ):
		"Add this to the dialog."
		self.checkbutton = Tkinter.Checkbutton( preferencesDialog.master, command = self.toggleCheckbox, text = self.name )
#toggleCheckbox is being used instead of a Tkinter IntVar because there is a weird bug where it doesn't work properly if this preference is not on the first window.
		self.checkbutton.grid( row = preferencesDialog.row, columnspan = 4, sticky = Tkinter.W )
		self.setStateToValue()
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
		"Set the checkbox to the boolean."
		if self.value:
			self.checkbutton.select()
		else:
			self.checkbutton.deselect()

	def setToDisplay( self ):
		"Do nothing because toggleCheckbox is handling the value."
		pass

	def setValueToSplitLine( self, lineIndex, lines, splitLine ):
		"Set the value to the second word of a split line."
		self.setValueToString( splitLine[ 1 ] )

	def setValueToString( self, valueString ):
		"Set the boolean to the string."
		self.value = ( valueString.lower() == 'true' )

	def toggleCheckbox( self ):
		"Workaround for Tkinter bug, toggle the value."
		self.value = not self.value
		self.setStateToValue()

	def writeToArchiveWriter( self, archiveWriter ):
		"Write tab separated name and value to the archive writer."
		archiveWriter.write( self.name + globalSpreadsheetSeparator + str( self.value ) + '\n' )


class DeleteListboxSelection( AddListboxSelection ):
	"A class to delete the selection of a listbox preference."
	def addToDialog( self, preferencesDialog ):
		"Add this to the dialog."
		self.deleteButton = Tkinter.Button( preferencesDialog.master, text = "Delete Listbox Selection", command = self.deleteSelection )
		self.deleteButton.grid( row = preferencesDialog.row, column = 0 )
		preferencesDialog.row += 1

	def deleteSelection( self ):
		"Delete the selection of a listbox preference."
		self.listboxPreference.setToDisplay()
		if self.listboxPreference.value not in self.listboxPreference.listPreference.value:
			return
		self.listboxPreference.listPreference.value.remove( self.listboxPreference.value )
		self.listboxPreference.listbox.delete( 0, Tkinter.END )
		self.listboxPreference.setListboxItems()
		self.listboxPreference.listbox.select_set( 0 )
		self.listboxPreference.setToDisplay()


class DisplayToolButton:
	"A class to display the tool preferences dialog."
	def addToDialog( self, preferencesDialog ):
		"Add this to the dialog."
		withSpaces = self.name.lower().replace( '_', ' ' )
		words = withSpaces.split( ' ' )
		capitalizedStrings = []
		for word in words:
			capitalizedStrings.append( word.capitalize() )
		capitalizedName = ' '.join( capitalizedStrings )
		self.displayButton = Tkinter.Button( preferencesDialog.master, text = capitalizedName, command = self.displayTool )
		self.displayButton.grid( row = preferencesDialog.row, column = 0 )
		preferencesDialog.row += 1

	def addToPreferenceTable( self, preferenceTable ):
		"Do nothing because the add listbox selection is not archivable."
		pass

	def displayTool( self ):
		"Display the tool preferences dialog."
		pluginModule = gcodec.getModule( self.name, self.folderName, self.moduleFilename )
		if pluginModule != None:
			pluginModule.main()

	def getFromFolderName( self, folderName, moduleFilename, name ):
		"Initialize."
		self.folderName = folderName
		self.moduleFilename = moduleFilename
		self.name = name
		return self

	def getLowerName( self ):
		"Get the lower case name."
		return self.name.lower()

	def setToDisplay( self ):
		"Do nothing because the display tool button is not archivable."
		pass

	def writeToArchiveWriter( self, archiveWriter ):
		"Do nothing because the display tool button is not archivable."
		pass


class DisplayToolButtonBesidePrevious( DisplayToolButton ):
	"A class to display the tool preferences dialog beside the previous preference dialog element."
	def addToDialog( self, preferencesDialog ):
		"Add this to the dialog."
		withSpaces = self.name.lower().replace( '_', ' ' )
		words = withSpaces.split( ' ' )
		capitalizedStrings = []
		for word in words:
			capitalizedStrings.append( word.capitalize() )
		capitalizedName = ' '.join( capitalizedStrings )
		self.displayButton = Tkinter.Button( preferencesDialog.master, text = capitalizedName, command = self.displayTool )
		self.displayButton.grid( row = preferencesDialog.row - 1, column = 2, columnspan = 2 )


class Filename( BooleanPreference ):
	def addToDialog( self, preferencesDialog ):
		"Add this to the dialog."
		preferencesDialog.executables.append( self )

	"A class to display, read & write a filename."
	def execute( self ):
		try:
			import tkFileDialog
			summarized = gcodec.getSummarizedFilename( self.value )
			initialDirectory = os.path.dirname( summarized )
			if len( initialDirectory ) > 0:
				initialDirectory += os.sep
			else:
				initialDirectory = "."
			filename = tkFileDialog.askopenfilename( filetypes = self.getFilenameFirstTypes(), initialdir = initialDirectory, initialfile = os.path.basename( summarized ), title = self.name )
			if ( str( filename ) == '()' ):
				self.wasCancelled = True
			else:
				self.value = filename
		except:
			print( 'Oops, ' + self.name + ' could not get filename.' )

	def getFromFilename( self, fileTypes, name, value ):
		"Initialize."
		self.getFromValue( name, value )
		self.fileTypes = fileTypes
		self.wasCancelled = False
		return self

	def getFilenameFirstTypes( self ):
		"Get the file types with the file type of the filename moved to the front of the list."
		basename = os.path.basename( self.value )
		splitFile = basename.split( '.' )
		allReadables = []
		for fileType in self.fileTypes:
			allReadable = ( ( 'All Readable', fileType[ 1 ] ) )
			allReadables.append( allReadable )
		if len( splitFile ) < 1:
			return self.fileTypes + allReadables
		baseExtension = splitFile[ - 1 ]
		for fileType in self.fileTypes:
			fileExtension = fileType[ 1 ].split( '.' )[ - 1 ]
			if fileExtension == baseExtension:
				filenameFirstTypes = self.fileTypes[ : ]
				filenameFirstTypes.remove( fileType )
				return [ fileType ] + filenameFirstTypes
		return self.fileTypes + allReadables

	def setToDisplay( self ):
		"Pass."
		pass

	def setValueToString( self, valueString ):
		"Set the filename to the string."
		self.value = valueString


class FloatPreference( BooleanPreference ):
	"A class to display, read & write a float."
	def addToDialog( self, preferencesDialog ):
		"Add this to the dialog."
		self.entry = Tkinter.Entry( preferencesDialog.master )
		self.entry.insert( 0, str( self.value ) )
		self.entry.grid( row = preferencesDialog.row, column = 2, columnspan = 2, sticky = Tkinter.W )
		self.label = Tkinter.Label( preferencesDialog.master, text = self.name )
		self.label.grid( row = preferencesDialog.row, column = 0, columnspan = 2, sticky = Tkinter.W )
		preferencesDialog.row += 1

	def setToDisplay( self ):
		"Set the float to the entry field."
		valueString = self.entry.get()
		self.setValueToString( valueString )

	def setValueToString( self, valueString ):
		"Set the float to the string."
		try:
			self.value = float( valueString )
		except:
			print( 'Oops, can not read float' + self.name + ' ' + valueString )


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
		self.label = Tkinter.Label( preferencesDialog.master, text = self.name )
		self.label.grid( row = preferencesDialog.row, column = 0, columnspan = 2, sticky = Tkinter.W )
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


class ListPreference( BooleanPreference ):
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


class ListboxPreference( BooleanPreference ):
	def addToDialog( self, preferencesDialog ):
		"Add this to the dialog."
#http://www.pythonware.com/library/tkinter/introduction/x5453-patterns.htm
		frame = Tkinter.Frame( preferencesDialog.master )
		scrollbar = Tkinter.Scrollbar( frame, orient = Tkinter.VERTICAL )
		self.listbox = Tkinter.Listbox( frame, selectmode = Tkinter.SINGLE, yscrollcommand = scrollbar.set )
		scrollbar.config( command = self.listbox.yview )
		scrollbar.pack( side = Tkinter.RIGHT, fill = Tkinter.Y )
		self.listbox.pack( side = Tkinter.LEFT, fill = Tkinter.BOTH, expand = 1 )
		self.setListboxItems()
		frame.grid( row = preferencesDialog.row, columnspan = 4, sticky = Tkinter.W )
		preferencesDialog.row += 1

	def getFromListPreference( self, listPreference, name, value ):
		"Initialize."
		self.getFromValue( name, value )
		self.listPreference = listPreference
		return self

	def setListboxItems( self ):
		"Set the listbox items to the list preference."
		for item in self.listPreference.value:
			self.listbox.insert( Tkinter.END, item )
			if self.value == item:
				self.listbox.select_set( Tkinter.END )

	def setToDisplay( self ):
		"Set the selection value to the listbox selection."
		valueString = self.listbox.get( Tkinter.ACTIVE )
		self.setValueToString( valueString )

	def setValueToString( self, valueString ):
		"Set the selection value to the string."
		self.value = valueString


class Radio( BooleanPreference ):
	"A class to display, read & write a boolean with associated radio button."
	def addToDialog( self, preferencesDialog ):
		"Add this to the dialog."
		self.radiobutton = Tkinter.Radiobutton( preferencesDialog.master, command = self.clickRadio, text = self.name, value = preferencesDialog.row, variable = self.getIntVar() )
		self.radiobutton.grid( row = preferencesDialog.row, column = 0, columnspan = 2, sticky = Tkinter.W )
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
		"Set the boolean to the checkbox."
		if self.value:
			self.getIntVar().set( self.radiobutton[ 'value' ] )
			self.radiobutton.select()


class RadioCapitalized( Radio ):
	"A class to display, read & write a boolean with associated radio button."
	def addToDialog( self, preferencesDialog ):
		"Add this to the dialog."
		withSpaces = self.name.lower().replace( '_', ' ' )
		words = withSpaces.split( ' ' )
		capitalizedStrings = []
		for word in words:
			capitalizedStrings.append( word.capitalize() )
		capitalizedName = ' '.join( capitalizedStrings )
		self.radiobutton = Tkinter.Radiobutton( preferencesDialog.master, command = self.clickRadio, text = capitalizedName, value = preferencesDialog.row, variable = self.getIntVar() )
		self.radiobutton.grid( row = preferencesDialog.row, column = 0, columnspan = 2, sticky = Tkinter.W )
		self.setDisplayState( preferencesDialog.row )
		preferencesDialog.row += 1

	def getLowerName( self ):
		"Get the lower case name."
		return self.name.lower()


class StringPreference( BooleanPreference ):
	"A class to display, read & write a string."
	def addToDialog( self, preferencesDialog ):
		"Add this to the dialog."
		self.entry = Tkinter.Entry( preferencesDialog.master )
		self.entry.insert( 0, self.value )
		self.entry.grid( row = preferencesDialog.row, column = 2, columnspan = 2, sticky = Tkinter.W )
		self.label = Tkinter.Label( preferencesDialog.master, text = self.name )
		self.label.grid( row = preferencesDialog.row, column = 0, columnspan = 2, sticky = Tkinter.W )
		preferencesDialog.row += 1

	def setToDisplay( self ):
		"Set the string to the entry field."
		valueString = self.entry.get()
		self.setValueToString( valueString )

	def setValueToString( self, valueString ):
		"Set the string to the value string."
		self.value = valueString


class PreferencesDialog:
	def __init__( self, displayPreferences, master ):
		self.column = 0
		self.displayPreferences = displayPreferences
		self.executables = []
		self.master = master
		self.row = 0
		master.title( displayPreferences.title )
		frame = Tkinter.Frame( master )
		for preference in displayPreferences.archive:
			preference.addToDialog( self )
		Tkinter.Label( master ).grid( row = self.row, column = 0 )
		self.row += 1
		cancelColor = 'black'
		cancelTitle = 'Close'
		if displayPreferences.saveTitle != None:
			saveButton = Tkinter.Button( master, text = displayPreferences.saveTitle, command = self.savePreferencesDestroy )
			saveButton.grid( row = self.row, column = self.column )
			self.column += 1
			cancelColor = 'red'
			cancelTitle = 'Cancel'
		if displayPreferences.executeTitle != None:
			executeButton = Tkinter.Button( master, text = displayPreferences.executeTitle, command = self.execute )
			executeButton.grid( row = self.row, column = self.column )
			self.column += 1
		helpButton = Tkinter.Button( master, text = "       ?       ", command = self.openBrowser )
		helpButton.grid( row = self.row, column = self.column )
		self.column += 1
		cancelButton = Tkinter.Button( master, command = master.destroy, fg = cancelColor, text = cancelTitle )
		cancelButton.grid( row = self.row, column = self.column )

	def execute( self ):
		for executable in self.executables:
			executable.execute()
		self.savePreferences()
		self.displayPreferences.execute()
		self.master.destroy()

	def openBrowser( self ):
		numberOfLevelsDeepInPackageHierarchy = 2
		packageFilePath = os.path.abspath( __file__ )
		for level in range( numberOfLevelsDeepInPackageHierarchy + 1 ):
			packageFilePath = os.path.dirname( packageFilePath )
		documentationPath = os.path.join( os.path.join( packageFilePath, 'documentation' ), self.displayPreferences.filenameHelp )
		os.system( webbrowser.get().name + ' ' + documentationPath )#used this instead of webbrowser.open() to workaround webbrowser open() bug

	def savePreferences( self ):
		for preference in self.displayPreferences.archive:
			preference.setToDisplay()
		writePreferences( self.displayPreferences )

	def savePreferencesDestroy( self ):
		self.savePreferences()
		self.master.destroy()

"""
class Dialog(Toplevel):
    def __init__(self, parent, title = None):
        Toplevel.__init__(self, parent)
        self.transient(parent)
        if title:
            self.title(title)
        self.parent = parent
        self.result = None
        body = Tkinter.Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)
        self.buttonbox()
        self.grab_set()
        if not self.initial_focus:
            self.initial_focus = self
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                  parent.winfo_rooty()+50))
        self.initial_focus.focus_set()
        self.wait_window(self)

    def body(self, master):
        # create dialog body.  return widget that should have
        # initial focus.  this method should be overridden

        pass

    def buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons
        
        box = Tkinter.Frame(self)

        w = Tkinter.Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.pack(side=Tkinter.LEFT, padx=5, pady=5)
        w = Tkinter.Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=Tkinter.LEFT, padx=5, pady=5)

        self.bind("&lt;Return>", self.ok)
        self.bind("&lt;Escape>", self.cancel)

        box.pack()

    #
    # standard button semantics

    def ok(self, event=None):

        if not self.validate():
            self.initial_focus.focus_set() # put focus back
            return

        self.withdraw()
        self.update_idletasks()

        self.apply()

        self.cancel()

    def cancel(self, event=None):

        # put focus back to the parent window
        self.parent.focus_set()
        self.destroy()

    #
    # command hooks

    def validate(self):

        return 1 # override

    def apply(self):

        pass # override

"""
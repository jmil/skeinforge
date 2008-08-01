"""
Polyfile is a script to choose whether the skeinforge toolchain will operate on one file or all the files in a directory.

Polyfile stores and lets the user change the preference of whether to operate on one file or all the files in a directory.  The default
'Polyfile Choice' radio button group choice is 'Execute File'.  With 'Execute File' chosen, the toolchain will operate on only the
chosen file.  When the chosen choice is 'Execute All Unmodified Files in a Directory', the toolchain will operate on all the
unmodifed files in the directory that the chosen file is in.  To use the dialog to change the polyfile
preferences, in a shell type:
> python polyfile.py

Polyfile examples follow below.


> python
Python 2.5.1 (r251:54863, Sep 22 2007, 01:43:31)
[GCC 4.2.1 (SUSE Linux)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import polyfile
>>> polyfile.main()
This brings up the polyfile preference dialog.


>>> polyfile.isDirectoryPreference()
This returns true if 'Execute All Unmodified Files in a Directory' is chosen and returns false if 'Execute File' is chosen.

"""

#Init has to be imported first because it has code to workaround the python bug where relative imports don't work if the module is imported as a main module.
import __init__

from skeinforge_tools.skeinforge_utilities import gcodec
from skeinforge_tools.skeinforge_utilities import preferences


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


def getFileOrGcodeDirectory( filename, wasCancelled ):
	"Get the gcode files in the directory the file is in if directory preference is true.  Otherwise, return the file in a list."
	if isEmptyOrCancelled( filename, wasCancelled ):
		return []
	if isDirectoryPreference():
		return gcodec.getFilesWithFileTypeWithoutWords( 'gcode', [], filename )
	return [ filename ]

def getFileOrUnmodifiedGcodeDirectory( filename, wasCancelled ):
	"Get the gcode files in the directory the file is in if directory preference is true.  Otherwise, return the file in a list."
	if isEmptyOrCancelled( filename, wasCancelled ):
		return []
	if isDirectoryPreference():
		return gcodec.getUnmodifiedGCodeFiles( filename )
	return [ filename ]

def getFileOrGNUUnmodifiedGcodeDirectory( filename, wasCancelled ):
	"Get the gcode files in the directory the file is in if directory preference is true.  Otherwise, return the file in a list."
	if isEmptyOrCancelled( filename, wasCancelled ):
		return []
	if isDirectoryPreference():
		return gcodec.getGNUGcode( filename )
	return [ filename ]

def isDirectoryPreference():
	"Determine if the directory preference is true."
	polyfilePreferences = PolyfilePreferences()
	preferences.readPreferences( polyfilePreferences )
	if polyfilePreferences.directoryPreference.value:
		print( '"Execute All Unmodified Files in a Directory" is selected, so all the unmodified files in the directory will be executed.  To only execute one file, change the preference in polyfile.' )
	else:
		print( '"Execute File" is selected, so only the opened file will be executed.  To execute all the unmodified files in the directory, change the preference in polyfile.' )
	return polyfilePreferences.directoryPreference.value

def isEmptyOrCancelled( filename, wasCancelled ):
	"Determine if the filename is empty or the dialog was cancelled."
	return str( filename ) == '' or str( filename ) == '()' or wasCancelled


class PolyfilePreferences:
	"A class to handle the polyfile preferences."
	def __init__( self ):
		"Set the default preferences, execute title & preferences filename."
		#Set the default preferences.
		directoryRadio = []
		self.directoryPreference = preferences.RadioLabel().getFromRadioLabel( 'Execute All Unmodified Files in a Directory', 'Polyfile Choice:', directoryRadio, False )
		self.filePreference = preferences.Radio().getFromRadio( 'Execute File', directoryRadio, True )
		#Create the archive, title of the dialog & preferences filename.
		self.archive = [ self.directoryPreference, self.filePreference ]
		self.executeTitle = None
		self.filenameHelp = 'skeinforge_tools.polyfile.html'
		self.filenamePreferences = preferences.getPreferencesFilePath( 'polyfile.csv' )
		self.saveTitle = 'Save Preferences'
		self.title = 'Polyfile Preferences'


def main( hashtable = None ):
	"Display the file or directory dialog."
	preferences.displayDialog( PolyfilePreferences() )

if __name__ == "__main__":
	main()

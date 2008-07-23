"""
Multifile is a script to choose whether the skeinforge toolchain will operate on one file or all the files in a directory.

Multifile stores and lets the user change the preference of whether to operate on one file or all the files in a directory.  The default
'Multifile Choice' radio button group choice is 'Execute File'.  With 'Execute File' chosen, the toolchain will operate on only the
chosen file.  When the chosen choice is 'Execute All Unmodified Files in a Directory', the toolchain will operate on all the
unmodifed files in the directory that the chosen file is in.  The preferences can be set in the dialog or by changing the preferences
file 'multifile.csv' with a text editor or a spreadsheet program set to separate tabs.  To use the dialog to change the multifile
preferences, in a shell type:
> python multifile.py

To run multifile, install python 2.x on your machine, which is avaliable from http://www.python.org/download/

To use the preferences dialog you'll also need Tkinter, which probably came with the python installation.  If it did not, look for it at:
www.tcl.tk/software/tcltk/

To write documentation for this program, open a shell in the multifile.py directory, then type 'pydoc -w multifile', then open 'multifile.html' in
a browser or click on the '?' button in the dialog.  To write documentation for all the python scripts in the directory, type 'pydoc -w ./'.
To use other functions of multifile, type 'python' in a shell to run the python interpreter, then type 'import multifile' to import this program.

Multifile example follow below.


> pydoc -w multifile
wrote multifile.html


> python multifile.py
This brings up the multifile preference dialog.


>python
Python 2.5.1 (r251:54863, Sep 22 2007, 01:43:31)
[GCC 4.2.1 (SUSE Linux)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import multifile
>>> multifile.main()
This brings up the multifile preference dialog.


>>> multifile.isDirectoryPreference()
This returns true if 'Execute All Unmodified Files in a Directory' is chosen and returns false if 'Execute File' is chosen.

"""

from skeinforge_utilities import gcodec
from skeinforge_utilities import preferences


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


def getFileOrGcodeDirectory( filename, wasCancelled ):
	"Get the gcode files in the directory the file is in if directory preference is true.  Otherwise, return the file in a list."
	if str( filename ) == '()' or wasCancelled:
		return []
	if isDirectoryPreference():
		return gcodec.getFilesWithFileTypeWithoutWords( 'gcode', [], filename )
	return [ filename ]

def getFileOrUnmodifiedGcodeDirectory( filename, wasCancelled ):
	"Get the gcode files in the directory the file is in if directory preference is true.  Otherwise, return the file in a list."
	if str( filename ) == '()' or wasCancelled:
		return []
	if isDirectoryPreference():
		return gcodec.getUnmodifiedGCodeFiles( filename )
	return [ filename ]

def getFileOrGNUUnmodifiedGcodeDirectory( filename, wasCancelled ):
	"Get the gcode files in the directory the file is in if directory preference is true.  Otherwise, return the file in a list."
	if str( filename ) == '()' or wasCancelled:
		return []
	if isDirectoryPreference():
		return gcodec.getGNUGcode( filename )
	return [ filename ]

def isDirectoryPreference():
	"Determine if the directory preference is true."
	multifilePreferences = MultifilePreferences()
	preferences.readPreferences( multifilePreferences )
	if multifilePreferences.directoryPreference.value:
		print( '"Execute All Unmodified Files in a Directory" is selected, so all the unmodified files in the directory will be executed.  To only execute one file, change the preference in multifile.' )
	else:
		print( '"Execute File" is selected, so only the opened file will be executed.  To execute all the unmodified files in the directory, change the preference in multifile.' )
	return multifilePreferences.directoryPreference.value


class MultifilePreferences:
	"A class to handle the multifile preferences."
	def __init__( self ):
		"Set the default preferences, execute title & preferences filename."
		#Set the default preferences.
		directoryRadio = []
		self.directoryPreference = preferences.RadioLabel().getFromRadioLabel( 'Execute All Unmodified Files in a Directory', 'Multifile Choice:', directoryRadio, False )
		self.filePreference = preferences.Radio().getFromRadio( 'Execute File', directoryRadio, True )
		#Create the archive, title of the dialog & preferences filename.
		self.archive = [ self.directoryPreference, self.filePreference ]
		self.executeTitle = None
		self.filenameHelp = 'multifile.html'
		self.filenamePreferences = preferences.getPreferencesFilePath( 'multifile.csv' )
		self.title = 'Multifile Preferences'


def main( hashtable = None ):
	"Display the file or directory dialog."
	preferences.displayDialog( MultifilePreferences() )

if __name__ == "__main__":
	main()

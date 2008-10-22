#!/bin/sh

"""
Introduction

Skeinforge is a tool chain to forge a gcode skein for a model.

The tool chain starts with slice_shape, which slices the model into layers, then the layers are modified by other tools in turn like
fill, comb, tower, raft, stretch, hop, nozzle_wipe, oozebane, fillet & export.  Each tool automatically gets the gcode from the
previous tool.  So if you want a sliced & filled gcode, call the fill tool and it will call slice_shape, then it will fill and output the
gcode.  If you want to use all the tools, call export and it will call in turn all the other tools down the chain to produce the gcode file.

The skeinforge module provides a single place to call up all the preference dialogs.  When the 'Skeinforge' button is clicked,
skeinforge calls export, since that is the end of the chain.

To run skeinforge, type in a shell in the same folder as skeinforge:
> python skeinforge.py

To run only fill for example, type in the skeinforge_tools folder which fill is in:
> python fill.py

If you do not want a tool after fill to modify the output, deselect the Activate checkbox for that tool.  When the Activate checkbox
is off, the tool will just hand off the gcode to the next tool without modifying it.

There are also tools which handle preferences for the chain, like material & polyfile.

The analyze tool calls plugins in the analyze_plugins folder, which will analyze the gcode in some way when it is generated if
their Activate checkbox is selected.

The import_translator tool accesses and displays the import plugins.

The default preferences are similar to those on Nophead's machine.  A preference which is often different is the
'Extrusion Diameter' in slice_shape.



Getting Started

For skeinforge to run, install python 2.x on your machine, which is available from:
http://www.python.org/download/

To use the preferences dialog you'll also need Tkinter, which probably came with the python installation.  If it did not, look for it at:
http://www.tcl.tk/software/tcltk/

If you want python and Tkinter together on MacOS, you can try:
http://www.astro.washington.edu/owen/PythonOnMacOSX.html

If you want python and Tkinter together on all platforms and don't mind filling out forms, you can try the ActivePython package
from Active State at:
http://www.activestate.com/Products/activepython/feature_list.mhtml

To run gifscene you need the Python Imaging Library, which can be downloaded from:
http://www.pythonware.com/products/pil/

Skeinforge imports Stereolithography (.stl) files or GNU Triangulated Surface (.gts) files.  The import plugin for STL files is
experimental and if it doesn't work, an indirect way to import an STL file is by turning it into a GTS file is by using the Export GNU
Triangulated Surface script at:
http://members.axion.net/~enrique/Export%20GNU%20Triangulated%20Surface.bsh

The Export GNU Triangulated Surface script is also in the Art of Illusion folder, which is in the same folder as skeinforge.py.  To
bring the script into Art of Illusion, drop it into the folder ArtOfIllusion/Scripts/Tools/.  Then import the STL file using the STL
import plugin in the import submenu of the Art of Illusion file menu.  Then from the Scripts submenu in the Tools menu, choose
'Export GNU Triangulated Surface' and select the imported STL shape.  Click the 'Export Selected' checkbox and click OK.
Once you've created the GTS file, you can turn it into gcode by typing in a shell in the same folder as skeinforge:
> python skeinforge.py

When the skeinforge dialog pops up, click 'Skeinforge', choose the file which you exported in 'Export GNU Triangulated Surface'
and the gcode file will be saved with the suffix '_export.gcode'.

Or you can turn files into gcode by adding the file name, for example:
> python skeinforge.py Hollow Square.stl



End of the Beginning

When slice is generating the code, if there is a file start.txt, it will add that to the very beginning of the gcode.  After it has
added some initialization code and just before it adds the extrusion gcode, it will add the file endofthebeginning.txt if it exists.
At the very end, it will add the file end.txt if it exists.  Slice does not care if the text file names are capitalized, but some file
systems do not handle file name cases properly, so to be on the safe side you should give them lower case names.  It will
first look for the file in the same directory as slice, if it does not find it it will look in ~/.skeinforge/gcode_scripts.

The computation intensive python modules will use psyco if it is available and run about twice as fast.  Psyco is described at:
http://psyco.sourceforge.net/index.html

The psyco download page is:
http://psyco.sourceforge.net/download.html



Documentation

The documentation is in the documentation folder, in the doc strings for each module and it can be called from the '?'
button in each preference dialog.

To modify the documentation for this program, modify the first comment in the desired module.  Then open a shell in
the skeinforge.py directory, then type:
> pydoc -w ./'

Then move all the generated html files to the documentation folder.



Fabrication

To fabricate a model with gcode and the Arduino you can use the send.py in the fabricate folder.  The documentation for it is
in the folder as send.html and at:
http://reprap.org/bin/view/Main/ArduinoSend

Another way is to use an EMC2 or similar computer controlled milling machine, as described in the "ECM2 based repstrap"
forum thread at:
http://forums.reprap.org/read.php?1,12143

using the M-Apps package, which is at:
http://forums.reprap.org/file.php?1,file=772

Yet another way is to use Zach's GCode Host, written in Processing:
http://reprap.svn.sourceforge.net/viewvc/reprap/trunk/users/hoeken/arduino/GCode_Host/

For jogging, the Metalab group wrote their own exerciser, also in Processing:
http://reprap.svn.sourceforge.net/viewvc/reprap/trunk/users/metalab/processing/GCode_Exerciser/

There Zach's replicatorG to send parse gcdoe and send it to the machine, at:
http://replicat.org/

The Metalab group has descriptions of skeinforge in action and their adventures are described at:
http://reprap.soup.io/


File Formats

An explanation of the gcodes is at:
http://reprap.org/bin/view/Main/Arduino_GCode_Interpreter

and at:
http://reprap.org/bin/view/Main/MCodeReference

A gode example is at:
http://forums.reprap.org/file.php?12,file=565

The preferences are saved as tab separated .csv files in the .skeinforge folder in your home directory.  The preferences can
be set in the tool dialogs.  The .csv files can also be edited with a text editor or a spreadsheet program set to separate tabs.

The Scalable Vector Graphics file produced by vectorwrite can be opened by an SVG viewer or an SVG capable browser
like Mozilla:
http://www.mozilla.com/firefox/

A good triangle surface format is the GNU Triangulated Surface format, which is supported by Mesh Viewer and described at:
http://gts.sourceforge.net/reference/gts-surfaces.html#GTS-SURFACE-WRITE

STL is an inferior triangle surface format, described at:
http://en.wikipedia.org/wiki/STL_(file_format)



Getting Skeinforge

The latest version is in the last reprap_python_beanshell.zip attachment in the "How to Print Gcode from Host" thread at:
http://forums.reprap.org/read.php?12,10772

a sometimes out of date version is at:
http://members.axion.net/~enrique/reprap_python_beanshell.zip

another sometimes out of date version is at:
https://reprap.svn.sourceforge.net/svnroot/reprap/trunk/reprap/miscellaneous/python-beanshell-scripts/



Motto

I may be slow, but I get there in the end.



Troubleshooting

If there's a bug, try downloading the very latest version because sometimes I update without posting.

Then you can ask for skeinforge help by posting in the "How to Print Gcode from Host" thread at:
http://forums.reprap.org/read.php?12,10772

or send a private message through the forum software by going to my page at:
http://forums.reprap.org/profile.php?12,488



Examples

The following examples slice and dice the STL file Screw Holder.stl.  The examples are run in a terminal in the folder which
contains Screw Holder.gts and skeinforge.py.

> python skeinforge.py
This brings up the dialog, after clicking 'Skeinforge', the following is printed:
The exported file is saved as Screw Holder_export.gcode


> python skeinforge.py Screw Holder.stl
The exported file is saved as Screw Holder_export.gcode


> python
Python 2.5.1 (r251:54863, Sep 22 2007, 01:43:31)
[GCC 4.2.1 (SUSE Linux)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import skeinforge
>>> skeinforge.writeOutput()
The exported file is saved as Screw Holder_export.gcode


>>> skeinforge.main()
This brings up the skeinforge dialog.

"""

from __future__ import absolute_import

from skeinforge_tools.skeinforge_utilities import gcodec
from skeinforge_tools.skeinforge_utilities import preferences
from skeinforge_tools import import_translator
from skeinforge_tools import polyfile
import cStringIO
import sys


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__credits__ = """
Adrian Bowyer <http://forums.reprap.org/profile.php?12,13>
Brendan Erwin <http://forums.reprap.org/profile.php?12,217>
Greenarrow <http://forums.reprap.org/profile.php?12,81>
Ian England <http://forums.reprap.org/profile.php?12,192>
Kyle Corbitt <http://forums.reprap.org/profile.php?12,90>
Marius Kintel <http://reprap.soup.io/>
Nophead <http://www.blogger.com/profile/12801535866788103677>
Reece.Arnott <http://forums.reprap.org/profile.php?12,152>
Wade <http://forums.reprap.org/profile.php?12,489>

Organizations:
Art of Illusion <http://www.artofillusion.org/>"""
__date__ = "$Date: 2008/21/11 $"
__license__ = "GPL 3.0"


def getSkeinforgeToolFilenames():
	"Get skeinforge plugin filenames."
	return gcodec.getPluginFilenames( 'skeinforge_tools', __file__ )

def writeOutput( filename = '' ):
	"Skeinforge a gcode file.  If no filename is specified, skeinforge the first gcode file in this folder that is not modified."
	skeinforgePluginFilenames = getSkeinforgeToolFilenames()
	toolNames = 'export fillet oozebane nozzle_wipe hop stretch raft clip comb tower fill slice_shape'.split()
	for toolName in toolNames:
		for skeinforgePluginFilename in skeinforgePluginFilenames:
			if skeinforgePluginFilename == toolName:
				pluginModule = gcodec.getModule( skeinforgePluginFilename, 'skeinforge_tools', __file__ )
				if pluginModule != None:
					pluginModule.writeOutput( filename )
				return


class SkeinforgePreferences:
	"A class to handle the skeinforge preferences."
	def __init__( self ):
		"Set the default preferences, execute title & preferences filename."
		#Set the default preferences.
		self.archive = []
		self.skeinforgeLabel = preferences.LabelDisplay().getFromName( 'Open Preferences: ' )
		self.archive.append( self.skeinforgeLabel )
		skeinforgePluginFilenames = getSkeinforgeToolFilenames()
		self.skeinforgePlugins = []
		for skeinforgePluginFilename in skeinforgePluginFilenames:
			skeinforgePlugin = preferences.DisplayToolButton().getFromFolderName( 'skeinforge_tools', __file__, skeinforgePluginFilename )
			self.skeinforgePlugins.append( skeinforgePlugin )
		self.archive += self.skeinforgePlugins
		self.filenameInput = preferences.Filename().getFromFilename( import_translator.getGNUTranslatorGcodeFileTypeTuples(), 'Open File to be Skeinforged', '' )
		self.archive.append( self.filenameInput )
		#Create the archive, title of the execute button, title of the dialog & preferences filename.
		self.executeTitle = 'Skeinforge'
		self.filenamePreferences = preferences.getPreferencesFilePath( 'skeinforge.csv' )
		self.filenameHelp = 'skeinforge.html'
		self.saveTitle = None
		self.title = 'Skeinforge Preferences'

	def execute( self ):
		"Skeinforge button has been clicked."
		filenames = polyfile.getFileOrDirectoryTypesUnmodifiedGcode( self.filenameInput.value, import_translator.getGNUTranslatorFileTypes(), self.filenameInput.wasCancelled )
		for filename in filenames:
			writeOutput( filename )

def main():
	"Display the skeinforge dialog."
	if len( sys.argv ) > 1:
		writeOutput( ' '.join( sys.argv[ 1 : ] ) )
	else:
		preferences.displayDialog( SkeinforgePreferences() )

if __name__ == "__main__":
	main()

"""
Gcode_only is an export plugin to remove all the comments from a gcode file.

An export plugin is a script in the export_plugins folder which has the functions getOuput and writeOutput.  It is meant to be run
from the export tool.  To ensure that the plugin works on platforms which do not handle file capitalization properly, give the plugin
a lower case name.

The getOuput function of this script takes a gcode text and returns that text without comments.  The writeOutput function of this
script takes a gcode text and writes that text without comments to a file.
"""

import cStringIO
import os


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"

def getOutput( gcodeText ):
	"""Get the exported version of a gcode file.  This function and writeOutput are the only necessary functions in a skeinforge export plugin.
	If this plugin writes an output than should not be printed, an empty string should be returned."""
	lines = getTextLines( gcodeText )
	output = cStringIO.StringIO()
	for line in lines:
		parseLine( line, output )
	return output.getvalue()

def getSummarizedFilename( filename ):
	"Get the filename basename if the file is in the current working directory, otherwise return the original full name."
	if os.getcwd() == os.path.dirname( filename ):
		return os.path.basename( filename )
	return filename

def getTextLines( text ):
	"Get the all the lines of text of a text."
	return text.replace( '\r', '\n' ).split( '\n' )

def parseLine( line, output ):
	"Parse a gcode line."
	splitLine = line.split( ' ' )
	if len( splitLine ) < 1:
		return
	firstWord = splitLine[ 0 ]
	if len( firstWord ) < 1:
		return
	if firstWord[ 0 ] != '(':
		output.write( line + "\n" )

def writeFileText( filename, fileText ):
	"Write a text to a file."
	try:
		file = open( filename, 'w+' )
		file.write( fileText )
		file.close()
	except IOError:
		print( 'The file ' + filename + ' can not be written to.' )

def writeOutput( filename, gcodeText ):
	"Write the exported version of a gcode file.  This function and getOutput are the only necessary functions in a skeinforge export plugin."
	output = getOutput( gcodeText )
	writeFileText( filename, output )
	print( 'The exported file is saved as ' + getSummarizedFilename( filename ) )

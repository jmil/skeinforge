"""
Gcode_small is an export plugin to remove the comments and the redundant z and feedrate parameters from a gcode file.

An export plugin is a script in the export_plugins folder which has the functions getOuput and writeOutput.  It is meant to be run
from the export tool.  To ensure that the plugin works on platforms which do not handle file capitalization properly, give the plugin
a lower case name.

The getOuput function of this script takes a gcode text and returns that text without comments and redundant z and feedrate
parameters.  The writeOutput function of this script takes a gcode text and writes that text without comments and redundant z
and feedrate parameterscomments to a file.

Many of the functions in this script are copied from gcodec in skeinforge_utilities.  They are copied rather than imported so
developers making new plugins do not have to learn about gcodec, the code here is all they need to learn.

"""

from __future__ import absolute_import
import cStringIO
import os


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"

def getOutput( gcodeText ):
	"""Get the exported version of a gcode file.  This function and writeOutput are the only necessary functions in a skeinforge export plugin.
	If this plugin writes an output than should not be printed, an empty string should be returned."""
	skein = GcodeSmallSkein()
	skein.parseGcode( gcodeText )
	return skein.output.getvalue()

def getStringFromCharacterSplitLine( character, splitLine ):
	"Get the string after the first occurence of the character in the split line."
	indexOfCharacter = indexOfStartingWithSecond( character, splitLine )
	if indexOfCharacter < 0:
		return None
	return splitLine[ indexOfCharacter ][ 1 : ]

def getSummarizedFilename( filename ):
	"Get the filename basename if the file is in the current working directory, otherwise return the original full name."
	if os.getcwd() == os.path.dirname( filename ):
		return os.path.basename( filename )
	return filename

def getTextLines( text ):
	"Get the all the lines of text of a text."
	return text.replace( '\r', '\n' ).split( '\n' )

def indexOfStartingWithSecond( letter, splitLine ):
	"Get index of the first occurence of the given letter in the split line, starting with the second word.  Return - 1 if letter is not found"
	for wordIndex in range( 1, len( splitLine ) ):
		word = splitLine[ wordIndex ]
		firstLetter = word[ 0 ]
		if firstLetter == letter:
			return wordIndex
	return - 1

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


class GcodeSmallSkein:
	"A class to remove redundant z and feedrate parameters from a skein of extrusions."
	def __init__( self ):
		self.lastFeedrateString = None
		self.lastZString = None
		self.output = cStringIO.StringIO()

	def parseGcode( self, gcodeText ):
		"Parse gcode text and store the gcode."
		lines = getTextLines( gcodeText )
		for line in lines:
			self.parseLine( line )

	def parseLine( self, line ):
		"Parse a gcode line."
		splitLine = line.split()
		if len( splitLine ) < 1:
			return
		firstWord = splitLine[ 0 ]
		if len( firstWord ) < 1:
			return
		if firstWord[ 0 ] == '(':
			return
		if firstWord != 'G1':
			self.output.write( line + "\n" )
			return
		xString = getStringFromCharacterSplitLine( 'X', splitLine )
		yString = getStringFromCharacterSplitLine( 'Y', splitLine )
		zString = getStringFromCharacterSplitLine( 'Z', splitLine )
		feedrateString = getStringFromCharacterSplitLine( 'F', splitLine )
		self.output.write( 'G1' )
		if xString != None:
			self.output.write( ' X' + xString )
		if yString != None:
			self.output.write( ' Y' + yString )
		if zString != None and zString != self.lastZString:
			self.output.write( ' Z' + zString )
		if feedrateString != None and feedrateString != self.lastFeedrateString:
			self.output.write( ' F' + feedrateString )
		self.lastFeedrateString = feedrateString
		self.lastZString = zString
		self.output.write( '\n' )

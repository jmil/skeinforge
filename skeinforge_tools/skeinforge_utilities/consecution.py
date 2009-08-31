"""
Consecution is a collection of utilities to chain together the craft plugins.

"""

from __future__ import absolute_import
#Init has to be imported first because it has code to workaround the python bug where relative imports don't work if the module is imported as a main module.
import __init__

from skeinforge_tools.skeinforge_utilities import gcodec
from skeinforge_tools.skeinforge_utilities import interpret
from skeinforge_tools.skeinforge_utilities import preferences
from skeinforge_tools import analyze
from skeinforge_tools import polyfile
import cStringIO
import os
import sys
import time


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


def getCraftModule( fileName ):
	"Get craft module."
	return gcodec.getModule( fileName, 'craft_plugins', os.path.dirname( os.path.abspath( __file__ ) ) )

def getChainText( fileName, procedure ):
	"Get a crafted shape file."
	text = gcodec.getFileText( fileName )
	procedures = getProcedures( procedure, text )
	return getChainTextFromProcedures( fileName, procedures, text )

def getChainTextFromProcedures( fileName, procedures, text ):
	"Get a crafted shape file from a list of procedures."
	lastProcedureTime = time.time()
	for procedure in procedures:
		craftModule = getCraftModule( procedure )
		text = craftModule.getCraftedText( fileName, text )
		if gcodec.isProcedureDone( text, procedure ):
			print( '%s procedure took %s seconds.' % ( procedure.capitalize(), int( round( time.time() - lastProcedureTime ) ) ) )
			lastProcedureTime = time.time()
	return text

def getLastModule():
	"Get the last tool."
	profileSequence = getProfileSequence()
	if len( profileSequence ) < 1:
		return None
	return getCraftModule( profileSequence[ - 1 ] )

def getProcedures( procedure, text ):
	"Get the procedures up to and including the given procedure."
	profileSequence = getProfileSequence()
	sequenceIndexPlusOneFromText = getSequenceIndexPlusOneFromText( text )
	sequenceIndexFromProcedure = getSequenceIndexFromProcedure( procedure )
	return profileSequence[ sequenceIndexPlusOneFromText : sequenceIndexFromProcedure + 1 ]

def getProfileSequence():
	"Get profile sequence."
	profileCraftPreference = 'extrude'
	sequencesDirectory = preferences.getDirectoryInAboveDirectory( 'craft_sequences' )
	profileSequenceFileName = os.path.join( sequencesDirectory, profileCraftPreference + '.csv' )
	profileSequenceText = gcodec.getFileText( profileSequenceFileName )
	profileSequenceLines = gcodec.getTextLines( profileSequenceText )
	profileSequence = []
	for profileSequenceLine in profileSequenceLines[ 1 : ]:
		if len( profileSequenceLine ) > 0:
			profileSequence.append( profileSequenceLine )
	return profileSequence

def getSequenceIndexPlusOneFromText( fileText ):
	"Get the profile sequence index of the file plus one.  Return zero if the procedure is not in the file"
	profileSequence = getProfileSequence()
	for profileSequenceIndex in xrange( len( profileSequence ) - 1, - 1, - 1 ):
		procedure = profileSequence[ profileSequenceIndex ]
		if gcodec.isProcedureDone( fileText, procedure ):
			return profileSequenceIndex + 1
	return 0

def getSequenceIndexFromProcedure( procedure ):
	"Get the profile sequence index of the procedure.  Return None if the procedure is not in the sequence"
	profileSequence = getProfileSequence()
	if procedure not in profileSequence:
		return 0
	return profileSequence.index( procedure )

def writeChainText( fileName, messageBegin, messageEnd, procedure ):
	"Get and write a crafted shape file."
	print( 'File ' + gcodec.getSummarizedFilename( fileName ) + messageBegin )
	startTime = time.time()
	suffixFilename = fileName[ : fileName.rfind( '.' ) ] + '_' + procedure + '.gcode'
	craftText = getChainText( fileName, procedure )
	if craftText == '':
		return
	gcodec.writeFileText( suffixFilename, craftText )
	print( messageEnd + suffixFilename )
	print( 'It took ' + str( int( round( time.time() - startTime ) ) ) + ' seconds to craft the file.' )
	analyze.writeOutput( suffixFilename, craftText )

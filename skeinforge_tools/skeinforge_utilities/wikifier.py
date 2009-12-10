"""
Wikifier is a script to add spaces to the pydoc files and move them to the documentation folder.

"""

from __future__ import absolute_import
#Init has to be imported first because it has code to workaround the python bug where relative imports don't work if the module is imported as a main module.
import __init__

from skeinforge_tools.skeinforge_utilities import gcodec
from skeinforge_tools.skeinforge_utilities import preferences
import cStringIO
import os


__author__ = "Enrique Perez (perez_enrique@yahoo.com)"
__date__ = "$Date: 2008/21/04 $"
__license__ = "GPL 3.0"


def getNavigationHypertext( fileText, transferredFileNameIndex, transferredFileNames ):
	"Get the hypertext help with navigation lines."
	helpTextEnd = fileText.find( '</p>' )
	helpTextStart = fileText.find( '<p>' )
	helpText = fileText[ helpTextStart : helpTextEnd ]
	previousFileName = 'contents.html'
	previousIndex = transferredFileNameIndex - 1
	if previousIndex >= 0:
		previousFileName = transferredFileNames[ previousIndex ]
	previousLinkText = '<a href="%s">Previous</a>' % previousFileName
	helpText = getNavigationLine( '<a href="contents.html">Contents</a>', previousLinkText, getNextLinkText( transferredFileNames, transferredFileNameIndex + 1 ) ) + helpText
	return fileText[ : helpTextStart ] + helpText + fileText[ helpTextEnd : ]

def getNavigationLine( contentsLinkText, previousLinkText, nextLinkText ):
	"Get the wrapped pydoc hypertext help."
	return '<p>\n%s / %s / %s\n</p>\n' % ( previousLinkText, nextLinkText, contentsLinkText )

def getNextLinkText( hypertextFiles, nextIndex ):
	"Get the next link text."
	nextFileName = 'contents.html'
	if nextIndex < len( hypertextFiles ):
		nextFileName = hypertextFiles[ nextIndex ]
	return '<a href="%s">Next</a>' % nextFileName

def getWrappedHypertext( fileText, hypertextFileIndex, hypertextFiles ):
	"Get the wrapped pydoc hypertext help."
	helpTextEnd = fileText.find( '</p>' )
	if helpTextEnd < 0:
		print( 'Failed to find the helpTextEnd in getWrappedHypertext in docwrap.' )
	helpTextStart = fileText.find( '<p>' )
	if helpTextStart < 0:
		print( 'Failed to find the helpTextStart in getWrappedHypertext in docwrap.' )
	helpText = fileText[ helpTextStart : helpTextEnd ]
	helpText = helpText.replace( '&nbsp;', ' ' )
	return fileText[ : helpTextStart ] + helpText + fileText[ helpTextEnd : ]

def readWriteDeleteHypertextHelp( documentDirectoryPath, hypertextFileIndex, hypertextFiles, transferredFileNames ):
	"Read the pydoc hypertext help documents, write them in the documentation folder then delete the originals."
	fileName = hypertextFiles[ hypertextFileIndex ]
	print( fileName )
	filePath = os.path.join( documentDirectoryPath, fileName )
	fileText = gcodec.getFileText( fileName )
	fileText = getWrappedHypertext( fileText, hypertextFileIndex, hypertextFiles )
	if fileText.find( 'This page is in the table of contents.' ) > - 1:
		fileText = fileText.replace( 'This page is in the table of contents.', '' )
		transferredFileNames.append( fileName )
	gcodec.writeFileText( filePath, fileText )
	os.remove( fileName )

def readWriteNavigationHelp( documentDirectoryPath, transferredFileNameIndex, transferredFileNames ):
	"Read the hypertext help documents, and add the navigation lines to them."
	fileName = transferredFileNames[ transferredFileNameIndex ]
	print( fileName )
	filePath = os.path.join( documentDirectoryPath, fileName )
	fileText = gcodec.getFileText( filePath )
	fileText = getNavigationHypertext( fileText, transferredFileNameIndex, transferredFileNames )
	gcodec.writeFileText( filePath, fileText )

def removeFilesInDirectory( directoryPath ):
	"Remove all the files in a directory."
	fileNames = os.listdir( directoryPath )
	for fileName in fileNames:
		filePath = os.path.join( directoryPath, fileName )
		os.remove( filePath )

def writeContentsFile( documentDirectoryPath, hypertextFiles ):
	"Write the contents file."
	output = cStringIO.StringIO()
	output.write( '<html>\n  <head>\n    <title>Contents</title>\n  </head>\n  <body>\n' )
	output.write( getNavigationLine( 'Contents', 'Previous', getNextLinkText( hypertextFiles, 0 ) ) )
	for hypertextFile in hypertextFiles:
		writeContentsLine( hypertextFile, output )
	output.write( '  </body>\n</html>\n' )
	filePath = os.path.join( documentDirectoryPath, 'contents.html' )
	gcodec.writeFileText( filePath, output.getvalue() )

def writeContentsLine( hypertextFile, output ):
	"Write a line of the contents file."
	summarizedFileName = hypertextFile[ : hypertextFile.rfind( '.' ) ]
	numberOfDots = summarizedFileName.count( '.' )
	prefixSpaces = '&nbsp;&nbsp;' * numberOfDots
	if numberOfDots > 0:
		summarizedFileName = summarizedFileName[ summarizedFileName.rfind( '.' ) + 1 : ]
	capitalizedSummarizedFileName = preferences.getEachWordCapitalized( summarizedFileName )
	output.write( '%s<a href="%s">%s</a><br>\n' % ( prefixSpaces, hypertextFile, capitalizedSummarizedFileName ) )

def writeHypertext():
	"Run pydoc, then read, write and delete each of the files."
	shellCommand = 'pydoc -w ./'
	commandResult = os.system( shellCommand )
	if commandResult != 0:
		print( 'Failed to execute the following command in writeHypertext in docwrap.' )
		print( shellCommand )
	hypertextFiles = gcodec.getFilesWithFileTypeWithoutWords( 'html' )
	if len( hypertextFiles ) <= 0:
		print( 'Failed to find any help files in writeHypertext in docwrap.' )
		return
	documentDirectoryPath = gcodec.getAbsoluteFolderPath( hypertextFiles[ 0 ], 'documentation' )
	removeFilesInDirectory( documentDirectoryPath )
	sortedReplaceFiles = []
	for hypertextFile in hypertextFiles:
		sortedReplaceFiles.append( hypertextFile.replace( '.html', '. html' ) )
	sortedReplaceFiles.sort()
	hypertextFiles = []
	for sortedReplaceFile in sortedReplaceFiles:
		hypertextFiles.append( sortedReplaceFile.replace( '. html', '.html' ) )
	transferredFileNames = []
	for hypertextFileIndex in xrange( len( hypertextFiles ) ):
		readWriteDeleteHypertextHelp( documentDirectoryPath, hypertextFileIndex, hypertextFiles, transferredFileNames )
	for transferredFileNameIndex in xrange( len( transferredFileNames ) ):
		readWriteNavigationHelp( documentDirectoryPath, transferredFileNameIndex, transferredFileNames )
	writeContentsFile( documentDirectoryPath, transferredFileNames )
	print( '%s files were wrapped.' % len( transferredFileNames ) )


def main():
	"Display the craft dialog."
	writeHypertext()

if __name__ == "__main__":
	main()

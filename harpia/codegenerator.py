# -*- coding: utf-8 -*-
#
# STARLING PROJECT 
#
# LIRIS - Laboratoire d'InfoRmatique en Image et Systèmes d'information 
#
# Copyright: 2012 - 2015 Eric Lombardi (eric.lombardi@liris.cnrs.fr), LIRIS (liris.cnrs.fr), CNRS (www.cnrs.fr)
#
#
#    This program is free software: you can redistribute it and/or modify it
#    under the terms of the GNU General Public License version 3, as published
#    by the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranties of
#    MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
#    PURPOSE.  See the GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    For further information, check the COPYING file distributed with this software.
#
#----------------------------------------------------------------------

#
# C/C++ code generator.
# Convert blocks graph to C/C++ code.
#

import re
import os
import subprocess
import threading
import multiprocessing
import sys
import gobject

import lvExtensions
import blocksgraph
import s2idirectory
import xmltree

# constants
unixMakefileName = 'build.sh'
winMakefileName = 'build.bat'
winRunFileName = 'run.bat'
codeFileName = 'source_code.cpp'
executableName = 'executable'

# C/C++ compilation informations
includePaths = []
libraries = []
libraryPaths = []

# C/C++ code sections
includes = []
functions = []
initializations = []
processings = []
cleanings = []


"""
Return blockId string blockxx_.
"""
def getBlockIdStr(blockId):
	return str(blockId)


"""
Return output variable name
"""
def getOutVarName(blockId, outId):
	return 'block' + getBlockIdStr(blockId) + '_out' + str(outId)


"""
Return generic input name for given input id.
Generic input name is used in block definition xml file.
"""
def getGenericInputName(inputId):
	return '_INPUT' + str(inputId) + '_'


"""
Return generic output name for given output id.
Generic output name is used in block definition xml file.
"""
def getGenericOutputName(outputId):
	return '_OUTPUT' + str(outputId) + '_'


"""
Replace text in string.
"""
def replace( string, oldText, newText):
	return re.sub( oldText, newText, string, flags=re.MULTILINE)


"""
Remove duplicate element from list, whilst preserving order.
"""
def uniq(input):
	output = []
	for x in input:
		if x not in output:
			output.append(x)
	return output


"""
Generate C/C++ code for one block from blocks graph
"""
def generateBlockCode(blockId, block):
	global includePaths
	global libraries
	global libraryPaths
	global includes
	global functions
	global initializations
	global processings
	global cleanings
	bkIncludes = ''
	bkFunctions = ''
	bkInitializations = ''
	bkProcessings = ''
	bkCleanings = ''

	blockDict = s2idirectory.block 	# generic block definition
	blockType = block['type']

	# create output variables even if they are not used
	# and build _OUTPUTx_ to real variable matching table
	outVarNames = {}
	for outId in blockDict[blockType]['OutTypes'].iterkeys():
		outType = blockDict[blockType]['OutTypes'][outId]['type']
		varName = getOutVarName(blockId, outId)
		outVarNames[getGenericOutputName(outId)] = '&' + varName
		bkProcessings += outType + ' ' + varName + ';\n'

	# build _INPUTx_ to real variable matching table
	inVarNames = {}
	for inId in blockDict[blockType]['InTypes'].iterkeys():
		inVarNames[getGenericInputName(inId)] = 'NULL'
	for inId, fromBlockId, fromOutputId in block['inputs']:
		inVarNames[getGenericInputName(inId)] = '&' + getOutVarName(fromBlockId, fromOutputId)

	# get code sections from block definition
	bkIncludes += blockDict[blockType]['includes']
	bkFunctions += blockDict[blockType]['functions']
	bkInitializations += blockDict[blockType]['initializations']
	bkProcessings += blockDict[blockType]['processings']
	bkCleanings += blockDict[blockType]['cleanings']

	# replace parameter name by real value
	for	paramName, paramValue in block['properties'].iteritems():
		paramType = blockDict[blockType]['Defaultprops'][paramName].get('type')
		if paramType == 'filename':
			paramValue = lvExtensions.getAbsolutePath(paramValue)
			# on windows, replace \ by \\ in file path
			if os.name == 'nt':
				paramValue = paramValue.replace('\\', '\\\\\\\\')
		bkInitializations = replace(bkInitializations, paramName, paramValue)
		bkProcessings = replace(bkProcessings, paramName, paramValue) 
		bkCleanings = replace(bkCleanings, paramName, paramValue) 
	
	# replace _BLOCKID_
	# this is done after parameter replacement, so that _BLOCKID_ keyword
	# can be used as a parameter value ;)
	bkInitializations = replace(bkInitializations, '_BLOCKID_', getBlockIdStr(blockId))
	bkProcessings = replace(bkProcessings, '_BLOCKID_', getBlockIdStr(blockId))
	bkCleanings = replace(bkCleanings, '_BLOCKID_', getBlockIdStr(blockId))
	
	# replace _INPUTx_ by real variable name
	for inputStr, inVarName in inVarNames.iteritems():
		bkProcessings = replace(bkProcessings, inputStr, inVarName)
		
	# replace _OUTPUTx_ by real variable name
	for outputStr, outVarName in outVarNames.iteritems():
		bkProcessings = replace(bkProcessings, outputStr, outVarName)

	# update source code
	includes.append(bkIncludes)
	functions.append(bkFunctions)
	initializations.append(bkInitializations)
	processings.append(bkProcessings)
	cleanings.append(bkCleanings)

	# update compilation informations
	includePaths.extend(blockDict[blockType]['includePaths'])
	libraries.extend(blockDict[blockType]['libraries'])
	libraryPaths.extend(blockDict[blockType]['libraryPaths'])


"""
Return a string of formatted code based on a code string list.
"""
def formatCode(codeStrList, tabs='', afterEach='\n', afterCode=''):
	# concatenate strings
	codeStr = ''
	for elt in codeStrList:
		codeStr += elt
		if elt != '':
			codeStr += afterEach

	# add tabs at beginning of each line
	if tabs and codeStr:
		codeStr = re.sub( '^', tabs, codeStr, flags=re.MULTILINE)

	# remove unwanted tabs on empty lines
	codeStr = re.sub( '^\t*$', '', codeStr, flags=re.MULTILINE)

	if codeStr and afterCode:
		codeStr += afterCode

	return codeStr


"""
Return true if block is a source and a stream.
"""
def getBlockIsStream(block):
	blockDict = s2idirectory.block 	# generic block definition
	blockType = block['type']

	if blockDict[blockType]['Inputs'] == 0 and blockDict[blockType]['IsStream']:
		return True
	else:
		return False


"""
Parse blocs graph, generate code for each bloc.
"""
def generateCode(processingChainFileName):
	global includePaths
	global libraries
	global libraryPaths
	global includes
	global functions
	global initializations
	global processings
	global cleanings

	# reset global variables
	includePaths = []
	libraries = []
	libraryPaths = []
	includes = []
	functions = []
	initializations = []
	processings = []
	cleanings = []

	# batch mode indicator
	inBatchMode = False

	# load blocks graph from file
	xmlChain = xmltree.xmlTree()
	xmlChain.load(processingChainFileName)
	assert xmlChain.isValid(), 'failed to parse xml file: %r'
	
	# build blocks graph
	graph = blocksgraph.blocksGraph()
	graph.buildFromXml(xmlChain)
	#print graph.graph

	# produce code by parsing graph by rank (depth) order
	for blockId in graph.getSortedBlocks():
		generateBlockCode(blockId, graph.getBlock(blockId))

	# remove duplicates from some sections
	includePaths = uniq(includePaths)
	libraries = uniq(libraries)
	libraryPaths = uniq(libraryPaths)
	includes = uniq(includes)
	functions = uniq(functions)
	initializations = uniq(initializations)

	# check if one source is a stream
	isStream = False
	for block in graph.getBlocksList().values():
		isStream = getBlockIsStream(block)
		if isStream:
			break  # there is one stream, no need to continue

	# check if there is a 'show' block
	isShow = False
	for block in graph.getBlocksList().values():
		if block['type'] == 2:
			isShow = True
			break

	# headers
	sourceCode = '''
#include <opencv2/opencv.hpp>
#include <stdio.h>

#ifdef WIN32
	// unix to win porting
	#define	  __func__   __FUNCTION__
	#define	  __PRETTY_FUNCTION__   __FUNCTION__
	#define   snprintf   _snprintf
	#define	  sleep(n_seconds)   Sleep((n_seconds)*1000)
	#define   round(d)   floor((d) + 0.5)
#endif
'''

	# add include section
	sourceCode += '\n\n'
	sourceCode += formatCode(['// includes section'], afterCode='\n')
	sourceCode += formatCode(includes, afterCode='\n')

	# add function definition section
	sourceCode += formatCode(['// functions section'], afterCode='\n')
	sourceCode += formatCode(functions, afterEach='\n\n')

	sourceCode += '''
int main(void)
{
	// disable buffer on stdout to make 'printf' outputs
	// immediately displayed in GUI-console
	setbuf(stdout, NULL);

'''

	# add initialization section
	tabs = '\t'
	sourceCode += formatCode(['// initializations section'], tabs, afterCode='\n')
	sourceCode += formatCode(initializations, tabs, afterCode='\n')

	# if one source is a stream, add a loop
	if isStream:
		sourceCode += formatCode(['int key = 0;'], tabs)
		sourceCode += formatCode(['bool paused = false;'], tabs)
		sourceCode += formatCode(['bool goOn = true;'], tabs)
		sourceCode += formatCode(['while( goOn )'], tabs)
		sourceCode += formatCode(['{'], tabs)
		tabs = '\t\t'

	# add processing section
	sourceCode += formatCode(['// processings section'], tabs, afterCode='\n')
	sourceCode += formatCode(processings, tabs, afterCode='\n')

	# add minimal user interaction, but not in batch mode
	if not inBatchMode:
		if isStream: 
			# pause/unpause when space key pressed
			sourceCode += formatCode(['if( paused )'], tabs)
			sourceCode += formatCode(['\tkey = cv::waitKey(0);'], tabs)
			sourceCode += formatCode(['else'], tabs)
			sourceCode += formatCode(['\tkey = cv::waitKey(25);'], tabs)
			sourceCode += formatCode(['if( (key & 255) == \' \' )'], tabs)
			sourceCode += formatCode(['\tpaused = ! paused;'], tabs)
			sourceCode += formatCode(['else if( key != -1 )'], tabs)
			sourceCode += formatCode(['\tgoOn = false;'], tabs)
		elif isShow:
			sourceCode += formatCode(['cv::waitKey(0);'], tabs, afterCode='\n')

	# if one source is a stream, close loop
	if isStream: 
		tabs = '\t'
		sourceCode += formatCode(['}'], tabs, afterCode='\n')
		
	# add cleaning section
	sourceCode += formatCode(['// cleanings section'], tabs, afterCode='\n')
	sourceCode += formatCode(cleanings, tabs, afterCode='\n')

	# end of code
	sourceCode += formatCode(['return 0;'], tabs)
	sourceCode += formatCode(['}'], afterCode='\n')


	#print 'processings=', processings
	#print 'cleanings=', cleanings
	#print sourceCode
	return sourceCode


"""
Save code to file.
"""
def saveCode(sourceCode):
	print 'Save code to file \'' + os.path.abspath(codeFileName) + '\''
	codeFile = open(codeFileName, 'w')
	codeFile.write(sourceCode)
	codeFile.close()


"""
Create Makefile to compile source code.
"""
def createMakefile():
	global includePaths
	global libraries
	global libraryPaths

	# add Opencv paths and libs

	includePaths = lvExtensions.getOpencvIncludeDirs().split(';') + includePaths
	libraryPaths = lvExtensions.getOpencvLibrariesDirs().split(';') + libraryPaths
	libraries = lvExtensions.getOpencvLibraries().split(';') + libraries
	dllPaths = lvExtensions.getOpencvDllDirs().split(';')

	# add other libraries paths and libs

	includePaths = lvExtensions.getOtherIncludeDirs().split(';') + includePaths
	libraryPaths = lvExtensions.getOtherLibrariesDirs().split(';') + libraryPaths
	libraries = lvExtensions.getOtherLibraries().split(';') + libraries
	dllPaths = lvExtensions.getOtherDllDirs().split(';') + dllPaths

	# add extra include path

	includePaths.insert(0, lvExtensions.getLirisvisionDir())

	# remove empty strings from paths and libs list

	includePaths = filter(lambda f: f != '', includePaths)
	libraryPaths = filter(lambda f: f != '', libraryPaths)
	libraries = filter(lambda f: f != '', libraries)
	dllPaths = filter(lambda f: f != '', dllPaths)

	# replace _LV_DIR_ keyword in include and library paths
	# then convert relative paths to absolute paths
	includePaths = [p.replace('_LV_DIR_',lvExtensions.getLirisvisionDir()) for p in includePaths]	
	includePaths = [lvExtensions.getAbsolutePath(p) for p in includePaths]	
	libraryPaths = [p.replace('_LV_DIR_',lvExtensions.getLirisvisionDir()) for p in libraryPaths]	
	libraryPaths = [lvExtensions.getAbsolutePath(p) for p in libraryPaths]	
	dllPaths = [lvExtensions.getAbsolutePath(p) for p in dllPaths]	

	# create makefiles

	print 'Create Makefiles'

	# Windows ...

	makeFileEntry = '@echo off\n'
	makeFileEntry += '\n'
	makeFileEntry += 'REM set path for visual C++\n'
	#makeFileEntry += 'call "%VS90COMNTOOLS%vsvars32.bat"\n'
	makeFileEntry += 'call "%VS100COMNTOOLS%vsvars32.bat"\n'
	makeFileEntry += '\n'
	makeFileEntry += 'cl.exe /EHsc /MD /DWIN32 /I "%WindowsSdkDir%\Include"'
	
	for includePath in includePaths:
		makeFileEntry += ' /I ' + includePath

	makeFileEntry += ' ' + codeFileName

	for libName in libraries:
		makeFileEntry += ' ' + libName + '.lib'
	
	makeFileEntry += ' /link /LIBPATH:"%WindowsSdkDir%\\Lib"'

	for libDir in libraryPaths:
		makeFileEntry += ' /LIBPATH:"' + libDir + '"'

	makeFileEntry += '\n'

	makeFile = open(winMakefileName, 'w')
	makeFile.write(makeFileEntry)
	makeFile.close()

	winRunEntry = '@echo off\n'
	winRunEntry += '\n'
	winRunEntry += 'set PATH=%PATH%;'
	for dllDir in dllPaths:
		winRunEntry += dllDir + ';'
	for libDir in libraryPaths:
		winRunEntry += libDir + ';'

	winRunEntry += '\n'
	winRunEntry += 'source_code.exe'
	winRunFile = open(winRunFileName, 'w')
	winRunFile.write(winRunEntry)
	winRunFile.close()
	
	# Linux ...

	makeFileEntry = "#!/bin/bash\n\ng++ -o " + executableName

	for includePath in includePaths:
		makeFileEntry += ' -I"' + includePath + '"'

	makeFileEntry += ' ' + codeFileName

	for libDir in libraryPaths:
		makeFileEntry += ' -L"' + libDir + '"'

	for libName in libraries:
		makeFileEntry += ' -l' + libName

	if sys.platform != 'darwin' :
		if libraryPaths :
			makeFileEntry += ' -Xlinker -rpath="'
			for libDir in libraryPaths:
				makeFileEntry += libDir + ':'
			makeFileEntry += '"'

	makeFileEntry += '\n'

	makeFile = open(unixMakefileName, 'w')
	makeFile.write(makeFileEntry)
	makeFile.close()


"""
Run project.
@return: running subprocess
"""
def runProject():
	# linux
	compileCmd = ['sh', unixMakefileName]
	runFileName = executableName
	if os.name == "nt":
		# win
		compileCmd = [winMakefileName]
		runFileName = winRunFileName

	# compiling
	print 'Compiling in \'' + os.getcwd() + '\' ...'
	p = subprocess.Popen(compileCmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	compileOutput = p.communicate()[0]
	compileResult = p.returncode

	if compileResult != 0:
		print 'COMPILATION FAILED !'
		lvExtensions.runEditor([codeFileName])

	if compileOutput:
		if os.name == "nt":
			# fix compiler output character coding / GTK Text View issue on Windows
			if sys.__stdout__.encoding:
				compileOutput = compileOutput.decode(sys.__stdout__.encoding)
		compileOutput = "COMPILATION MESSAGE:\n" + compileOutput
		print compileOutput
	
	# running
	p = None
	if compileResult == 0:
		print 'Running ... (press ESC to stop, SPACE to pause)'
		execPath = os.path.abspath(runFileName)
		currentDir = os.getcwd()
		p = runSubprocess(execPath)
		os.chdir(currentDir)
	return p


"""
Run subprocess in non-blocking mode
and launch subprocess monitoring thread.
"""
def runSubprocess(executablePath):
	# start subprocess
	p = subprocess.Popen(executablePath, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	print 'Subprocess ' + str(p.pid) + ' started' 

	# start subprocess monitoring thread
	thread = threading.Thread(target=monitoringThread, args=(p,))
	thread.start()
	return p

"""
Subprocess monitoring thread.
Continuously display subprocess output in console.
"""
def monitoringThread(process):
	# Due to stdout being redirected to GUI,
	# do NOT call 'print' function here, nor any other gui function
	# because pygtk has issues with threading.
	# Use gobject.idle_add(...) to interact with GUI.
	# Using 'sys.__stdout__.write()' to write in the real console is also safe.
	#sys.__stdout__.write('DBG in codegenerator.monitoringThread')
	while process.poll() is None:
		chars = process.stdout.read()
		#sys.__stdout__.write(chars)
		gobject.idle_add(sys.stdout.write, chars, priority=gobject.PRIORITY_HIGH_IDLE)
	message = 'Subprocess ' + str(process.pid) + ' stopped\n' 
	gobject.idle_add(sys.stdout.write, message, priority=gobject.PRIORITY_HIGH_IDLE)
	return


"""
Build and run image processing diagram.
Returns running subprocess.
"""
def buildAndRunProject(processingChainFileName):
	sourceCode = generateCode(processingChainFileName)
	saveCode(sourceCode)
	createMakefile()
	return runProject()


"""
Open source code in an editor.
"""
def editSourceCode(dirName):
	lvExtensions.runEditor([dirName + '/' + codeFileName])

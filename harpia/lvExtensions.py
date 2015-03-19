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
# Store and manage Starling configuration.
# Define some usefull functions to load blocks, open editor ...
#

import re
import subprocess
import os
import sys
import glob
import tempfile

import xmltree

#----------------------------------------------------------------------

# directory from which this program is run
runDir = os.path.abspath(os.getcwd())  

harpia_data_dir = 'app_data/'

lirisvisionDir = '../..'
if os.name == "nt":
	lirisvisionDir = '..\\..'

workingDirsPlace = '' # the place (directory) where temporary working directories are created 
user_guide_filename = os.path.normpath('doc/user_guide.html')
developer_guide_filename = os.path.normpath('doc/developer_guide.html')
configurationFileName = os.path.expanduser('~/.starling.conf')

# options used to compile generated C++ code
compilerOptions = ''
linkerOptions = ''

# directories where local blocks are stored (string list separated by ";")
localBlocksDirs = ''

# OpenCV directories
# values are lists of strings separated by ";"
# default values for Linux
opencvIncludeDirs = '/usr/include/opencv'
opencvLibrariesDirs = ''
opencvDllDirs = ''
opencvLibraries = 'opencv_core;opencv_imgproc;opencv_highgui;opencv_ml;opencv_video;opencv_features2d;opencv_calib3d;opencv_objdetect;opencv_contrib;opencv_legacy;opencv_flann'
if os.name == "nt":
	# default values for Windows
	opencvDir = lirisvisionDir + '\\External\\opencv-2.4.8'
	opencvIncludeDirs = opencvDir + '\\build\\include;' + opencvDir + '\\build\\include\\opencv'
	opencvLibrariesDirs = opencvDir + '\\build\\x86\\vc10\\lib'
	opencvDllDirs = opencvDir + '\\build\\x86\\vc10\\bin'
	opencvLibraries =		'opencv_calib3d248;opencv_contrib248;opencv_core248;opencv_features2d248;opencv_flann248;opencv_gpu248;opencv_highgui248;opencv_imgproc248;opencv_legacy248;opencv_ml248;opencv_objdetect248;opencv_ocl248;opencv_photo248;opencv_stitching248;opencv_superres248;opencv_ts248;opencv_video248;opencv_videostab248'
	
# Other libraries directories and names
# values are lists of strings separated by ";"
# default values
otherIncludeDirs = ''
otherLibrariesDirs = ''
otherDllDirs = ''
otherLibraries = ''
if os.name == "nt":
	# default values for Windows
	otherDllDirs = '..\\..\\External\\dlls'

#----------------------------------------------------------------------

"""
Add blocks from xml files present in one directory.
"""
def addBlocksFromDir(blocks, dirName, relativePath=False):
	if relativePath:
		currentDir = os.getcwd()
		dirName = currentDir + '/' + harpia_data_dir + '/' + dirName
		fileNames = glob.glob(dirName + '/*.xml')
	else:
		fileNames = glob.glob(dirName + '/*.xml')

	for fileName in fileNames :
		addBlockFromFile(blocks, fileName)

#----------------------------------------------------------------------

def addBlockFromFile( blocks, fileName):
	"""add one block entirely defined in xml configuration file"""
	"""alternative way of hardcoded one in s2idirectory.py"""
	tree = xmltree.xmlTree()
	tree.load(fileName)
	#print 'DBG fileName=', fileName
	#print 'DBG tree=', tree.toString()

	# parse file

	blockType = int(tree.getAttribute('./block', 'type'))

	# get default properties
	properties = {}
	for prop in tree.findAttributes('./block/property'):
		propName = prop['name']
		prop.pop('name')
		properties[propName] = prop
	#print 'DBG in', __file__, '.addBlockFromFile(), properties=', properties

	label = tree.getText('./label')
	xmlpath = fileName
	inputs = {}
	for input in tree.findAttributes('./input'):
		# each input is a dictionnary of input attributes
		inputs[int(input['id'])] = input

	outputs = {}
	for output in tree.findAttributes('./output'):
		# each output is a dictionnary of output attributes
		outputs[int(output['id'])] = output

	icon =  tree.getText('./icon')
	color =  tree.getText('./color')
	description =  tree.getText('./description')
	treegroup =  tree.getText('./treegroup')
	isstream = False
	if tree.getText('./isstream') == 'true':
		isstream = True

	# get compilation informations

	includePaths = []
	for inclPath in tree.findAttributes('./includepath'):
		try:
			pathStr = inclPath['path']
			if pathStr:
				# do not append empty string !
				includePaths.append(pathStr)
		except:
			pass

	libraries = []
	for elem in tree.findAttributes('./library'):
		try:
			libStr = elem['name']
			if libStr:
				# do not append empty string !
				libraries.append(libStr)
		except:
			pass

	libraryPaths = []
	for elem in tree.findAttributes('./librarypath'):
		try:
			pathStr = elem['path']
			if pathStr:
				# do not append empty string !
				libraryPaths.append(pathStr)
		except:
			pass

	# get code and remove unwanted characters
	includes = tree.getText('./includes')
	includes = cleanCode(includes)

	functions = tree.getText('./functions')
	functions = cleanCode(functions)

	initializations = tree.getText('./initializations')
	initializations = cleanCode(initializations)

	processings = tree.getText('./processings')
	processings = cleanCode(processings)

	cleanings = tree.getText('./cleanings')
	cleanings = cleanCode(cleanings)

	# add new block to block list
	blocks[blockType] = { 
		"Defaultprops":properties,
		"Label":label,
		"Path":{ "Xml":xmlpath },
		"Inputs":len(inputs),
		"Outputs":len(outputs),
		"Icon":icon,
		"Color":color,
		"InTypes":inputs,
		"OutTypes":outputs,
		"Description":description,
		"TreeGroup":treegroup,
		"IsStream":isstream,
		"includes":includes,
		"includePaths":includePaths,
		"libraries":libraries,
		"libraryPaths":libraryPaths,
		"functions":functions,
		"initializations":initializations,
		"processings":processings,
		"cleanings":cleanings,
		"help":tree.getText('./help')
	}

#----------------------------------------------------------------------

"""
Remove unwanted characters from code string.
"""
def cleanCode(codeStr):
	# remove tabs and blank lines
	codeStr = re.sub( r'^\n[ \t]*\n', '', codeStr)
	codeStr = re.sub( r'\n[ \t]*\n[ \t]*$', '', codeStr)
	codeStr = re.sub( r'[ \t]*\n[ \t]*$', '', codeStr)
	return codeStr

#----------------------------------------------------------------------

"""
Run text editor.
Files to open are given as list.
"""
def runEditor(fileNamesList):
	if os.name == "nt":
		# windows
		cmd = ["notepad.exe"]
	else:
		if sys.platform != 'darwin' :
			# linux
			#cmd = ["gedit"]
			cmd = ["xdg-open"]
		else:
			cmd = ['open']
	cmd.extend(fileNamesList)
	subprocess.Popen(cmd)

#----------------------------------------------------------------------

"""
Open documentation, using default system viewer.
"""
def openDocumentation(doc):
	if doc == 'user':
		filename = user_guide_filename
	elif doc == 'developer':
		filename = developer_guide_filename
	else:
		return

	if os.name == 'nt':
		# windows
		cmd = ['start', filename]
		subprocess.Popen(cmd, shell=True)
	else:
		if sys.platform != 'darwin' :
			# linux
			cmd = ['xdg-open', filename]
			subprocess.Popen(cmd)
		else:
			subprocess.Popen(['open', filename])

#----------------------------------------------------------------------

"""
Get absolute path.
Relative path are relative to Starling directory.
"""
def getAbsolutePath(path):
	if not os.path.isabs(path):
		# make an absolute path
		path = runDir + '/' + path
	path = os.path.normpath(path)
	return path

#----------------------------------------------------------------------

"""
Set working directory place.
"""
def setWorkingDirsPlace(wdir):
	global workingDirsPlace
	if wdir:
		workingDirsPlace = getAbsolutePath(wdir)
	else:
		workingDirsPlace = '' 

#----------------------------------------------------------------------

"""
Get working directory.
"""
def getWorkingDirsPlace():
	return workingDirsPlace

#----------------------------------------------------------------------

"""
Set LIRIS-VISION directory
"""
def setLirisvisionDir(dirName):
	global lirisvisionDir
	lirisvisionDir = dirName

#----------------------------------------------------------------------

"""
Get LIRIS-VISION directory
"""
def getLirisvisionDir():
	return lirisvisionDir

#----------------------------------------------------------------------

"""
Set Opencv include dirs
"""
def setOpencvIncludeDirs(dirsNames):
	global opencvIncludeDirs
	opencvIncludeDirs = dirsNames.strip(';')

#----------------------------------------------------------------------

"""
Get Opencv include dirs
"""
def getOpencvIncludeDirs():
	return opencvIncludeDirs

#----------------------------------------------------------------------

"""
Set Opencv libraries dirs
"""
def setOpencvLibrariesDirs(dirsNames):
	global opencvLibrariesDirs
	opencvLibrariesDirs = dirsNames.strip(';')

#----------------------------------------------------------------------

"""
Get Opencv libraries dirs
"""
def getOpencvLibrariesDirs():
	return opencvLibrariesDirs

#----------------------------------------------------------------------

"""
Set Opencv dll dirs
"""
def setOpencvDllDirs(dirsNames):
	global opencvDllDirs
	opencvDllDirs = dirsNames.strip(';')

#----------------------------------------------------------------------

"""
Get Opencv dll dirs
"""
def getOpencvDllDirs():
	return opencvDllDirs

#----------------------------------------------------------------------

"""
Set Opencv libraries
"""
def setOpencvLibraries(libsNames):
	global opencvLibraries
	opencvLibraries = libsNames.strip(';')

#----------------------------------------------------------------------

"""
Get Opencv libraries
"""
def getOpencvLibraries():
	return opencvLibraries

#----------------------------------------------------------------------

"""
Set other include dirs
"""
def setOtherIncludeDirs(dirsNames):
	global otherIncludeDirs
	otherIncludeDirs = dirsNames.strip(';')

#----------------------------------------------------------------------

"""
Get other include dirs
"""
def getOtherIncludeDirs():
	return otherIncludeDirs

#----------------------------------------------------------------------

"""
Set other libraries dirs
"""
def setOtherLibrariesDirs(dirsNames):
	global otherLibrariesDirs
	otherLibrariesDirs = dirsNames.strip(';')

#----------------------------------------------------------------------

"""
Get other libraries dirs
"""
def getOtherLibrariesDirs():
	return otherLibrariesDirs

#----------------------------------------------------------------------

"""
Set other dll dirs
"""
def setOtherDllDirs(dirsNames):
	global otherDllDirs
	otherDllDirs = dirsNames.strip(';')

#----------------------------------------------------------------------

"""
Get other dll dirs
"""
def getOtherDllDirs():
	return otherDllDirs

#----------------------------------------------------------------------

"""
Set other libraries
"""
def setOtherLibraries(libsNames):
	global otherLibraries
	otherLibraries = libsNames.strip(';')

#----------------------------------------------------------------------

"""
Get other libraries
"""
def getOtherLibraries():
	return otherLibraries

#----------------------------------------------------------------------

"""
Set compiler options
"""
def setCompilerOptions(options):
	global compilerOptions
	compilerOptions = options

#----------------------------------------------------------------------

"""
Get compiler options
"""
def getCompilerOptions():
	return compilerOptions

#----------------------------------------------------------------------

"""
Set linker options
"""
def setLinkerOptions(options):
	global linkerOptions
	linkerOptions = options

#----------------------------------------------------------------------

"""
Get linker options
"""
def getLinkerOptions():
	return linkerOptions

#----------------------------------------------------------------------

"""
Set local blocks directories
"""
def setLocalBlocksDirs(dirsNames):
	global localBlocksDirs
	localBlocksDirs = dirsNames.strip(';')

#----------------------------------------------------------------------

"""
Get local blocks directories
"""
def getLocalBlocksDirs():
	return localBlocksDirs

#----------------------------------------------------------------------

"""
Set configuration file name.
"""
def setConfigurationFileName(name):
	global configurationFileName
	configurationFileName = name

#----------------------------------------------------------------------

"""
Save configuration to file
"""
def saveConfiguration():
	config = '<?xml version="1.0" encoding="UTF-8"?>\n'
	config += '<starlingConfiguration>\n'
	config += '\t<lirisvisionDir>' + unicode(lirisvisionDir) + '</lirisvisionDir>\n'
	config += '\t<opencvIncludeDirs>' + unicode(opencvIncludeDirs) + '</opencvIncludeDirs>\n'
	config += '\t<opencvLibrariesDirs>' + unicode(opencvLibrariesDirs) + '</opencvLibrariesDirs>\n'
	config += '\t<opencvDllDirs>' + unicode(opencvDllDirs) + '</opencvDllDirs>\n'
	config += '\t<opencvLibraries>' + unicode(opencvLibraries) + '</opencvLibraries>\n'
	config += '\t<otherIncludeDirs>' + unicode(otherIncludeDirs) + '</otherIncludeDirs>\n'
	config += '\t<otherLibrariesDirs>' + unicode(otherLibrariesDirs) + '</otherLibrariesDirs>\n'
	config += '\t<otherDllDirs>' + unicode(otherDllDirs) + '</otherDllDirs>\n'
	config += '\t<otherLibraries>' + unicode(otherLibraries) + '</otherLibraries>\n'
	config += '\t<compilerOptions>' + unicode(compilerOptions) + '</compilerOptions>\n'
	config += '\t<linkerOptions>' + unicode(linkerOptions) + '</linkerOptions>\n'
	config += '\t<localBlocksDirs>' + unicode(localBlocksDirs) + '</localBlocksDirs>\n'
	config += '\t<workingDirsPlace>' + unicode(workingDirsPlace) + '</workingDirsPlace>\n'
	config += '</starlingConfiguration>\n'

	# save configuration to file
	configFile = file(configurationFileName, 'w')
	configFile.write(config)
	configFile.close()

#----------------------------------------------------------------------

"""
Load configuration from file
"""
def loadConfiguration():
	global lirisvisionDir
	global opencvIncludeDirs
	global opencvLibrariesDirs
	global opencvDllDirs
	global opencvLibraries
	global otherIncludeDirs
	global otherLibrariesDirs
	global otherDllDirs
	global otherLibraries
	global compilerOptions
	global linkerOptions
	global localBlocksDirs
	global workingDirsPlace

	if not os.path.exists(configurationFileName):
		print 'Failed to read configuration file \'' + configurationFileName + '\'.'
		return # do nothing

	# read configuration file
	
	tree = xmltree.xmlTree()
	tree.load(configurationFileName)

	lirisvisionDir = tree.getText('./lirisvisionDir') or ''

	opencvIncludeDirs = tree.getText('./opencvIncludeDirs') or ''
	opencvLibrariesDirs = tree.getText('./opencvLibrariesDirs') or ''
	opencvDllDirs = tree.getText('./opencvDllDirs') or ''
	opencvLibraries = tree.getText('./opencvLibraries') or ''

	otherIncludeDirs = tree.getText('./otherIncludeDirs') or ''
	otherLibrariesDirs = tree.getText('./otherLibrariesDirs') or ''
	otherDllDirs = tree.getText('./otherDllDirs') or ''
	otherLibraries = tree.getText('./otherLibraries') or ''

	compilerOptions = tree.getText('./compilerOptions') or ''
	linkerOptions = tree.getText('./linkerOptions') or ''

	localBlocksDirs = tree.getText('./localBlocksDirs') or ''
	workingDirsPlace = tree.getText('./workingDirsPlace') or ''


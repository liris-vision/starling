# -*- coding: utf-8 -*-
#
# STARLING PROJECT 
# (based on HARPIA PROJECT)
#
# S2i - Intelligent Industrial Systems
# DAS - Automation and Systems Department
# UFSC - Federal University of Santa Catarina
# LIRIS - Laboratoire d'InfoRmatique en Image et Systèmes d'information 
#
# Copyright: 2006 - 2007 Luis Carlos Dill Junges (lcdjunges@yahoo.com.br), Clovis Peruchi Scotti (scotti@ieee.org),
#                        Guilherme Augusto Rutzen (rutzen@das.ufsc.br), Mathias Erdtmann (erdtmann@gmail.com) and S2i (www.s2i.das.ufsc.br)
#            2007 - 2009 Clovis Peruchi Scotti (scotti@ieee.org), S2i (www.s2i.das.ufsc.br)
#            2012 - 2015 Eric Lombardi (eric.lombardi@liris.cnrs.fr), LIRIS (liris.cnrs.fr), CNRS (www.cnrs.fr)
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

import lvExtensions
#i18n
import gettext


def setExperimentalMode(mode):
	"""
	Set experimental mode (True or False).
	"""
	global experimentalMode
	experimentalMode = mode


def loadBlocks():
	"""
	Load blocks definition from some directories.
	"""
	global block
	global experimentalMode
	
	block.clear()
	
	# add standard blocks
	lvExtensions.addBlocksFromDir(block, 'blocks.public', True)
	lvExtensions.addBlocksFromDir(block, 'blocks.private', True)
	lvExtensions.addBlocksFromDir(block, 'blocks.extra', True)

	# add local blocks
	localBlocksDirs = lvExtensions.getLocalBlocksDirs().split(';')
	localBlocksDirs = filter(lambda f: f != '', localBlocksDirs)
	for localDir in localBlocksDirs:
		lvExtensions.addBlocksFromDir(block, localDir)

	# add experimental blocks
	if experimentalMode:
		lvExtensions.addBlocksFromDir(block, 'blocks.experimental', True)
	'''
	# list id / block label
	for id in block.iterkeys():
		print id, block[id]['Label']
	'''


def buildGroups():
	"""
	Build blocks-groups list according to defined blocks.
	"""
	global block
	global groups

	groups.clear()
	for b in block.itervalues():
		groups[b['TreeGroup']] = []


APP='harpia'
DIR='/usr/share/harpia/po'
experimentalMode = False
block = {}
groups = {}
_ = gettext.gettext

gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)


#HERE: ADD TYPED ICONS for inputs and outputs
icons = {
    "IconInput":"images/input_unknown.png",
    "IconOutput":"images/output_unknown.png"
    }

typeIconsIn = {
	"cv::Mat":"images/input_Mat.png",
	"cv::Rect":"images/input_Rec.png",
	"cv::Point":"images/input_Pt.png",
	"cv::MatND":"images/input_MND.png",
	"std::vector < cv::KeyPoint >":"images/input_KPV.png",
	"std::vector < std::vector < cv::Point > >":"images/input_PVV.png",
	}

typeIconsOut = {
	"cv::Mat":"images/output_Mat.png",
	"cv::Rect":"images/output_Rec.png",
	"cv::Point":"images/output_Pt.png",
	"cv::MatND":"images/output_MND.png",
	"std::vector < cv::KeyPoint >":"images/output_KPV.png",
	"std::vector < std::vector < cv::Point > >":"images/output_PVV.png",
	}


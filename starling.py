#!/usr/bin/env python
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

#
# Starling launching script.
#

# Libraries 
import gobject
import gtk
import sys
import os
import argparse
import locale

from harpia import harpiagcfrontend
from harpia import lvExtensions


def main(argv):
	"""
	Parse the command line arguments, then start the application.
	"""

	# force locale to US to avoid (partial) translation of menus and buttons
	locale.setlocale(locale.LC_ALL, 'C')

	# avoid threads + gtk issues
	gobject.threads_init()

	# initializations
	os.environ['HARPIA_DATA_DIR'] = lvExtensions.harpia_data_dir
	batchMode = False
	experimentalMode = False
	userFiles = []

	# parse command line arguments
	argParser = argparse.ArgumentParser()
	argParser.add_argument('-b', '--batch', help='turn batch mode on', action='store_true')
	argParser.add_argument('-e', '--experimental', help='active experimental blocks', action='store_true')
	argParser.add_argument('-c', '--config-file', help='configuration file')
	args, unknown = argParser.parse_known_args()
	userFiles = unknown
	if args.batch and userFiles:
		batchMode = True
	if args.experimental:
		experimentalMode = True
	if args.config_file:
		lvExtensions.setConfigurationFileName(os.path.abspath(args.config_file))
	
	## initialize the frontend
	HarpiaFrontend = harpiagcfrontend.S2iHarpiaFrontend(userFiles, batchMode, experimentalMode)
	
	if not batchMode:
		HarpiaFrontend.show( center=0 )
		gtk.main()
	
	#----------------------------------------------------------------------

if __name__ == '__main__':
    main(sys.argv)
    
    #----------------------------------------------------------------------

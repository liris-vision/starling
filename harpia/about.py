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

import os
import gtk

## Implements the about window in the Frontend.
class About():
	"""
		The class implements the functionalities for showing the window and handles the singnals.
		Allow the user to see information about the Harpia Project.
	"""
	#----------------------------------------------------------------------

	def __init__( self ):
		"""
			Build the window UI.
    	"""
		self.m_sDataDir = os.environ['HARPIA_DATA_DIR']
		UIFilename = self.m_sDataDir+'gui/about.xml'
		windowName = 'about'
	
		# build gtk window
		builder = gtk.Builder()
		builder.add_from_file(UIFilename)
		self.gtkWindow = builder.get_object(windowName)

	#----------------------------------------------------------------------

	def __del__(self):
		# destroy the GTK window
		self.gtkWindow.destroy()

	#---------------------------------------------------------------------- 

	def show(self):
		"""
		Display the GTK window
		"""
		self.gtkWindow.show()

	#---------------------------------------------------------------------- 

# Debugging
#About = About()
#About.show()

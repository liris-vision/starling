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

# Imported Libraries
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


#i18n
import gettext
APP='harpia'
DIR='/usr/share/harpia/po'
_ = gettext.gettext
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)


#----------------------------------------------------------------------
## Block Properties base class
class S2iCommonProperties:
	"""
	This class implements the base properties for the blocks.
	In the Harpia current version, it only implements the color selection that is used to change the block back color and border color.
	"""

	#----------------------------------------------------------------------

	m_oColorSelectionDlg = None
	
	#----------------------------------------------------------------------
	
	def __init__( self, *args ):

		pass

	#----------------------------------------------------------------------

	def __del__(self):
		pass

	#----------------------------------------------------------------------

	def RunColorSelection(self,*args):
		"""
		This function creates a window for Color selection. This function is used to change the block back color and the border color.
		"""

		if self.m_oColorSelectionDlg == None:
			
			self.m_oColorSelectionDlg = Gtk.ColorSelectionDialog(_("Color selection"))

		t_oColorSelection = self.m_oColorSelectionDlg.colorsel
		
		t_oResponse = self.m_oColorSelectionDlg.run()

		if t_oResponse == Gtk.RESPONSE_OK:

			t_oColor = t_oColorSelection.get_current_color()

			self.m_oColorSelectionDlg.hide()

			return t_oColor

		else:
			self.m_oColorSelectionDlg.hide()

			return None
			
	#----------------------------------------------------------------------

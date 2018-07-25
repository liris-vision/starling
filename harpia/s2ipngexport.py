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

# Libraries
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

## Export the diagram to a .png file
class S2iPNGExport:
	"""
	This class implements the functionalities for exporting a blocks diagram in a .png file.
	"""

	#----------------------------------------------------------------------
	
	def Execute(self):
		"""
		This function gets the blocks chain and saves as a .png file by print screen.
		"""
		if Gtk.gtk_version < (2, 4, 0):
			t_oFilesel = Gtk.FileSelection('Exportar cadeia para imagem tipo .png')
		else:
			t_oFilesel = Gtk.FileChooserDialog(title='Exportar cadeia para imagem tipo .png',
											action=Gtk.FileChooserAction.SAVE,
											buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
														Gtk.STOCK_SAVE, Gtk.ResponseType.OK))


#Scotti
		if os.name == 'posix':
			t_oFilesel.set_current_folder(os.path.expanduser("~"))
#Scotti
		t_oFilter = Gtk.FileFilter()
		t_oFilter.set_name(_("PNG Image (*.png)"))
		t_oFilter.add_pattern("*.png")
		t_oFilesel.add_filter(t_oFilter)

		t_oFilter = Gtk.FileFilter()
		t_oFilter.set_name(_("Todos os arquivos"))
		t_oFilter.add_pattern("*")
		t_oFilesel.add_filter(t_oFilter)

		t_oResponse = t_oFilesel.run()
		
		t_sFilename = t_oFilesel.get_filename()
		
		t_oFilesel.destroy()
		
		print t_sFilename
		
		#if t_oResponse == Gtk.ResponseType.OK:
			
			#if t_sFilename and len(t_sFilename) > 0:
				
				#t_oView = diacanvas.view.get_active_view()

				#t_oWindow = t_oView.window
				
				#(x,y,t_nWidth,t_nHeight,t_nDepth) = t_oWindow.get_geometry()
				
				#t_oPixbuf = Gtk.gdk.Pixbuf(Gtk.gdk.COLORSPACE_RGB,False,8,t_nWidth,t_nHeight)
				
				#t_oBuffer = t_oPixbuf.get_from_drawable(t_oWindow, t_oView.get_colormap(),
														#0, 0, 0, 0, t_nWidth, t_nHeight)
				#t_oBuffer.save(t_sFilename, "png")
		
	#----------------------------------------------------------------------

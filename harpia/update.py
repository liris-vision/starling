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


# Imported class GladeWindow
from GladeWindow import  GladeWindow
import pygtk
import os
import gtk, gobject

#----------------------------------------------------------------------

## Implements the about window in the Frontend.
class Update( GladeWindow ):
	"""
	The class implements the functionalities for showing the window and handles the signals.
	Presents a beautiful look to update the appropriate files from the web.
		
	"""
	#----------------------------------------------------------------------

	def __init__( self ):
		"""
			Sets the Glade file where the about window is defined and Connects the
			signals and its handlers through GladeWindow __init__
    	"""

		## Get the file with the about window
		filename = 'glade/update.glade'
		## The widget list
		widget_list = [
			'ProgressBarUpdate', 'note_update', 'TextViewUpdate'
        	    ]
		handlers = ['on_update_destroy_event', 'on_ok_update_clicked']
		
		# The top three widget
		top_window = 'update'
		
		# Starts the Glade Window
		GladeWindow.__init__(self, filename, top_window, widget_list, handlers)

		# Add a timer callback to update the value of the progress bar
		self.timer = gobject.timeout_add (50, self.progress_timeout)

   	#	self.m_oPopen = popen2.Popen3('sh ../updhrp.sh')

		if os.name=="nt":		
			self.i,self.o = os.popen4('..\updhrp.bat')
		else:
			self.i,self.o = os.popen4('sh ../updhrp.sh')

		self.widgets['note_update'].set_current_page(0)
		self.widgets['ProgressBarUpdate'].pulse()
		self.widgets['ProgressBarUpdate'].pulse()
		self.widgets['ProgressBarUpdate'].pulse()

        #----------------------------------------------------------------------

	def GetPID(self):
		return os.getpid()
	# Update the value of the progress bar so that we get some movement
	def progress_timeout(self):
		self.widgets['ProgressBarUpdate'].pulse()

	 	ss= self.o.readline()

		print ss
		t_oTextBuffer = self.widgets['TextViewUpdate'].get_buffer()
		t_oTextBuffer.insert_at_cursor(ss)
		if ss == "":
			self.widgets['note_update'].set_current_page(1)			
			return False
#			os.popen('sh harpia.sh')
#			popen2.Popen3('python Harpia-Frontend.py')

		
		# As this is a timeout function, return TRUE so that it
		# continues to get called
		return True

	#----------------------------------------------------------------------

	def __del__(self):
		pass
	
	#---------------------------------------------------------------------- 

	def on_update_destroy_event(self,*args):
		gobject.source_remove(self.timer)
   	        self.timer = 0
   		gtk.main_quit()
		
	#---------------------------------------------------------------------- 

	def on_ok_update_clicked(self,*args):

		self.on_update_destroy_event()

	#---------------------------------------------------------------------- 
	
def main():
    gtk.main()
    return 0

if __name__ == "__main__":
    Update()
    main()

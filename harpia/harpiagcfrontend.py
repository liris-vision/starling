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
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
from gi.repository import GObject

#rm from uu import *
import sys
import os
import signal
from glob import glob

import xmltree

import commands

# Harpia

#import s2ipngexport
import s2idirectory

import GcdConnector
import GcdBlock
import GcDiagram

import s2iSessionManager
import TipOfTheDay
import about

import lvExtensions
import codegenerator

#i18n
import gettext
APP='harpia'
DIR='/usr/share/harpia/po'
_ = gettext.gettext
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)


#----------------------------------------------------------------------

#consts

BLOCK_SIZE_X = 100
BLOCK_SIZE_Y = 50

## Main window
class S2iHarpiaFrontend():
	"""
	Implements the main window frontend functionalities.
	This class connects all the signals in the main window and implements their functions.
	"""

	#----------------------------------------------------------------------

	def __init__( self, userFiles, batchModeOn, experimentalMode):
		"""
		Constructor. Initializes the GUI, connects the GTK signals, creates a dictionary for the Blocks and BlocksProperties and loads the configurations.
		"""
	
		GObject.threads_init()
		self.batchModeOn = batchModeOn
		s2idirectory.setExperimentalMode(experimentalMode)
		lvExtensions.loadConfiguration()

		self.exampleMenuItens = []
		
		self.m_sDataDir = os.environ['HARPIA_DATA_DIR']
		UIFilename = self.m_sDataDir+'gui/frontend.xml'

		widget_list = [
			'HarpiaFrontend',          'SearchEntry',          'SearchButton',
			'BlockDescription',        'WorkArea',
			'BlocksTreeView',          'StatusLabel',
			'ProcessImage',            'ProcessToolBar',       'CodeToolBar',
			'UpdateToolBar', 'toolbar1', 'examples_menu', 'fake_separator',
			'ConsoleTextView'
			]

		handlers = [
			'on_NewMenuBar_activate',          'on_OpenMenuBar_activate',
			'on_SaveMenuBar_activate',         'on_SaveASMenuBar_activate',
			'on_QuitMenuBar_activate',         'on_CutMenuBar_activate',
			'on_CopyMenuBar_activate',         'on_PasteMenuBar_activate',
			'on_DeleteMenuBar_activate',       'on_AboutMenuBar_activate',
			'on_NewToolBar_clicked',           'on_OpenToolBar_clicked',
			'on_SaveToolBar_clicked',          'on_ProcessToolBar_clicked',
			'on_StopToolBar_clicked',          'on_CodeToolBar_clicked',
			'on_ZoomOutToolBar_clicked',       'on_ZoomInToolBar_clicked',
			'on_SearchButton_clicked',         'on_BlocksTreeView_row_activated',
			'on_BlocksTreeView_cursor_changed','on_HarpiaFrontend_destroy',
			'on_ZoomDefaultToolBar_clicked',   'on_Preferences_clicked',
			'on_Export_clicked',               'on_CloseMenuBar_activate',
			'on_UpdateToolBar_clicked',        'on_tip_activate',
			'on_user_guide_activate',
			'on_developer_guide_activate',     'on_Reload_blocks_clicked',
			'on_UndoMenuBar_activate',         'on_RedoMenuBar_activate',
			'on_DebugMenuBar_activate'
			]

		topWindowName = 'HarpiaFrontend'
		
		# Initializes the GUI
		builder = Gtk.Builder()
		builder.add_from_file(UIFilename)
		builder.connect_signals(self)
		self.gtkTopWindow = builder.get_object(topWindowName)

		# build widgets list
		self.widgets = {}
		for w in widget_list:
			self.widgets[w] = builder.get_object(w)
		
		self.widgets['HarpiaFrontend'].set_icon_from_file(self.m_sDataDir+"images/starling.jpg")

		self.g_sTreeViewPath = "0,0"

		self.m_nStatus = 0
		
		self.SaveAs = False
		
		#Member Diagram references
		self.m_oGcDiagrams = {}
		
		self.m_oSessionIDs = {}

		self.m_oCopyBuffer = (-1, -1) #tuple (fromPage, [listOfBlocks]) ...listOfConns?

		self.m_nCurrentIDSession = None
		
		self.LoadExamplesMenu()
		
		self.setBlocksMenu()

		self.on_NewToolBar_clicked() #creating blank page
		
		#Tip of The Day code
		tipOfTheDayWind = TipOfTheDay.TipOfTheDay()
		tipOfTheDayWind.run()

		# catch SIGTERM signal to destroy subprocesses if starling is killed 
		signal.signal(signal.SIGTERM, self.sigTERM)

		# open files automatically
		if self.batchModeOn:
			# in batchMode, open first user file and run it
			print "Running in batch mode ..."
			self.openFile(userFiles[0])
			# run project
			self.on_ProcessToolBar_clickedIneer()
			# release resources and quit
			self.on_QuitMenuBar_activate()
			#self.top_window.emit("destroy")
			#Gtk.window().emit("destroy")
		else:
			# open all user files given on command line
			for fileName in userFiles :
				self.openFile(fileName)

		# initialize block search
		self.lastSearchRequest = ''
		self.lastSearchResults = []
		self.lastSearchResponse = None

		# initialize console text view
		self.consoleTextView = self.widgets['ConsoleTextView']
		color_black = Gdk.RGBA(0,0,0).to_color()
		self.consoleTextView.modify_base(Gtk.StateType.NORMAL, color_black)
		color_white = Gdk.RGBA(1,1,1).to_color()
		self.consoleTextView.modify_text(Gtk.StateType.NORMAL, color_white)
		self.captureStdout()
		
	#----------------------------------------------------------------------

	def __del__(self):
		pass

	#----------------------------------------------------------------------

	def show(self, center=1):
		"""
		Display the top_window widget
		"""
		if center:
			self.gtkTopWindow.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
		else:
			self.gtkTopWindow.set_position(Gtk.WindowPosition.NONE)
		self.gtkTopWindow.show()

	#---------------------------------------------------------------------- 

	def setBlocksMenu(self):
		"""
		Inserts the blocks in the BlocksTree.
		"""
		
		# refresh blocks list
		self.setBlocks()

		# build GTK TreeStore, to store blocks list for the menu 

		t_oTreeStore = Gtk.TreeStore(GObject.TYPE_STRING)

		# self.Blocks.keys() is a list of blocks-group
		# = [ 'Filtering', 'Features' ... ]
		for t_sItem in sorted(self.Blocks.keys()):
			t_oParent = t_oTreeStore.append(None, [t_sItem])
			# self.Blocks[t_sItem] is the list of block labels of
			# the group t_sItem
			# self.Blocks['Filetring']=['Morphology',...]
			for blockLabel in sorted(self.Blocks[t_sItem]):
				t_oTreeStore.append(t_oParent, [blockLabel])

		# display menu

		self.widgets['BlocksTreeView'].set_model(t_oTreeStore)

		# create the column and set drag&drop just one time 
		if not self.widgets['BlocksTreeView'].get_column(0):

			# create column

			t_oTextRender = Gtk.CellRendererText()
			t_oTextRender.set_property( 'editable', False )
			t_oColumn = Gtk.TreeViewColumn(_("Available Blocks"), t_oTextRender, text=0)
			self.widgets['BlocksTreeView'].append_column( t_oColumn )

			# set drag&drop

			#		TARGETS = [
			#			('MY_TREE_MODEL_ROW', Gtk.TARGET_SAME_WIDGET, 0),
			#			('text/plain', 0, 1),
			#			('TEXT', 0, 2),
			#			('STRING', 0, 3),
			#			]

			#TODO-fix-beg
			##drag......
			#self.widgets['BlocksTreeView'].enable_model_drag_source( 
			#	Gdk.ModifierType.BUTTON1_MASK,
			#	[('text/plain', Gtk.TARGET_SAME_APP, 1)],
			#	Gtk.gdk.ACTION_DEFAULT | Gtk.gdk.ACTION_COPY)
			#self.widgets['BlocksTreeView'].connect( "drag-data-get",
			#	self.drag_data_get_cb)

			##........'n'drop
			#self.widgets['WorkArea'].connect( "drag_data_received",
			#	self.drag_data_received)
			#self.widgets['WorkArea'].drag_dest_set(
			#	Gtk.DEST_DEFAULT_MOTION | Gtk.DEST_DEFAULT_HIGHLIGHT |
			#		Gtk.DEST_DEFAULT_DROP,
			#	[('text/plain', Gtk.TARGET_SAME_APP, 1)],
			#	Gtk.gdk.ACTION_DEFAULT | Gtk.gdk.ACTION_COPY)
			#TODO-fix-end

		#ELtry use GtkTreeView internal search
		#ELself.widgets['BlocksTreeView'].set_enable_search(True)
		#ELself.widgets['BlocksTreeView'].set_search_column(0)


	def drag_data_received(self, widget, context, x, y, selection, targetType,time):
		self.on_BlocksTreeView_row_activated_pos( self.widgets['BlocksTreeView'], self.g_sTreeViewPath, 0, x-5, y-30)
		
		return

	#----------------------------------------------------------------------

	def drag_data_get_cb(self, treeview, context, selection, target_id,etime):
		treeselection = treeview.get_selection()
		model, iterac = treeselection.get_selected()
		self.g_sTreeViewPath = model.get_path(iterac)
		selection.set('text/plain', 8, "test")
		#necessary in order to the notebook receive the drag:
		return

	def make_pb(self, tvcolumn, cell, model, iter):
		stock = model.get_value(iter, 1)
		pb = self.widgets["BlocksTreeView"].render_icon(stock, Gtk.ICON_SIZE_MENU, None)
		cell.set_property('pixbuf', pb)
		return


	def on_NewMenuBar_activate(self, *args):		

		self.on_NewToolBar_clicked( )

	#----------------------------------------------------------------------

	def on_OpenMenuBar_activate(self, *args):

		self.on_OpenToolBar_clicked()

	#----------------------------------------------------------------------

	def on_SaveMenuBar_activate(self, *args):

		self.on_SaveToolBar_clicked()

	#----------------------------------------------------------------------

	def on_SaveASMenuBar_activate(self, *args):

		self.SaveAs = True
		
		self.on_SaveToolBar_clicked()

	#----------------------------------------------------------------------

	def on_QuitMenuBar_activate(self, *args):
		"""
		Callback function that destroys the windows when quit menu bar clicked.
		"""
		self.on_HarpiaFrontend_destroy()

	#----------------------------------------------------------------------

	def on_tip_activate(self, *args):
		# enable tip display
		tipOfTheDayWind = TipOfTheDay.TipOfTheDay()
		tipOfTheDayWind.GenerateBlankConf()
		# display tip
		tipOfTheDayWind = TipOfTheDay.TipOfTheDay()
		tipOfTheDayWind.run()
	
	#ELrm def on_reset_tip_activate(self, *args):
	#ELrm 	tipOfTheDayWind = TipOfTheDay.TipOfTheDay()
	#ELrm 	tipOfTheDayWind.GenerateBlankConf()

	def on_user_guide_activate(self, *args):
		lvExtensions.openDocumentation('user')

	def on_developer_guide_activate(self, *args):
		lvExtensions.openDocumentation('developer')

	def on_CutMenuBar_activate(self, *args):
		"""
		Callback function called when CutMenuBar is activated. Copy the block an removes from the diagram.
		"""
		print "Cut functionality not implemented yet"
		
	#----------------------------------------------------------------------

	def on_CopyMenuBar_activate(self, *args):
		"""
		Callback function called when CopyMenuBar is activated. Just copy the block.
		"""
		if self.m_oGcDiagrams.has_key( self.widgets['WorkArea'].get_current_page() ): 
			t_oGcDiagram = self.m_oGcDiagrams[self.widgets['WorkArea'].get_current_page()]

		# store tuple (pageN, blockN)
		self.m_oCopyBuffer = ( self.widgets['WorkArea'].get_current_page(), t_oGcDiagram.GetBlockOnFocus() ) 
		#print 'DBG block', self.m_oCopyBuffer, 'copied.'
		#print 'DBG copied block props =', t_oGcDiagram.m_oBlocks[self.m_oCopyBuffer[1]].PrintXML()

	#----------------------------------------------------------------------

	def on_PasteMenuBar_activate(self, *args):
		"""
		Callback function called when PasteMenuBar is activated.
		Paste the copied block(s) in the diagram.
		"""
		# self.m_oCopyBuffer contains the previously copied block
		# self.m_oCopyBuffer[0] = notebook widget tab identifier
		# self.m_oCopyBuffer[1] = block identifier

		if self.m_oCopyBuffer[0] == -1: #nothing copied
			return
		
		#print "pasting"
		
		if self.m_oGcDiagrams.has_key( self.widgets['WorkArea'].get_current_page() ): 
			t_oGcDiagram = self.m_oGcDiagrams[self.widgets['WorkArea'].get_current_page()]
			#print "destination exists"
			
			if self.m_oGcDiagrams.has_key( self.m_oCopyBuffer[0] ):
				t_oFromDiagram = self.m_oGcDiagrams[self.m_oCopyBuffer[0]]
				#print "source exists"
				
				if t_oFromDiagram.m_oBlocks.has_key(self.m_oCopyBuffer[1]):
					# add new block of right type
					newBlockId = t_oGcDiagram.InsertBlock(t_oFromDiagram.m_oBlocks[self.m_oCopyBuffer[1]].m_nBlockType)
					# copy properties (aka parameters, not position) of copied block
					# to new block
					t_oGcDiagram.m_oBlocks[newBlockId].SetPropertiesXML_nID(t_oFromDiagram.m_oBlocks[self.m_oCopyBuffer[1]].GetPropertiesXML())
		
	#----------------------------------------------------------------------

	def on_DeleteMenuBar_activate(self, *args):
		"""
		Callback function called when DeleteMenuBar is activated. Deletes the selected item.
		"""
		if self.m_oGcDiagrams.has_key( self.widgets['WorkArea'].get_current_page() ): 
			t_oGcDiagram = self.m_oGcDiagrams[self.widgets['WorkArea'].get_current_page()]
			blockId = t_oGcDiagram.GetBlockOnFocus()
			if t_oGcDiagram.m_oBlocks.has_key(blockId):
				t_oGcDiagram.DeleteBlock(blockId)
		
	#----------------------------------------------------------------------

	def on_UndoMenuBar_activate(self, *args):
		"""
		Callback funtion called when Undo menu entry is activated.
		Undo the last change.
		"""
		if self.m_oGcDiagrams.has_key( self.widgets['WorkArea'].get_current_page() ): 
			t_oGcDiagram = self.m_oGcDiagrams[self.widgets['WorkArea'].get_current_page()]
			t_oGcDiagram.undo()

	#----------------------------------------------------------------------

	def on_RedoMenuBar_activate(self, *args):
		"""
		Callback funtion called when Redo menu entry is activated.
		Redo the last change.
		"""
		if self.m_oGcDiagrams.has_key( self.widgets['WorkArea'].get_current_page() ): 
			t_oGcDiagram = self.m_oGcDiagrams[self.widgets['WorkArea'].get_current_page()]
			t_oGcDiagram.redo()
			
	#----------------------------------------------------------------------

	def on_DebugMenuBar_activate(self, *args):
		"""
		Callback funtion called when Ctrl+D is pressed.
		Display debug informations in the terminal.
		"""
		if self.m_oGcDiagrams.has_key( self.widgets['WorkArea'].get_current_page() ): 
			t_oGcDiagram = self.m_oGcDiagrams[self.widgets['WorkArea'].get_current_page()]
			t_oGcDiagram.displayDebugInfos()
			
	#----------------------------------------------------------------------

	def on_AboutMenuBar_activate(self, *args):
		"""
		Callback function called when AboutMenuBar is activated. Loads the about window.
		"""
		self.about = about.About()
		self.about.show()

	#----------------------------------------------------------------------

	def on_NewToolBar_clicked(self, *args):
		"""
		Callback function called when NewToolBar is clicked. Creates a new tab with an empty diagram.
		"""
		
		#maybe pass to a s2iView base class
		t_oNewDiagram = GcDiagram.GcDiagram()#created new diagram

		scrolled_win = Gtk.ScrolledWindow()
		scrolled_win.set_shadow_type(Gtk.ShadowType.IN)
		scrolled_win.add(t_oNewDiagram)
		scrolled_win.show_all()
		
		t_nCurrentPage = self.widgets['WorkArea'].get_current_page()

		#tab label
		t_oLabel = Gtk.Label(_("Unnamed ") + str(t_nCurrentPage+1) + "[*]" )
		
		self.widgets['WorkArea'].set_show_tabs( True )
		self.widgets['WorkArea'].append_page(scrolled_win, t_oLabel)
		
		t_nSelectedPage = self.widgets['WorkArea'].get_n_pages()-1
		self.widgets['WorkArea'].set_current_page( t_nSelectedPage )

		self.m_oGcDiagrams[self.widgets['WorkArea'].get_current_page()] = t_oNewDiagram

		#self.ShowGrid( self.m_bShowGrid )

		#self.SetGridInterval( self.m_nGridInterval )
		
	#----------------------------------------------------------------------

	def on_OpenToolBar_clicked(self, *args):
		#Opens a dialog for file selection and opens the file.

		t_oDialog = Gtk.FileChooserDialog(_("Open..."),
										None,
										Gtk.FILE_CHOOSER_ACTION_OPEN,
										(Gtk.STOCK_CANCEL, Gtk.RESPONSE_CANCEL,
										Gtk.STOCK_OPEN, Gtk.RESPONSE_OK))

		t_oDialog.set_default_response(Gtk.RESPONSE_OK)

		if os.name == 'posix':
			t_oDialog.set_current_folder(os.path.expanduser("~"))

		t_oFilter = Gtk.FileFilter()
		t_oFilter.set_name(_("All Archives"))
		t_oFilter.add_pattern("*")
		t_oDialog.add_filter(t_oFilter)

		t_oFilter = Gtk.FileFilter()
		t_oFilter.set_name(_("Harpia Files"))
		t_oFilter.add_pattern("*.hrp")
		t_oDialog.add_filter(t_oFilter)

		t_oResponse = t_oDialog.run()
	
		if t_oResponse == Gtk.RESPONSE_OK:
			fileName = t_oDialog.get_filename()
			t_oDialog.destroy()
			self.openFile(fileName)
		else:
			t_oDialog.destroy()
				
	#----------------------------------------------------------------------

	def on_SaveToolBar_clicked(self, *args):
		#Opens a dialog for file and path selection. Saves the file and if necessary updates the tab name.
		
		if self.m_oGcDiagrams.has_key( self.widgets['WorkArea'].get_current_page() ): 

			t_oGcDiagram = self.m_oGcDiagrams[self.widgets['WorkArea'].get_current_page()]
		
			if t_oGcDiagram.GetFilename() is None or self.SaveAs:
				self.SaveAs = False
			
				t_oDialog = Gtk.FileChooserDialog(_("Save..."),
												None,
												Gtk.FILE_CHOOSER_ACTION_SAVE,
												(Gtk.STOCK_CANCEL, Gtk.RESPONSE_CANCEL,
												Gtk.STOCK_SAVE, Gtk.RESPONSE_OK))
			
				t_oDialog.set_default_response(Gtk.RESPONSE_OK)

				if os.name == 'posix':
					t_oDialog.set_current_folder(os.path.expanduser("~"))

				t_oFilter = Gtk.FileFilter()
				t_oFilter.set_name(_("All Archives"))
				t_oFilter.add_pattern("*")
				t_oDialog.add_filter(t_oFilter)

				t_oFilter = Gtk.FileFilter()
				t_oFilter.set_name(_("Harpia Files"))
				t_oFilter.add_pattern("*.hrp")
				t_oDialog.add_filter(t_oFilter)
			
				t_oResponse = t_oDialog.run()
				if t_oResponse == Gtk.RESPONSE_OK:
					t_oGcDiagram.SetFilename( t_oDialog.get_filename() )
					
				t_oDialog.destroy()

			if t_oGcDiagram.GetFilename() is not None:
				if len(t_oGcDiagram.GetFilename())>0:
					t_oGcDiagram.Save( )
					# update tab name
					t_nCurrentPage = self.widgets['WorkArea'].get_current_page()
					self.setTabName(t_nCurrentPage, t_oGcDiagram.GetFilename())
					
	#----------------------------------------------------------------------

	def UpdateStatus(self, a_nStatus):
		"""
		Receives a status and shows in the StatusBar.
		"""

		#a_nStatus
		#0 - Connecting...
		#1 - could not connect to server
		#2 - Processing...        
		#3 - could not create a new session ID
		#4 - could not send images to server
		#5 - could not send process file to server
		#6 - Process error
		#7 - Process complete
		#8 - Nothing to process
		#9 - Save error
		#10 - Code retrieved

		self.m_nStatus = a_nStatus		

		t_oStatusMessage = { 0: _("Processing ... (press ESC to stop, SPACE to pause)"),#cpscotti.. connecting nao tem nada a ver com a ideia... tah outdated
							1: _("Could not connect to server"),
							2: _("Processing(2)..."),
							3: _("Could not create a new session ID"),
							4: _("Could not send images to server"),
							5: _("Could not send process file to server"),
							6: _("Processing error"),
							7: _("Processing complete"),
							8: _("Nothing to process"),
							9: _("Save error"),
							10: _("Code Saved")}

		#if a_nStatus == 7 or a_nStatus == 10:
			#self.widgets['ProcessImage'].set_from_stock( Gtk.STOCK_YES, Gtk.ICON_SIZE_MENU)
		#else:
			#self.widgets['ProcessImage'].set_from_stock( Gtk.STOCK_NO, Gtk.ICON_SIZE_MENU  )
			
		self.widgets['StatusLabel'].set_text(t_oStatusMessage[a_nStatus])
		
		while Gtk.events_pending():
			Gtk.main_iteration_do(False)

	#----------------------------------------------------------------------
	def SetStatusMessage(self, a_sStatus, a_bGood):
		"""
		Receives a status message and shows it in the StatusBar.
		"""
		#print a_bGood
		if a_bGood:
			self.widgets['ProcessImage'].set_from_stock( Gtk.STOCK_YES, Gtk.ICON_SIZE_MENU  )
		else:
			self.widgets['ProcessImage'].set_from_stock( Gtk.STOCK_NO, Gtk.ICON_SIZE_MENU  )
		self.widgets['StatusLabel'].set_text(a_sStatus)
		while Gtk.events_pending():
			Gtk.main_iteration_do(False)

	#----------------------------------------------------------------------

	# Executed when Run button is clicked ...
	def on_ProcessToolBar_clickedIneer(self):
		t_nPage = self.widgets['WorkArea'].get_current_page()
		t_bIsLive = False
		if self.m_oGcDiagrams.has_key(t_nPage) :
			self.UpdateStatus(0)

			t_oGcDiagram = self.m_oGcDiagrams[t_nPage]
			t_oProcessXML = xmltree.xmlTree()
			t_oProcessXML.fromString("<harpia>" + str(t_oGcDiagram.GetProcessChain()) + "</harpia>")
			assert t_oProcessXML.isValid(), 'invalid process chain: %r'

			if t_oProcessXML.findAttributes('./properties/block'):
				# if harpia/properties is not empty

				#cpscotti standalone!!!
				t_lsProcessChain = []#lista pra n precisar ficar copiando prum lado e pro otro o xml inteiro
				t_lsProcessChain.append(t_oProcessXML.toString())
				
				workingDir = t_oGcDiagram.getDirName()
				t_Sm = s2iSessionManager.s2iSessionManager(workingDir)
				
				## pegando o novo ID (criado pela s2iSessionManager) e passando para o s2idiagram
				t_oGcDiagram.SetSessionManager(t_Sm)
				t_oGcDiagram.SetIDBackendSession(t_Sm.m_sSessionId)
				
				#step sempre sera uma lista.. primeiro elemento eh uma mensagem, segundo eh o erro.. caso exista erro.. passar para o s2idiagram tb!
				t_oGcDiagram.SetErrorLog('')
				t_bEverythingOk = True
				t_Sm.NewInstance(self.batchModeOn, t_lsProcessChain)
					
		#falta pegar o retorno!!!!!!
		self.UpdateStatus(7)

	def on_ProcessToolBar_clicked(self, *args):
		"""
		Callback function called when ProcessToolBar is clicked. Starts communication with Backend and process the Chain.
		"""
		self.UpdateStatus(0)
		self.widgets['ProcessToolBar'].set_sensitive(False)
		self.widgets['CodeToolBar'].set_sensitive(False)
		
		#######################################################################
		# We have two choices here, we could run with delays so all the numb info is displayed in the GUI
		#id2 = GObject.timeout_add(200,self.on_ProcessToolBar_clickedGenerator(self).next) #remember to uncomment the yield at line 842
		#
		# OORR
		# we could just iterate through it as fast as possible
		self.on_ProcessToolBar_clickedIneer()
		self.widgets['ProcessToolBar'].set_sensitive(True)
		self.widgets['CodeToolBar'].set_sensitive(True)
		
	def on_StopToolBar_clicked(self, *args):
		"""
		Callback function called when StopToolBar is clicked. Stops current diagram processing.
		"""
		t_nPage = self.widgets['WorkArea'].get_current_page()
		self.m_oGcDiagrams[t_nPage].stopSubProcess()

	def on_CodeToolBar_clickedIneer(self):
		t_nPage = self.widgets['WorkArea'].get_current_page()
		if not self.m_oGcDiagrams.has_key( t_nPage ):
			self.widgets['CodeToolBar'].set_sensitive(True)
			#message
			self.SetStatusMessage(_("Could not find current diagram"), 1)
			return

		# open C code in text editor 
		codegenerator.editSourceCode(self.m_oGcDiagrams[t_nPage].getDirName())

	def on_CodeToolBar_clicked(self, *args):
		self.widgets['ProcessToolBar'].set_sensitive(False)
		self.widgets['CodeToolBar'].set_sensitive(False)
	#	self.on_ProcessToolBar_clicked(self, *args)
		
		#self.SetStatusMessage(_("Saving the last generated code"), 0)
		if self.m_nStatus != 7:
			self.on_ProcessToolBar_clicked()
		
		self.on_CodeToolBar_clickedIneer()
		self.widgets['ProcessToolBar'].set_sensitive(True)
		self.widgets['CodeToolBar'].set_sensitive(True)
		#id3 = GObject.timeout_add(1000,self.on_CodeToolBar_clickedGenerator(self, *args).next)


	#----------------------------------------------------------------------

	def on_ZoomOutToolBar_clicked(self, *args):
		"""
		Just ZoomOut the current page. Exponentialy, thus preventing the "0 pixels_per_unit bug"
		"""
		t_nPage = self.widgets['WorkArea'].get_current_page()
		if self.m_oGcDiagrams.has_key( t_nPage ) :
			t_oGcDiagram = self.m_oGcDiagrams[ t_nPage ]
			t_oGcDiagram.ZoomOut()
	#----------------------------------------------------------------------

	def on_ZoomInToolBar_clicked(self, *args):
		"""
		Just ZoomIn the current view.
		"""
		t_nPage = self.widgets['WorkArea'].get_current_page()
		if self.m_oGcDiagrams.has_key( t_nPage ) :
			t_oGcDiagram = self.m_oGcDiagrams[ t_nPage ]
			t_oGcDiagram.ZoomIn()

	#----------------------------------------------------------------------

	def on_ZoomDefaultToolBar_clicked(self, *args):
		"""
		Just back to the default zoom view.
		"""
		t_nPage = self.widgets['WorkArea'].get_current_page()
		if self.m_oGcDiagrams.has_key( t_nPage ) :
			t_oGcDiagram = self.m_oGcDiagrams[ t_nPage ]
			t_oGcDiagram.ZoomOrig()

	#----------------------------------------------------------------------

	def on_UpdateToolBar_clicked(self, *args):
		"""
		Callback function called when Update is clicked. Update this Harpia version with the last in the server.
		"""
		pass

		#t_oCloseHarpia = Gtk.Dialog(title=_("Harpia Update"), parent=self.widgets['HarpiaFrontend'], flags=Gtk.DIALOG_MODAL, buttons=('Gtk-yes',Gtk.RESPONSE_YES,'Gtk-no',Gtk.RESPONSE_NO) )

		#t_oLabel=Gtk.Label(_("\nHarpia must be closed in order to update.\nDo you want to exit and continue update?\n"))

		#t_oCloseHarpia.set_border_width(5)
		
		#t_oCloseHarpia.vbox.pack_start(t_oLabel, True, True, 0)


		#t_oLabel.show()
		
		#t_nResponse=t_oCloseHarpia.run()

		#if t_nResponse == Gtk.RESPONSE_YES:

			#import xmlrpclib

			#t_oServer = xmlrpclib.Server('http://localhost:8376',allow_none=True)

			#if os.name=="nt":
				#t_oServer.StartApplication(os.getenv('HARPIAINSTALLDIR')+'/lib/python24/pythonw.exe', 'HRPUpdate.py')		

				##Here we have a bug. See s2iharpiasuperserver.py RegisterPID method for explanation.
				#t_oServer.StopApplication(os.getenv('HARPIAINSTALLDIR')+'/lib/python24/pythonw.exe', 'Harpia-Frontend.py')
			#else:
				#t_oServer.StartApplication('/usr/bin/python', 'HRPUpdate.py')		

				#t_oServer.StopApplication('/usr/bin/python', 'Harpia-Frontend.py')

		#else:
			#t_oCloseHarpia.destroy()
		

	#----------------------------------------------------------------------
	
	def on_Preferences_clicked(self, *args):
		"""
		Callback function called when Preferences is clicked. Loads the preferences window.
		"""
		from harpia import preferenceswindow
		prefs = preferenceswindow.PreferencesWindow(self)

	#----------------------------------------------------------------------

	def on_Export_clicked(self, *args):
		"""
		Callback function called when Export is clicked. Calls the Execute function in s2ipngexport class, that saves a blocks diagram in a .png file.
		"""

		if self.m_oGcDiagrams.has_key( self.widgets['WorkArea'].get_current_page() ): 

			t_oGcDiagram = self.m_oGcDiagrams[self.widgets['WorkArea'].get_current_page()]
			t_oDialog = Gtk.FileChooserDialog(_("Export Diagram to PNG..."),
											None,
											Gtk.FILE_CHOOSER_ACTION_SAVE,
											(Gtk.STOCK_CANCEL, Gtk.RESPONSE_CANCEL,
											Gtk.STOCK_SAVE, Gtk.RESPONSE_OK))
		
			t_oDialog.set_default_response(Gtk.RESPONSE_OK)

			if os.name == 'posix':
				t_oDialog.set_current_folder(os.path.expanduser("~"))

			t_oFilter = Gtk.FileFilter()
			t_oFilter.set_name(_("Png files"))
			t_oFilter.add_pattern("*.png")
			t_oDialog.add_filter(t_oFilter)
			
			t_oResponse = t_oDialog.run()
			filename = t_oDialog.get_filename()
			
			if filename and not filename.endswith(".png"):
				filename += ".png"
			t_oDialog.destroy()
			
			if t_oResponse == Gtk.RESPONSE_OK and filename:
				t_oGcDiagram.Export2Png(filename)
	
	#----------------------------------------------------------------------

	def on_SearchButton_clicked(self, *args):
		"""
		Callback function called when SearchButton is clicked. Search for block and shows it. If one search is repeated, the next result is shown.
		"""
		# get the request
		searchRequest = self.widgets['SearchEntry'].get_text().lower()

		# if request is an empty string ...
		if not searchRequest:
			self.lastSearchRequest = searchRequest
			self.lastSearchResults = []
			self.lastSearchResponse = None
			return

		# do search only if it's different of last one
		if searchRequest != self.lastSearchRequest:
			# new request:
			# search matching names in all blocks-group names 
			# and in all block names, and build the results list
			self.lastSearchRequest = searchRequest
			self.lastSearchResults = []
			self.lastSearchResponse = None
			for classIndex, className in enumerate(sorted(self.Blocks.keys())):
				classNameLow = className.lower()

				# search in blocks-group names
				if searchRequest in classNameLow:
					self.lastSearchResults.append((classIndex, None))

				# search in block names
				for blockIndex, blockName in enumerate(sorted(self.Blocks[className])):
					blockNameLow = blockName.lower()
					if searchRequest in blockNameLow:
						self.lastSearchResults.append((classIndex, blockIndex))

		# select response
		if self.lastSearchResponse is None:
			# this is a new search
			if self.lastSearchResults:
				# results list is not empty, select the first one
				self.lastSearchResponse = 0
			# if results list is empty, self.lastSearchResponse 
			# contains None
		else:
			# the search is the same as last time, 
			# select the next result in results list
			self.lastSearchResponse += 1
			if self.lastSearchResponse > len(self.lastSearchResults)-1:
				self.lastSearchResponse = 0
				
		# display response

		if self.lastSearchResponse is None:
			# no response
			return

		response = self.lastSearchResults[self.lastSearchResponse]
			# response is a pair (classIndex, blockIndex)
			# if blockIndex == None, then it's a blocks-group name
			# else it's a block name
		if response[1] is None:
			# response is a blocks-group name
			self.widgets['BlocksTreeView'].collapse_all()
			self.widgets['BlocksTreeView'].expand_row(response[0], True)
			self.widgets['BlocksTreeView'].set_cursor(response[0])
		else:
			# response is a block name
			self.widgets['BlocksTreeView'].collapse_all()
			self.widgets['BlocksTreeView'].expand_to_path(response)
			self.widgets['BlocksTreeView'].set_cursor(response)

	#------------------------------------------------------------------
	#VERY WEIRD!!!!!
	#YES, I TRYED making on_BlocksTreeView_row_activated just calling on_BlocksTreeView_row_activated_pos(...,0,0) but it didn't worked.. 

	def on_BlocksTreeView_row_activated(self, treeview, path, column):
		"""
		Callback function called when BlocksTreeView_row is activated. Loads the block in the diagram.
		"""
		t_oTreeViewModel = treeview.get_model()
		t_sBlockName = t_oTreeViewModel.get_value( t_oTreeViewModel.get_iter(path), 0 )

		if t_sBlockName not in self.Blocks.keys():
			t_nPage = self.widgets['WorkArea'].get_current_page()

			if self.m_oGcDiagrams.has_key( t_nPage ):
				t_oCurrentGcDiagram = self.m_oGcDiagrams[ t_nPage ]
				t_nBlockType = -1

				for t_oBlockTypeIter in s2idirectory.block.keys():
					if s2idirectory.block[int(t_oBlockTypeIter)]["Label"]==t_sBlockName:
						t_nBlockType = t_oBlockTypeIter
						break
				t_oCurrentGcDiagram.InsertBlock( t_nBlockType )
	

	def on_BlocksTreeView_row_activated_pos(self, treeview, path, column, x, y):
		"""
		Callback function called when BlocksTreeView_row is activated. 
		Loads the block in the diagram.
		"""
		t_oTreeViewModel = treeview.get_model()
		t_sBlockName = t_oTreeViewModel.get_value( t_oTreeViewModel.get_iter(path), 0 )

		if t_sBlockName not in self.Blocks.keys():
			t_nPage = self.widgets['WorkArea'].get_current_page()

			if self.m_oGcDiagrams.has_key( t_nPage ):
				t_oCurrentGcDiagram = self.m_oGcDiagrams[ t_nPage ]
				t_nBlockType = -1

				for t_oBlockTypeIter in s2idirectory.block.keys():
					if s2idirectory.block[int(t_oBlockTypeIter)]["Label"]==t_sBlockName:
						t_nBlockType = t_oBlockTypeIter
						break
				t_oCurrentGcDiagram.InsertBlock( t_nBlockType , x, y)


				
	#----------------------------------------------------------------------   
		
	def on_BlocksTreeView_cursor_changed( self, treeview ):
		"""
		Callback function called when BlocksTreeView cursor changed. Updates the Description.
		"""
				
		t_oTreeViewSelection = treeview.get_selection()
		
		(t_oTreeViewModel, t_oTreeViewIter) = t_oTreeViewSelection.get_selected()

		if t_oTreeViewIter != None:
		
			t_sBlockName = t_oTreeViewModel.get_value( t_oTreeViewIter, 0 )

			for x in s2idirectory.block:
				if s2idirectory.block[x]["Label"] == t_sBlockName :
					t_oTextBuffer = Gtk.TextBuffer()
					t_oTextBuffer.set_text(s2idirectory.block[x]["Description"])
					self.widgets['BlockDescription'].set_buffer(t_oTextBuffer)
					break

	#----------------------------------------------------------------------
	
	def OnEvent( self, a_oView, a_oEvent ):
		print "OnEvent( self, a_oView, a_oEvent ) not implemented (it is distributed among diagram objects)"

	#----------------------------------------------------------------------
	
	def fixBlockPositions(self): #this function removes all the blocks of unreacheable states
		print "fixBlockPositions not implemented (it is distributed among diagram objects)"

	#----------------------------------------------------------------------

	def on_HarpiaFrontend_destroy( self, *args):
		"""
		Destroys the Harpia Window.
		"""
		#DBG sys.__stdout__.write('*** on_HarpiaFrontend_destroy() ***\n')
		# close tabs one by one 
		abort = False
		while self.m_oGcDiagrams:
			if not self.CloseCurrentTab():
				abort = True
				break

		if not abort and not self.batchModeOn:
			# quit
			Gtk.main_quit()

		return True  # required for 'delete-event' signal processing
		
	#----------------------------------------------------------------------

	def __CopyBlock(self,a_oBlock):
		"""
		Receives a block and copy.
		"""
		print "Copy not implemented"

	#----------------------------------------------------------------------

	def on_CloseMenuBar_activate(self,*args):
		"""
		Callback funtion called when CloseMenuBar is activated. Close the current diagram tab.
		"""
		self.CloseCurrentTab()

	#----------------------------------------------------------------------

	def CloseCurrentTab(self):
		"""
		Close the current diagram tab.
		Returns True if successfully closed, else False (if canceled by user).
		"""
		t_nCurrentTabIndex = self.widgets['WorkArea'].get_current_page()
		if t_nCurrentTabIndex < 0:
			return True # no tab

		# check if diagram has been modified
		if self.m_oGcDiagrams[t_nCurrentTabIndex].HasChanged():
			# the diagram has changed since last save, ask for confirmation 
			dialog = Gtk.MessageDialog(self.widgets['HarpiaFrontend'], Gtk.DIALOG_MODAL, Gtk.MESSAGE_WARNING, Gtk.BUTTONS_OK_CANCEL, "The current processing chain has been modified. Do you really want to close WITHOUT saving ?")
			response = dialog.run()
			dialog.destroy()
			if response == Gtk.RESPONSE_CANCEL:
				return False# abort closing

		# close tab
		self.widgets["WorkArea"].remove_page( t_nCurrentTabIndex )

		if self.m_oGcDiagrams.has_key(t_nCurrentTabIndex):
			self.m_oGcDiagrams[t_nCurrentTabIndex].stopSubProcess()
			self.m_oGcDiagrams[t_nCurrentTabIndex].removeDir()
			del self.m_oGcDiagrams[t_nCurrentTabIndex]

		t_oGcDiagrams = {}
	
		for t_nTabIndex,t_nOldTabIndex in enumerate(self.m_oGcDiagrams.keys()):
			t_oGcDiagrams[t_nTabIndex] = self.m_oGcDiagrams[t_nOldTabIndex]
		
		self.m_oGcDiagrams = t_oGcDiagrams
		return True
		
	#----------------------------------------------------------------------

	def ShowGrid(self,a_bShowGrid):
		"""
		Shows the grid or not based on the boolean received as argument.
		"""
		print "no grids"

	#----------------------------------------------------------------------

	def SetGridInterval(self,a_nGridInterval):
		"""
		Defines the Grid interval and sets the diacanvas.
		"""
		print "no grids"

	#----------------------------------------------------------------------
	
	def LoadExample(self, *args):
		for example in self.exampleMenuItens:
			if example[0] == args[0]:
				#print example[0], example[1]
				self.openFile(example[1])
	
	def LoadExamplesMenu(self):
		t_lListOfExamples = glob(self.m_sDataDir+"examples.*/*")
		t_lListOfExamples.sort(key=os.path.basename)

		##ALG to prevent using filenames with _ on the menus
		#t_lNewL = []
		#for s in t_lListOfExamples:
			#t_lNewL.append(s.replace("_","-"))
		#t_lListOfExamples = t_lNewL
		
		self.widgets['fake_separator'].destroy()
		self.widgets.pop('fake_separator')
		
		for example in t_lListOfExamples:
			t_oMenuItem = Gtk.MenuItem(example.split("/").pop())
			self.widgets['examples_menu'].append(t_oMenuItem)
			t_oMenuItem.connect("activate", self.LoadExample)
			self.widgets['examples_menu'].show_all()
			self.exampleMenuItens.append((t_oMenuItem,example))


	def openFile( self, fileName):
		print "Opening", fileName, "..."

		##create a new workspace
		self.on_NewToolBar_clicked()

		t_nCurrentPage = self.widgets['WorkArea'].get_current_page()
		t_oGcDiagram = self.m_oGcDiagrams[t_nCurrentPage]

		if len(fileName) > 0:
			t_oGcDiagram.SetFilename(fileName)
				
		if self.m_oGcDiagrams.has_key( self.widgets['WorkArea'].get_current_page() ): 
			t_oGcDiagram = self.m_oGcDiagrams[self.widgets['WorkArea'].get_current_page()]
			if t_oGcDiagram.GetFilename() is not None:
				try:
					t_oGcDiagram.loadFromFile()
				except AssertionError, ZeroDivisionError:
					print "Failed to load " + fileName + "."
					self.CloseCurrentTab()
				else:
					print fileName + " successfully loaded."
					t_nCurrentPage = self.widgets['WorkArea'].get_current_page()
					self.setTabName(t_nCurrentPage, t_oGcDiagram.GetFilename())

	#----------------------------------------------------------------------
	
	def setBlocks(self):
		"""
		Set blocks list.
		"""

		s2idirectory.loadBlocks()
		s2idirectory.buildGroups()
		
		# self.Blocks is a dictionnary of blocks-groups
		# self.Blocks= {'Filtering': ['Morphology', 'Structuring element' ...], 'Features': ['Draw Keypoints', 'Compute BRISK' ...], ...}
		self.Blocks =  s2idirectory.groups
				
		for x in s2idirectory.block:
			self.Blocks[s2idirectory.block[x]["TreeGroup"]].append(s2idirectory.block[x]["Label"])

	#----------------------------------------------------------------------

	def on_Reload_blocks_clicked(self, *args):
		"""
		Callback function called when 'Reload blocks' is clicked.
		Reload the blocks from files.
		"""
		print 'Reload blocks ... '
		self.setBlocksMenu()

	#----------------------------------------------------------------------

	def write(self, text):
		"""
		Write text into console output window.
		Named write to be able to replace stdout.
		"""
		# append text to gtkTextView / gtkTextBuffer
		consoleTextBuffer = self.consoleTextView.get_buffer()
		consoleTextBuffer.place_cursor(consoleTextBuffer.get_end_iter())
		consoleTextBuffer.insert_at_cursor(text)

		# limit text size
		maxLinesCnt = 200
		textLinesCnt = consoleTextBuffer.get_line_count()
		if( textLinesCnt > maxLinesCnt ):
			cutBegin = consoleTextBuffer.get_iter_at_line(0)
			cutEnd = consoleTextBuffer.get_iter_at_line(textLinesCnt - maxLinesCnt)
			consoleTextBuffer.delete(cutBegin, cutEnd)

		# scroll to the end of text
		atEndMark = consoleTextBuffer.get_insert()
		self.consoleTextView.scroll_mark_onscreen(atEndMark)

		return 

	#----------------------------------------------------------------------

	def captureStdout(self):
		"""
		Capture stdout output. Redirect them to self.write().
		"""
		sys.stdout = self

	#----------------------------------------------------------------------

	def sigTERM(self, signum, frame):
		"""
		SIGTERM signal handler.
		"""
		#DBG sys.__stdout__.write('*** sigTERM() ***\n')
		self.on_HarpiaFrontend_destroy()

	#----------------------------------------------------------------------

	def setTabName(self, nPage, fileName):
		t_oChild= self.widgets['WorkArea'].get_nth_page(nPage)
		t_sNewLabel = os.path.basename(fileName)
		t_oLabel= Gtk.Label(str(t_sNewLabel))
		self.widgets['WorkArea'].set_tab_label(t_oChild, t_oLabel)


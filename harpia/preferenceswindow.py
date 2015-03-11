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
# Manage 'Preferences' window.
#

import pygtk
pygtk.require('2.0')
import gtk

import lvExtensions

class PreferencesWindow():
	def __init__(self, mainWindow, title='Preferences'):
		self.mainWindow = mainWindow
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.set_title(title)
		self.window.connect("delete_event", self.delete_event)
		self.window.connect("key-press-event", self.keyPressed)
		self.window.set_border_width(10)
		self.window.set_default_size(600, 50)

		# build window UI

		entries = {}
		vbox = gtk.VBox(False, 5)
		self.window.add(vbox)

		# LIRIS-VISION configuration

		self.newTitle(vbox, 'LIRIS-VISION configuration:')
		self.newEntry(vbox, entries, 'lirisvisionDir', ' - LIRIS-VISION directory', lvExtensions.getLirisvisionDir(), 'Path to directory')

		# OpenCV configuration

		self.newHSeparator(vbox)
		self.newTitle(vbox, 'OpenCV configuration:')
		# OpenCV include directories
		self.newEntry(vbox, entries, 'openCVIncludeDirs', ' - include directories', lvExtensions.getOpencvIncludeDirs(), 'List of paths separated by \';\'')
		# OpenCV libraries directories
		self.newEntry(vbox, entries, 'openCVLibrariesDirs', ' - libraries directories (.so/.lib)', lvExtensions.getOpencvLibrariesDirs(), 'List of paths separated by \';\'')
		# OpenCV dll directories
		self.newEntry(vbox, entries, 'openCVDllDirs', ' - dll directories (.dll)', lvExtensions.getOpencvDllDirs(), 'Windows OS only, list of paths separated by \';\'')
		# OpenCV libraries names
		self.newEntry(vbox, entries, 'openCVLibraries', ' - libraries names', lvExtensions.getOpencvLibraries(), 'List of names separated by \';\'')

		# Other libraries
		
		self.newHSeparator(vbox)
		self.newTitle(vbox, 'Other libraries configuration:')
		# Other include directories
		self.newEntry(vbox, entries, 'otherIncludeDirs', ' - include directories', lvExtensions.getOtherIncludeDirs(), 'List of paths separated by \';\'')
		# Other libraries directories
		self.newEntry(vbox, entries, 'otherLibrariesDirs', ' - libraries directories (.so/.lib)', lvExtensions.getOtherLibrariesDirs(), 'List of paths separated by \';\'')
		# Other dll directories
		self.newEntry(vbox, entries, 'otherDllDirs', ' - dll directories (.dll)', lvExtensions.getOtherDllDirs(), 'Windows OS only, list of paths separated by \';\'')
		# Other libraries names
		self.newEntry(vbox, entries, 'otherLibraries', ' - libraries names', lvExtensions.getOtherLibraries(), 'List of names separated by \';\'')

		# Miscalleneous

		self.newHSeparator(vbox)
		self.newTitle(vbox, 'Miscalleneous:')
		self.newEntry(vbox, entries, 'localModulesDirs', ' - block sources', lvExtensions.getLocalModulesDirs(), 'List of directories separated by \';\', containing blocks definition')
		self.newEntry(vbox, entries, 'workingDirsPlace', ' - working directories place', lvExtensions.getWorkingDirsPlace(), 'An existent directory where temporary working directories are created')

		# Build options

		self.newHSeparator(vbox)
		title = self.newTitle(vbox, 'Build options:')
		title.set_sensitive(False) #disable widget
		# Compiler options
		entry = self.newEntry(vbox, entries, 'compilerOptions', ' - compiler options', lvExtensions.getCompilerOptions(), 'List of options ("-xxx" for GCC, "/xxx" for MSVC++) separated by \';\'')
		entry.set_sensitive(False) #disable widget
		# Linker options
		entry = self.newEntry(vbox, entries, 'linkerOptions', ' - linker options', lvExtensions.getLinkerOptions(), 'List of options ("-xxx" for GCC, "/xxx" for MSVC++) separated by \';\'')
		entry.set_sensitive(False) #disable widget

		# display ok and cancel buttons

		self.newHSeparator(vbox)
		hbox = gtk.HBox(True, 10)
		vbox.pack_start(hbox, False, True, 20)
		# button ok
		buttonOk = gtk.Button("Ok")
		hbox.pack_start(buttonOk, False, True, 20)
		buttonOk.connect("clicked", self.buttonOkClicked, entries)
		# button cancel
		buttonCancel = gtk.Button("Cancel")
		hbox.pack_end(buttonCancel, False, True, 20)
		buttonCancel.connect("clicked", self.buttonCancelClicked)
		buttonCancel.show()

		# display all widgets
		vbox.show_all()
		self.window.show()


	def newEntry(self, vbox, entries, name, title, content, tooltip):
		"""Add a new line [label|text_entry] to the preferences window."""
		hbox = gtk.HBox(False, 5)
		# display label
		label = gtk.Label(title)
		label.set_alignment(0.0, 0.5)
		hbox.pack_start(label, False, False, 0)
		# display entry box
		entries[name] = gtk.Entry()
		entries[name].set_tooltip_text(tooltip)
		entries[name].set_text(content)
		hbox.pack_start(entries[name], True, True, 0)
		vbox.pack_start(hbox, False, False, 0)
		return hbox


	def newHSeparator(self, vbox):
		separator = gtk.HSeparator()
		vbox.pack_start(separator, False, True, 10)
		return separator


	def newTitle(self, vbox, title):
		label = gtk.Label(title)
		label.set_alignment(0.0, 0.0)
		vbox.pack_start(label, False, False, 0)
		return label


	def keyPressed(self, widget, event):
		# quit if ESC pressed
		if event.keyval == gtk.keysyms.Escape:
			self.window.destroy()
 

	def buttonOkClicked(self, widget, entries):
		# update global variables 
		lvExtensions.setLirisvisionDir(entries['lirisvisionDir'].get_text())
		lvExtensions.setOpencvIncludeDirs(entries['openCVIncludeDirs'].get_text())
		lvExtensions.setOpencvLibrariesDirs(entries['openCVLibrariesDirs'].get_text())
		lvExtensions.setOpencvDllDirs(entries['openCVDllDirs'].get_text())
		lvExtensions.setOpencvLibraries(entries['openCVLibraries'].get_text())
		lvExtensions.setOtherIncludeDirs(entries['otherIncludeDirs'].get_text())
		lvExtensions.setOtherLibrariesDirs(entries['otherLibrariesDirs'].get_text())
		lvExtensions.setOtherDllDirs(entries['otherDllDirs'].get_text())
		lvExtensions.setOtherLibraries(entries['otherLibraries'].get_text())
		lvExtensions.setCompilerOptions(entries['compilerOptions'].get_text())
		lvExtensions.setLinkerOptions(entries['linkerOptions'].get_text())
		lvExtensions.setLocalModulesDirs(entries['localModulesDirs'].get_text())
		lvExtensions.setWorkingDirsPlace(entries['workingDirsPlace'].get_text())
		# save to config file
		lvExtensions.saveConfiguration()
		# reload blocks in case local modules directory has changed
		self.mainWindow.on_Reload_blocks_clicked()
		self.window.destroy()


	def buttonCancelClicked(self, widget):
		self.window.destroy()


	def delete_event(self, widget, event, data=None):
		self.window.destroy()
		return False



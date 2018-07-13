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
# Display block properties window.
#

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import collections

fileSelectionFolder = ''  # store last file selection folder

class PropertiesWindow():
	def __init__(self, block, propertiesXML, title='Properties', help=''):
		self.window = Gtk.Window(Gtk.WINDOW_TOPLEVEL)
		self.window.set_title(title)
		self.window.connect("delete_event", self.delete_event)
		self.window.connect("key-press-event", self.keyPressed)
		self.window.set_border_width(10)
		self.window.set_default_size(500, 400)

		# convert xml structure to dictionnary
		# parameters[propertyName] = { 'value':..., 'type':..., ... }
		
		self.block = block  # the block the properties belong to
		self.propertiesXML = propertiesXML
		self.parameters = collections.OrderedDict() 
			# use an OrderedDict here rather than a dict to display
			# parameters in the same order as in the block xml file.
		for prop in self.propertiesXML.findAttributes('./property'):
			prop = dict(prop) # works on a copy to not change the real props
			name = prop['name']
			prop.pop('name') 
			self.parameters[name] = prop
		# remove 'state' property
		#self.parameters.pop('state')

		vbox = Gtk.VBox(False, 10)
		self.window.add(vbox)

		# display properties

		label = Gtk.Label('Block parameters:')
		label.set_alignment(0.0, 0.0)
		vbox.pack_start(label, False, False, 0)
		label.show()

		rowCnt = len(self.parameters)
		table = Gtk.Table(rowCnt, 3, False)
		#table.set_row_spacings(5)
		#table.set_col_spacings(5)
		vbox.pack_start(table, False, False, 0)

		entries = {}
		row = 0
		for param in self.parameters:
			row += 1

			# display property description
			try:
				label = Gtk.Label(self.parameters[param]['desc'])
			except:
				label = Gtk.Label(param)
			label.set_alignment(1, 0)
			table.attach(label, 0, 1, row-1, row, Gtk.FILL, 0, 5)
			label.show()
			
			# display property modification area
			try:
				if self.parameters[param]['type'] == 'selector':
					# build possible values list beginning with
					# current value

					current = self.parameters[param]['value']
					values = set(self.parameters[param]['values'].split(';'))
					values.discard(current)
					values = sorted(values)
					values.insert(0,current)

					comboBox = Gtk.combo_box_entry_new_text()
					for v in values:
						comboBox.append_text(v)
					comboBox.set_active(0)
					
					table.attach(comboBox, 1, 2, row-1, row, Gtk.EXPAND|Gtk.FILL, 0)
					comboBox.show()

					entries[param] = comboBox.get_child()
				else:
					# force except clause execution
					raise KeyError
			except KeyError:
				entries[param] = Gtk.Entry()
				entries[param].set_text(self.parameters[param]['value'])
				table.attach(entries[param], 1, 2, row-1, row, Gtk.EXPAND|Gtk.FILL, 0)
				entries[param].show()

			# if property is a file name, display a select file button
			try:
				if self.parameters[param]['type'] == 'filename':
					selectButton = Gtk.Button("...")
					table.attach(selectButton, 2, 3, row-1, row, 0, 0)
					selectButton.connect("clicked", self.selectFile, entries[param])
					selectButton.show()
			except KeyError:
				pass
	
		table.show()

		# display ok and cancel buttons

		separator = Gtk.HSeparator()
		vbox.pack_start(separator, False, True, 0)
		separator.show()

		hbox = Gtk.HBox(True, 10)
		vbox.pack_start(hbox, False, True, 0)

		buttonOk = Gtk.Button("Ok")
		hbox.pack_start(buttonOk, False, True, 20)
		buttonOk.connect("clicked", self.buttonOkClicked, entries)
		buttonOk.show()

		buttonCancel = Gtk.Button("Cancel")
		hbox.pack_end(buttonCancel, False, True, 20)
		buttonCancel.connect("clicked", self.buttonCancelClicked)
		buttonCancel.show()

		hbox.show()

		# display help

		if help:
			separator = Gtk.HSeparator()
			vbox.pack_start(separator, False, True, 0)
			separator.show()

			label = Gtk.Label('Help:')
			label.set_alignment(0.0, 0.0)
			vbox.pack_start(label, False, False, 0)
			label.show()

			sw = Gtk.ScrolledWindow()
			vbox.pack_start(sw, True, True, 0)
			sw.set_policy(Gtk.POLICY_AUTOMATIC, Gtk.POLICY_AUTOMATIC)
			textview = Gtk.TextView()
			sw.add_with_viewport(textview)
			textview.get_buffer().set_text(help)
			textview.set_editable(False)
			textview.set_wrap_mode(Gtk.WRAP_WORD)
			textview.show()
			sw.show()

		vbox.show()
		self.window.show()

	def keyPressed(self, widget, event):
		# quit if ESC pressed
		dummy, keyval = event.get_keyval()
		if keyval == Gdk.KEY_Escape:
			self.window.destroy()
 
	def selectFile(self, widget, entry):
		FileSelection(entry)

	"""
	Called when the user click the 'ok' button of the properties window.
	"""
	def buttonOkClicked(self, widget, entries):
		# keep track of previous properties
		oldProperties = self.propertiesXML.toString()
		# update properties with user data 
		for entry in entries:
			self.propertiesXML.setAttribute("./property/[@name='"+entry+"']", 'value', entries[entry].get_text())
		# close properties window
		self.window.destroy()
		# check if properties have changed
		newProperties = self.propertiesXML.toString()
		if newProperties != oldProperties:
			self.block.onPropertiesChanged()

	def buttonCancelClicked(self, widget):
		self.window.destroy()

	def delete_event(self, widget, event, data=None):
		self.window.destroy()
		return False


class FileSelection:
	global fileSelectionFolder

	def __init__(self, entry):
		global fileSelectionFolder

		dialog = Gtk.FileChooserDialog("Open..", None, Gtk.FILE_CHOOSER_ACTION_SAVE, (Gtk.STOCK_CANCEL, Gtk.RESPONSE_CANCEL, Gtk.STOCK_OPEN, Gtk.RESPONSE_OK))
		dialog.set_default_response(Gtk.RESPONSE_OK)

		dialog.set_current_folder(fileSelectionFolder)
		dialog.set_current_name(entry.get_text())
		"""
		filter = Gtk.FileFilter()
		filter.set_name("All files")
		filter.add_pattern("*")
		dialog.add_filter(filter)

		filter = Gtk.FileFilter()
		filter.set_name("Images")
		filter.add_mime_type("image/png")
		filter.add_mime_type("image/jpeg")
		filter.add_mime_type("image/gif")
		filter.add_pattern("*.png")
		filter.add_pattern("*.jpg")
		filter.add_pattern("*.gif")
		filter.add_pattern("*.tif")
		filter.add_pattern("*.xpm")
		dialog.add_filter(filter)
		"""

		response = dialog.run()
		if response == Gtk.RESPONSE_OK:
			entry.set_text(dialog.get_filename())
			fileSelectionFolder = dialog.get_current_folder()
		"""
		elif response == Gtk.RESPONSE_CANCEL:
			print 'Closed, no files selected'
		"""
		dialog.destroy()


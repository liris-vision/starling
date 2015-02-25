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
# Copyright: 2007 - 2009 Clovis Peruchi Scotti (scotti@ieee.org), S2i (www.s2i.das.ufsc.br)
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


import gobject
import pango
import gtk
import math
import goocanvas
import sys

#sys.path.append('../bin')
#import s2idirectory

class GcdConnector():
	def __init__( self, diagram, a_nConnectorCountId=1, a_nFrom=-1, a_nFromOut=-1):#a_nInputs, a_nOutputs, a_nBlockType ):
		
		self.ParentDiagram = diagram
		
		self.m_nCountId = a_nConnectorCountId
		
		self.fromBlock = a_nFrom
		self.fromBlockOut = a_nFromOut
		
		self.fromPoint = self.ParentDiagram.m_oBlocks[self.fromBlock].GetOutputPos(self.fromBlockOut) #pegando o ponto verdadeiro de onde sai o conector

		self.ConnBoundary = 16.0

		self.toPoint = (0,0)
		
		self.toBlock = -1#a_nTo
		self.toBlockIn = -1#a_nToIn
		
		self.m_bFocus = False
		self.m_bHasFlow = False
	
		self.wGroup = goocanvas.Group(can_focus=True)
		# append connector to canvas root at a low level
		# so that blocks catch events before connectors
		self.ParentDiagram.root_add(self.wGroup, 1)
		
		w1 = goocanvas.Polyline(end_arrow=True, line_width=3)
		self.wGroup.add_child(w1)

		self.widgets = {}
		self.widgets["Line"] = w1
		
		self.turnOnEvents()

	def __del__(self):
		print "GC: deleting GcdConnector:",self.m_nCountId


	"""
	Delete widgets.
	"""
	def removeWidgets(self):
		self.wGroup.remove()
	
	"""
	Set connector end to given input of given block.
	a_nTo: block id.
	a_nToIn: input id.
	"""
	def SetEnd(self, a_nTo=-1, a_nToIn=-1):
		self.toBlock = a_nTo
		self.toBlockIn = a_nToIn
		self.UpdateConnector()

	def group_event(self, widget, target, event=None):
		"""debug
		print '*', __file__, 'group_event:'
		self.ParentDiagram.displayEvent(event)
		"""

		if event.type == gtk.gdk.BUTTON_PRESS:
			#print __file__, ', group_event(): BUTTON_PRESS'
			if event.button == 1:
				self.grabFocus()
				return False
			elif event.button == 3:
				self.RightClick(event)

		elif event.type == gtk.gdk.KEY_PRESS:
			if event.keyval == gtk.keysyms.Delete:
				# on DELETE key pressed
				self.DeleteConnector()

		elif event.type == gtk.gdk.ENTER_NOTIFY:
				# Make the outline wide.
				self.setThickBorder(True)
		
		elif event.type == gtk.gdk.LEAVE_NOTIFY:
				# Make the outline thin.
				if not self.hasFocus():
					self.setThickBorder(False)

		return False

	def UpdateTracking(self, newEnd=None):
		#print 'newEnd=', newEnd
		p = []
		p.append(self.fromPoint)
		p.append(newEnd)
		p = goocanvas.Points(p)
		self.widgets["Line"].set_properties(points=p)



	"""
	Update connector position according to related blocks positions.
	Usefull when blocks are moved.
	"""
	def UpdateConnector(self):
		
		self.fromPoint = self.ParentDiagram.m_oBlocks[self.fromBlock].GetOutputPos(self.fromBlockOut) #pegando o ponto verdadeiro de onde sai o conector
		self.toPoint = self.ParentDiagram.m_oBlocks[self.toBlock].GetInputPos(self.toBlockIn) #pegando o ponto verdadeiro de onde sai o conector
	
		p = []
		p.append(self.fromPoint)
		p.append(self.toPoint)
		p = goocanvas.Points(p)
	
		self.widgets["Line"].set_properties(points=p)

	def setThickBorder(self, thick):
		if thick:
			self.widgets["Line"].set_properties(line_width=5.0)
		else:
			self.widgets["Line"].set_properties(line_width=3.0)

	def UpdateFlow(self):
		self.m_bHasFlow = self.ParentDiagram.m_oBlocks[self.fromBlock].m_bHasFlow
		return self.m_bHasFlow

	def UpdateFlowDisplay(self):
		if self.m_bHasFlow:
			self.widgets["Line"].set_properties(stroke_color='black')
		else:
			self.widgets["Line"].set_properties(fill_color='red', stroke_color='red')

	def RightClick(self, a_oEvent):
		t_oMenu = gtk.Menu()
	
		t_oMenuItem = gtk.MenuItem("Properties")
		#t_oMenuItem.connect("activate", self.ShowPropertiesGUI )
		t_oMenu.append(t_oMenuItem)
		
		# Menu separator
		t_oMenuItem = gtk.SeparatorMenuItem()
		t_oMenu.append(t_oMenuItem)
		
		# Excluir (delete) item
		t_oMenuItem = gtk.MenuItem("Delete")
		t_oMenuItem.connect("activate", self.DeleteClicked )
		t_oMenu.append(t_oMenuItem)

		# Another separator
		t_oMenuItem = gtk.SeparatorMenuItem()
		t_oMenu.append(t_oMenuItem)
		# Shows the menu
		t_oMenu.show_all()
		t_oMenu.popup(None, None, None, a_oEvent.button, a_oEvent.time)

	def DeleteClicked(self, *args ):
		self.DeleteConnector()

	"""
	Delete himself.
	"""
	def DeleteConnector(self):
		# ask diagram to be deleted
		self.ParentDiagram.DeleteConnector(self.m_nCountId)


	"""
	Check whether connector has focus.
	"""
	def hasFocus(self):
		return self.m_bFocus

	"""
	Grab focus.
	"""
	def grabFocus(self):
		self.wGroup.get_canvas().grab_focus(self.wGroup)
		
	"""
	Called when block focus state is changed.
	"""
	def onFocusChanged(self):
		self.setThickBorder(self.hasFocus())

	"""
	Called when connector gets keyboard focus.
	"""
	def onFocusIn(self, widget, target, event=None):
		self.m_bFocus = True
		self.onFocusChanged()

	"""
	Called when connector loses keyboard focus.
	"""
	def onFocusOut(self, widget, target, event=None):
		self.m_bFocus = False
		self.onFocusChanged()

	"""
	Turn on events.
	Connector events are not turned on startup to avoid that 
	currently drawn connector get events instead of target block.
	"""
	def turnOnEvents(self):
		self.wGroup.connect("button-press-event", self.group_event)
		self.wGroup.connect("key-press-event", self.group_event)
		self.wGroup.connect("enter-notify-event", self.group_event)
		self.wGroup.connect("leave-notify-event", self.group_event)
		self.wGroup.connect("focus-in-event", self.onFocusIn)
		self.wGroup.connect("focus-out-event", self.onFocusOut)

def Psub(p1,p0):
	return p1[0]-p0[0],p1[1]-p0[1]

def Psum(p1,p0):
	return p1[0]+p0[0],p1[1]+p0[1]

def CordModDec(Vector):
	ans = []
	for e in Vector:
		ans.append(e)
	
	for e in range(len(ans)):
		if ans[e] > 0:
			ans[e] -= 1
		else:
			ans[e] += 1
	
	return (ans[0],ans[1])
		
def ColorFromList(rgba):
	color = int(rgba[0])*0x1000000+int(rgba[1])*0x10000+int(rgba[2])*0x100+(int(rgba[3])*0x01)
	return color

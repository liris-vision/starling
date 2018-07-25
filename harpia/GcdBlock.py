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

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
gi.require_version('GooCanvas', '2.0')
from gi.repository import GooCanvas
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import GdkPixbuf

import os
import math

import xmltree
import s2idirectory
import propertieswindow

import copy

WIDTH_2_TEXT_OFFSET = 22
WIDTH_DEFAULT = 112
HEIGHT_DEFAULT = 56

PORT_SENSITIVITY = 12

# font used to display the block name
BLOCKNAME_FONT_NAME = 'sans bold condensed 9'
if os.name == 'nt':
	BLOCKNAME_FONT_NAME = 'Sans Not-Rotated 9'
BLOCKNAME_FONT_COLOR = 'dark-blue'

# font used to display input/ouput types
IO_FONT_NAME = 'sans condensed 7'
if os.name == 'nt':
	IO_FONT_NAME = 'Sans Not-Rotated 7'
IO_FONT_COLOR = 'blue'

# input/output icons
INPUT_ICON_FILE = 'images/input.png'
OUTPUT_ICON_FILE = 'images/output.png'


class GcdBlock():
	def __init__( self, diagram, a_nBlockType, a_nBlockCountId=1):#a_nInputs, a_nOutputs, a_nBlockType ):
		
		#initialize all members
		
		#if len(a_oDictBlock) == 0:
			#a_oDictBlock["Label"] = "Unknown Block"
			#a_oDictBlock["Icon"] = 'haarDetect.png'
			#a_oDictBlock["Color"] = "150:20:40:150"
			#a_oDictBlock["Inputs"] = 0
			#a_oDictBlock["Outputs"] = 0
		
		self.m_nBlockType = a_nBlockType
		
		self.ParentDiagram = diagram
		
		self.m_sDataDir = os.environ['HARPIA_DATA_DIR']
		
		if s2idirectory.block.has_key(a_nBlockType):
			self.m_oDictBlock = s2idirectory.block[a_nBlockType] #a_oDictBlock
		else:
			self.m_oDictBlock = s2idirectory.block[0] #a_oDictBlock
			print "Bad block type", a_nBlockType, "... assuming 0"
		
		self.m_nBlockCountId = a_nBlockCountId
		
		self.widgets = {}
		
		self.m_bFocus = False
		
		self.m_bHasFlow = False
		self.m_bTimeShifts = False
		self.m_bIsSource = False

		if self.m_oDictBlock['Inputs'] == 0:
			self.m_bIsSource = True
		
		if self.m_oDictBlock.has_key("TimeShifts"): #delay block
			self.m_bTimeShifts = self.m_oDictBlock["TimeShifts"]
		

		# self.m_oPropertiesXML contains something like:
		# <block id="1" type="0">
		#   <property name="state" value="true" />
		#   <property name="_PARAM1_" type="filename" value="resource/lena.jpg" />
		# </block>
		self.m_oPropertiesXML = xmltree.xmlTree()
		self.m_oPropertiesXML.load(str(self.m_oDictBlock["Path"]["Xml"]))
		self.m_oPropertiesXML = self.m_oPropertiesXML.findSubTrees('./block')[0]
		self.m_oPropertiesXML.setAttribute('.', 'id', unicode(str(self.m_nBlockCountId)))
		
		self.m_oBorderColor = [ 0, 0, 0, 255 ]
		self.m_oBackColor = [0,0,0,150]
		
		self.m_nRadius = 15
		
		self.m_nInputHeight = 24
		self.m_nInputWidth = 24
		self.m_nOutputHeight = 24
		self.m_nOutputWidth = 14
		
		self.inputPortCenters = []
		self.outputPortCenters = []
		
		self.width = WIDTH_DEFAULT
		self.TextWidth = self.width - WIDTH_2_TEXT_OFFSET
		
		
		t_nMaxIO = max(self.m_oDictBlock["Inputs"],self.m_oDictBlock["Outputs"])
		
		## Generates the block size, based on the number of inputs,outputs
			
		# Comment block is too small...
		if not t_nMaxIO:
			t_nMaxIO = 1
		
		self.height = max( ((t_nMaxIO-1)* 5 ) # space between ports = 5
												+(self.m_nRadius*2 ) #tirando a margem superior e inferior
												+(t_nMaxIO * self.m_nInputHeight),#adicionando a altura de cada port
												 HEIGHT_DEFAULT)
		
		self.Label = self.m_oDictBlock["Label"]
		self.iconFile = self.m_sDataDir+self.m_oDictBlock["Icon"]
		
		self.wGroup = GooCanvas.CanvasGroup(can_focus=True)
		self.ParentDiagram.root_add(self.wGroup)
		self.wGroup.connect("button-press-event", self.group_event)
		self.wGroup.connect("button-release-event", self.group_event)
		self.wGroup.connect("key-press-event", self.group_event)
		self.wGroup.connect("motion-notify-event", self.group_event)
		self.wGroup.connect("enter-notify-event", self.group_event)
		self.wGroup.connect("leave-notify-event", self.group_event)
		self.wGroup.connect("focus-in-event", self.onFocusIn)
		self.wGroup.connect("focus-out-event", self.onFocusOut)
		
		self.Build()
		self.isMoving = False  # is the block being moved ?


	"""
	Delete widgets.
	"""
	def removeWidgets(self):
		self.wGroup.remove()
	

	def IsInput(self, event):
		#checks whether distance from any input center to the event position is less than PORT_SENSITIVITY
		clickedPoint = (event.x, event.y)
		#print ' *', __file__, ', IsInput: clickedPoint=', clickedPoint
		inputPortCenters = []

		if len(self.inputPortCenters) == 0: 
			#compute portCenters if they don't exist
			self.ComputeInputPorts()
		
		for pointIndex in range(len(self.inputPortCenters)):
			if Dist(self.inputPortCenters[pointIndex],clickedPoint) < PORT_SENSITIVITY:
				return pointIndex
		return -1

	def IsOutput(self,event):
		#checks whether distance from any input center to the event position is less than PORT_SENSITIVITY
		clickedPoint = (event.x, event.y)
		
		if len(self.outputPortCenters) == 0: 
			#compute portCenters if they don't exist
			self.ComputeOutputPorts()
		
		for pointIndex in range(len(self.outputPortCenters)):
			if Dist(self.outputPortCenters[pointIndex],clickedPoint) < PORT_SENSITIVITY:
				return pointIndex
		return -1

	def ComputeOutputPorts(self):
		for outputPort in range(self.m_oDictBlock["Outputs"]):
			self.outputPortCenters.append((self.width-(self.m_nInputWidth/2),  (self.m_nRadius # upper border
																												+ (outputPort*5) # spacing betwen ports
																												+ outputPort*self.m_nInputHeight #previous ports
																												+ self.m_nInputHeight/2)))#going to the port's center

	def ComputeInputPorts(self):
		for inputPort in range(self.m_oDictBlock["Inputs"]):
			self.inputPortCenters.append((self.m_nInputWidth/2,  (self.m_nRadius # upper border
																												+ (inputPort*5) # spacing betwen ports
																												+ inputPort*self.m_nInputHeight #previous ports
																												+ self.m_nInputHeight/2)))#going to the port's center

	def group_event(self, widget, target, event=None):
		# position relative to canvas origin: event.x_root, event.y_root
		# position relative to block origin: event.x, event.y
		"""debug
		print '*', __file__, 'group_event:', event
		self.ParentDiagram.displayEvent(event)
		"""
		if event.type == Gdk.EventType.BUTTON_PRESS:
				#print __file__, ', group_event(): BUTTON_PRESS'
				if event.button == 1:
					#print 'in', __file__, 'group_event: event.x_root=', event.x_root, ', event.y_root=', event.y_root, ', event.x=', event.x, ', event.y=', event.y
					# Remember starting position.
					# if event resolution got here, the diagram event resolution routine didn't matched with any ports.. so..
					self.remember_x = event.x_root
					self.remember_y = event.y_root
					
					# check if a block input or output has been clicked
					t_nInput = self.IsInput(event)
					#print 't_nInput =', t_nInput
					if t_nInput <> -1:
						self.ParentDiagram.ClickedInput(self.m_nBlockCountId,t_nInput)
						return True
					else:
						t_nOutput = self.IsOutput(event)
						if t_nOutput <> -1:
							self.ParentDiagram.ClickedOutput(self.m_nBlockCountId,t_nOutput)
							return True
						else:
							self.grabFocus()
							#self.SetFocusedState(True)
							#print("onBlock(" + str(event.x - self.wGroup.get_property('x')) + "," + str(event.y - self.wGroup.get_property('y')) + ")")
							#print("Since this event does nothing, we should warn GcDiagram that any current opperations were aborted! or just return False!")
							#self.ParentDiagram.AbortConnection()
							return False
					return False
				elif event.button == 3:
					#print "right button at block"
					self.RightClick(event)
					return True #explicitly returns true so that diagram won't catch this event
		elif event.type == Gdk.EventType.MOTION_NOTIFY:
			# moving block with the mouse (left button down + move)
			#DBG print 'in', __file__, 'group_event: MOTION_NOTIFY'
			if event.state & Gdk.ModifierType.BUTTON1_MASK:
				if self.ParentDiagram.m_oCurrConnector == None:
					new_x = event.x_root
					new_y = event.y_root
					self.Move(new_x - self.remember_x, new_y - self.remember_y)
					self.remember_x = new_x
					self.remember_y = new_y
					self.isMoving = True
					return False
		elif event.type == Gdk.EventType.BUTTON_RELEASE:
			if event.button == 1 and self.isMoving:
				# end of moving
				self.ParentDiagram.onBlockStopMoving(self.m_nBlockCountId)
				self.isMoving = False
				return False
		elif event.type == Gdk.EventType._2BUTTON_PRESS:
			#print 'in', __file__, 'group_event: _2BUTTON_PRESS'
			#Open up the block's options
			self.ShowBlockGUI()
			return True
		
		elif event.type == Gdk.EventType.ENTER_NOTIFY:
			#print 'in', __file__, 'group_event: ENTER_NOTIFY'
			# Make the outline wide.
			self.setThickBorder(True)
			return False #pode propagar p/ cima
		
		elif event.type == Gdk.EventType.LEAVE_NOTIFY:
			#print 'in', __file__, 'group_event: LEAVE_NOTIFY'
			# Make the outline thin.
			if not self.hasFocus():
				self.setThickBorder(False)
			return False #pode passar p/ cima
		
		elif event.type == Gdk.EventType.KEY_PRESS:
			#print 'in', __file__, 'group_event: KEY_PRESS'
			dummy, keyval = event.get_keyval()
			if keyval == Gdk.KEY_Delete:
				# on DELETE key pressed
				self.DeleteBlock()
				

	def __del__(self):
		print "GC: deleting GcdBlock:",self.m_nBlockCountId
		
	def DeleteClicked(self, *args ): 
		self.DeleteBlock()

	def DeleteBlock(self):
		# ask diagram to be deleted
		self.ParentDiagram.DeleteBlock(self.m_nBlockCountId)

	def _BbRect(self):
		self.SetBackColor()
		#w1 = GooCanvas.CanvasPolyline(points=GooCanvas.CanvasPoints(pf), fill_color_rgba=ColorFromList(self.m_oBackColor), line_width=1)
		w1 = GooCanvas.CanvasRect(width=self.width, height=self.height, fill_color_rgba=ColorFromList(self.m_oBackColor), line_width=1, radius_x=self.m_nRadius, radius_y=self.m_nRadius)
		self.wGroup.add_child(w1, -1)
		self.widgets["Rect"] = w1
		
	def _BIcon(self):
		pb = GdkPixbuf.Pixbuf.new_from_file(self.m_sDataDir+self.m_oDictBlock["Icon"])
		xpos = self.width/2 - pb.get_width()/2
		ypos = self.height/2 - pb.get_height()/2
		icon = GooCanvas.CanvasImage(pixbuf=pb, x=xpos, y=ypos)
		self.wGroup.add_child(icon, -1)
		self.widgets["pb"] = icon
	
	def _BInputs(self):
		inPWids = []
		for inputId in range(len(self.m_oDictBlock["InTypes"])):
			yIcon = self.m_nRadius + inputId*5 + inputId*self.m_nInputHeight

			inputType = self.m_oDictBlock["InTypes"][inputId+1]['type']

			# build description string (escape '<' and '>' characters)
			try:
				description = self.m_oDictBlock["InTypes"][inputId+1]['desc']
			except KeyError:
				description = ''
			description += ' (' + inputType + ')'
			description = description.replace('<', '&lt;')
			description = description.replace('>', '&gt;')
		
			# display input icon
			icon = GdkPixbuf.Pixbuf.new_from_file(self.m_sDataDir + INPUT_ICON_FILE)
			t_Wid = GooCanvas.CanvasImage(pixbuf=icon, x=0, y=yIcon)
			t_Wid.set_property('tooltip', description)
			self.wGroup.add_child(t_Wid, -1)
			inPWids.append(t_Wid)

			# display input text (input type)
			inputTypeText = inputType
			if inputTypeText.startswith('cv::'):
				inputTypeText = inputTypeText[4:]
			if len(inputTypeText) > 10:
				inputTypeText = ' ...'
			label = GooCanvas.CanvasText( text=inputTypeText, anchor=GooCanvas.CanvasAnchorType.WEST, x=2, y=(yIcon+16), font=IO_FONT_NAME, fill_color=IO_FONT_COLOR)
			label.set_property('tooltip', description)
			self.wGroup.add_child(label, -1)
			inPWids.append(label)
		
		self.widgets["Inputs"] = inPWids
	
	def _BOutputs(self):
		outPWids = []
		for outputId in range(len(self.m_oDictBlock["OutTypes"])):
			xIcon = self.width - self.m_nOutputWidth
			yIcon = self.m_nRadius + outputId*5 + outputId*self.m_nOutputHeight

			outputType = self.m_oDictBlock["OutTypes"][outputId+1]['type']

			# build description string (escape '<' and '>' characters)
			try:
				description = self.m_oDictBlock["OutTypes"][outputId+1]['desc']
			except KeyError:
				description = ''
			description += ' (' + outputType + ')'
			description = description.replace('<', '&lt;')
			description = description.replace('>', '&gt;')
		
			# display input icon
			icon = GdkPixbuf.Pixbuf.new_from_file(self.m_sDataDir + OUTPUT_ICON_FILE)
			t_Wid = GooCanvas.CanvasImage(pixbuf=icon, x=xIcon, y=yIcon)
			t_Wid.set_property('tooltip', description)
			self.wGroup.add_child(t_Wid, -1)
			outPWids.append(t_Wid)

			# display input text (input type)
			outputTypeText = outputType
			if outputTypeText.startswith('cv::'):
				outputTypeText = outputTypeText[4:]
			if len(outputTypeText) > 10:
				outputTypeText = '... '
			label = GooCanvas.CanvasText( text=outputTypeText, anchor=GooCanvas.CanvasAnchorType.EAST, x=(self.width-2), y=(yIcon+16), font=IO_FONT_NAME, fill_color=IO_FONT_COLOR)
			label.set_property('tooltip', description)
			self.wGroup.add_child(label, -1)
			outPWids.append(label)

		self.widgets["Outputs"] = outPWids
	
	def _BLabels(self):
		label = GooCanvas.CanvasText( text=self.m_oDictBlock["Label"], anchor=GooCanvas.CanvasAnchorType.CENTER, x=(self.width/2), y=(self.height-10), font=BLOCKNAME_FONT_NAME, fill_color=BLOCKNAME_FONT_COLOR)
		self.wGroup.add_child(label, -1)
		textBounds = label.get_bounds()
		self.TextWidth = textBounds.x2 - textBounds.x1
		oldX,oldY = ((self.width/2),(self.height-10))
		self.width = max(self.TextWidth+WIDTH_2_TEXT_OFFSET,self.width)
		label.translate((self.width/2)-oldX, (self.height-10)-oldY)
		self.widgets["Label"] = label

	def Build(self):
		# must be called in this order ! 
		# otherwise the box rect won't have the propper width
		self._BLabels()
		self._BbRect()
		self._BInputs()
		self._BOutputs()
		self._BIcon()
		self.UpdateFlow()
		self.UpdateFlowDisplay()
	
	
	def UpdateFlow(self,a_bCheckTimeShifter=False):
		#print '---------------'
		#print 'block', self.m_oDictBlock["Label"]

		if self.m_bIsSource or (self.m_bTimeShifts and (not a_bCheckTimeShifter)):#
			#if all in connectors have flow
			#print "Block ",self.Label," id(",self.m_nBlockCountId,") has flow"
			self.m_bHasFlow = True
		else:
			# check if all required inputs have the flow
			
			# build required (aka non-optionnal) input list
			inputDict = self.m_oDictBlock["InTypes"]
			requiredInputs = set()
			for input in inputDict.values():
				try:
					if input['optional'] == 'true':
						continue
				except KeyError:
					pass
				# this is a required input
				requiredInputs.add(int(input['id']))
			
			# eliminate required inputs that have the flow
			sourceConnectors = self.ParentDiagram.GetConnectorsTo(self.m_nBlockCountId)
			for connector in sourceConnectors:
				if connector.m_bHasFlow:
					requiredInputs.discard(connector.toBlockIn + 1)

			# if some required inputs do not have the flow, then
			# the block does not have the flow
			if requiredInputs:
				self.m_bHasFlow = False
			else:
				self.m_bHasFlow = True

		return self.m_bHasFlow
	
	def ClickedInput(self, a_nInput):
		print "Input(" + str(a_nInput) + ")"
		
	def ClickedOutput(self, a_nOutput):
		print "Output(" + str(a_nOutput) + ")"
		
	def GetInputPos(self, a_nInputID):
		if len(self.inputPortCenters) == 0: #compute portCenters if they don't exist
			self.ComputeInputPorts()
		i_x,i_y = 0+self.wGroup.get_property('x'),self.inputPortCenters[a_nInputID][1]+self.wGroup.get_property('y')#x=0, y=yc
		wPoint = self.i2w(i_x,i_y)
		return (wPoint[0],wPoint[1])
	
	def GetOutputPos(self, a_nOutputID):
		if len(self.outputPortCenters) == 0: #compute portCenters if they don't exist
			self.ComputeOutputPorts()
		o_x,o_y = self.width+self.wGroup.get_property('x'),self.outputPortCenters[a_nOutputID][1]+self.wGroup.get_property('y')#x=0, y=yc
		wPoint = self.i2w(o_x,o_y)
		return (wPoint[0],wPoint[1])

	def GetBlockPos(self):
		return (self.wGroup.get_property('x'),self.wGroup.get_property('y'))

	def UpdateFlowDisplay(self):
		
		t_oFocusCorrectedColor = [self.m_oBackColor[0],self.m_oBackColor[1],self.m_oBackColor[2],self.m_oBackColor[3]]
		
		if self.m_bHasFlow:
			t_oFocusCorrectedColor[3] = self.m_oBackColor[3] #with focus: original colors
			self.widgets["Rect"].set_properties(stroke_color='black', fill_color_rgba=ColorFromList(t_oFocusCorrectedColor))
		else:
			t_oFocusCorrectedColor[3] = 50 #without focus the block background will be much more transparent
			self.widgets["Rect"].set_properties(stroke_color='red', fill_color_rgba=ColorFromList(t_oFocusCorrectedColor))

	def setThickBorder(self, bThick):
		if bThick:
			self.widgets["Rect"].set_properties(line_width=3)
		else:
			self.widgets["Rect"].set_properties(line_width=1)

	def RightClick(self, a_oEvent):
		t_oMenu = Gtk.Menu()
	
		t_oMenuItem = Gtk.MenuItem("Properties")
		t_oMenuItem.connect("activate", self.ShowBlockGUI )
		t_oMenu.append(t_oMenuItem)
		
		t_oMenuItem = Gtk.MenuItem("PrintXML")
		t_oMenuItem.connect("activate", self.PrintXML )
		t_oMenu.append(t_oMenuItem)
		
		t_oMenuItem = Gtk.MenuItem("PrintPOS")
		t_oMenuItem.connect("activate", self.PrintPOS )
		t_oMenu.append(t_oMenuItem)
		
		t_oMenuItem = Gtk.SeparatorMenuItem()
		t_oMenu.append(t_oMenuItem)
		
		t_oMenuItem = Gtk.MenuItem("Delete")
		t_oMenuItem.connect("activate", self.DeleteClicked )
		t_oMenu.append(t_oMenuItem)

		t_oMenuItem = Gtk.SeparatorMenuItem()
		t_oMenu.append(t_oMenuItem)
		
		# Shows the menu
		t_oMenu.show_all()
		t_oMenu.popup(None, None, None, a_oEvent.button, a_oEvent.time)

	def ShowBlockGUI(self, *args):
		# open non blocking properties window 
		propertieswindow.PropertiesWindow(self, self.m_oPropertiesXML, self.m_oDictBlock['Label'] + ' - block #' + str(self.m_nBlockCountId), self.m_oDictBlock['help'])
	
	def GetState(self):
		return self.m_bHasFlow
	
	def SetPropertiesXML_nID( self, a_oPropertiesXML ):
		self.SetPropertiesXML(a_oPropertiesXML)
	
	def GetBorderColor(self,*args):
		return self.m_oBorderColor
	
	def GetBackColor(self,*args):
		return self.m_oBackColor

	def SetBackColor( self, a_nColors=None ):#RGBA
		if a_nColors == None:
			a_nColors = self.m_oDictBlock["Color"].split(":")
		t_nRed = int(a_nColors[0])
		t_nGreen = int(a_nColors[1])
		t_nBlue = int(a_nColors[2])
		t_nAlpha = int(a_nColors[3])
		self.m_oBackColor = [t_nRed, t_nGreen, t_nBlue, t_nAlpha]
		
		if self.widgets.has_key("Rect"): #rect already drawn
			self.widgets["Rect"].set(fill_color_rgba=ColorFromList(self.m_oBackColor))
			
	def Move(self, dx, dy):
		# better translate than change block x and y properties
		# so that event.x and event.y are directly in block coordinates
		self.wGroup.translate(dx,dy)
		#newX = self.wGroup.get_property('x') + dx
		#newY = self.wGroup.get_property('y') + dy
		#self.wGroup.set_properties(x=newX, y=newY)
		self.ParentDiagram.onBlockMoved(self.m_nBlockCountId)
	
	def Redraw(self):
		self.Move(0, 0)
	
	def SetBorderColor(self, a_nColor=None):
		print "SetBorderColor is deprecated, fix this"

	def ToggleState(self,*args):
		print "ToggleState is deprecated, fix this"
	
	
	def GetPropertiesXML(self):
		return self.m_oPropertiesXML
	
	def SetPropertiesXML(self, outerProps):
		# only set properties values to preserve properties
		# set in block dictionnary
		for prop in outerProps.findAttributes('./property'):
			self.m_oPropertiesXML.setAttribute("./property/[@name='"+prop['name']+"']", 'value', prop['value'])

	
	#debug functions
	def PrintXML(self, *args):
		print self.m_oPropertiesXML.toString()

	def GetId(self):
		return self.m_nBlockCountId
	
	def GetType(self):
		return self.m_nBlockType
	
	def GetPos(self):
		transform = self.wGroup.get_simple_transform()
		return transform[1], transform[2]

	
	def PrintPOS(self, *args):
		print "(",self.wGroup.get_property('x'),",",self.wGroup.get_property('y'),")"

	"""
	Convert from item coordinates to world (aka canvas) coordinates.
	Gnomecanvas to goocanvas porting.
	"""
	def i2w(self, x, y):
		canvas = self.wGroup.get_canvas()
		return canvas.convert_from_item_space(self.wGroup, x, y)

	"""
	Check whether block has focus.
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
	Called when block gets keyboard focus.
	"""
	def onFocusIn(self, widget, target, event=None):
		self.m_bFocus = True
		self.onFocusChanged()

	"""
	Called when block loses keyboard focus.
	"""
	def onFocusOut(self, widget, target, event=None):
		self.m_bFocus = False
		self.onFocusChanged()
	
	"""
	Called when block properties are changed by properties window.
	"""
	def onPropertiesChanged(self):
		self.ParentDiagram.onBlockPropertiesChanged(self.m_nBlockCountId)


def Dist(p1,p2):
	return math.sqrt( math.pow(p2[0]-p1[0],2) + math.pow(p2[1]-p1[1],2))

def MakeArc(radius, edges, q=1):
	t_oPoints = []

	sin = math.sin	
	cos = math.cos
	pi2 = (math.pi/2)
	for i in xrange(edges + 1):
		n = (pi2 * i) / edges + pi2*q
		t_oPoints.append((cos(n) * radius, sin(n) * radius))
	
	return t_oPoints

def AlterArc(arc, offsetx=0, offsety=0):
	return [(x+offsetx, y+offsety) for x, y in arc]

def ColorFromList(rgba):
	color = int(rgba[0])*0x1000000+int(rgba[1])*0x10000+int(rgba[2])*0x100+(int(rgba[3])*0x01)
	return color

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

import GcdBlock
import GcdConnector
import time
import tempfile
import os
import shutil

from exceptions import AttributeError

import xmltree
import s2idirectory
import lvExtensions

UNDO_LEVELS_CNT = 20

class GcDiagram( GooCanvas.Canvas ):

	def __init__( self ):
		#TODO-fix self.__gobject_init__()
		GooCanvas.Canvas.__init__(self)

		# canvas size
		canvasWidth = 2000   
		canvasHeight = 1000

		self.set_bounds(0, 0, canvasWidth, canvasHeight)
		
		self.lastClickecPt = ( None, None)
		
		self.m_fPixels_per_unit = 1.0

		self.reset()
		self.savedXml = self.ToXml() # capture the current state
 		self.bIsUndoEnabled = False # undo enabled flag
		self.initUndo()
		
		self.show()
		
		#self.set_flags(Gtk.CAN_FOCUS)
		#self.grab_focus(self)
		#self.get_root_item().connect("event", self.canvas_root_event)#tem q ser o root() se nao ele pega os eventos antes de todu mundo! =]

		#self.connect("event", self.canvas_event)

		# canvas receives events before its children, so we need to use
		# a group as root item, so that its receives events after blocks
		# and connectors
		self.wGroup = GooCanvas.CanvasGroup()
		self.get_root_item().add_child(self.wGroup, -1)
		self.wGroup.connect("button-press-event", self.group_event)
		self.wGroup.connect("button-release-event", self.group_event)
		self.wGroup.connect("motion-notify-event", self.group_event)
		# add a rectangle as 'group background', else group will not
		# receive interior events
		#linedash = GooCanvas.CanvasLineDash([3.0])
		self.root_add(GooCanvas.CanvasRect(width=canvasWidth, height=canvasHeight, pointer_events=GooCanvas.CanvasPointerEvents.ALL, stroke_color='gray')) 

		self.m_sFilename = None
		self.createWorkingDir()
		
		self.m_sErrorLog = ""

		# turn on tooltips
		self.set_property('has-tooltip', True) 
		
		self.sessionManager = None
		
	def __del__(self):
		pass

	def stopSubProcess(self):
		# kill running subprocess if any
		self.SetSessionManager(None)

	def group_event(self, widget, target, event=None):
		"""debug
		print '*', __file__, 'group_event:'
		self.displayEvent(event)
		"""
		if event.type == Gdk.EventType.MOTION_NOTIFY:
			#print __file__, ', group_event(): MOTION_NOTIFY'
			if self.m_oCurrConnector <> None:
				t_Point = (event.x_root, event.y_root)
				#print __file__, ', group_event(): t_Point=', t_Point
				self.m_oCurrConnector.UpdateTracking(t_Point)

		if event.type == Gdk.EventType.BUTTON_PRESS:
			#print __file__, ', group_event(): BUTTON_PRESS'
			if event.button == 1:
				# abort eventual current connection
				#print "Aborting connection"
				self.AbortConnection()
				self.UpdateFlows()

		return False  # propagate event to upper level

	def RedrawBlocks(self):
		for blockIdx in self.m_oBlocks:#self.m_oBlocks is a dict!
			self.m_oBlocks[blockIdx].Redraw()
	
	def InsertBlock(self, a_nBlockType, x=None, y=None):
		"""
		Insert a block of the given type at the given relative position
		in the canvas.
		"""
		if x == None:
			x = 0
			y = 0

		xScroll, yScroll = self.getScrolledPosition()
		self.InsertBlockPosId(a_nBlockType, x+xScroll, y+yScroll, self.m_nBlockCountId)
		self.m_nBlockCountId += 1
		return self.m_nBlockCountId - 1
		
	def InsertBlockPosId(self, a_nBlockType, x, y, a_sBlockCountId):
		"""
		Insert a block of the given type and the given Id, at the given 
		absolute position in the canvas.
		"""
		t_oNewBlock = GcdBlock.GcdBlock(self, a_nBlockType, a_sBlockCountId)
		t_oNewBlock.Move(x, y)
		self.m_oBlocks[a_sBlockCountId] = t_oNewBlock
		self.setUndoSlot()

	def getScrolledPosition(self):
		"""
		Returned the scrolled position of the canvas.
		"""
		xScroll = self.get_parent().get_hadjustment().get_value()
		yScroll = self.get_parent().get_vadjustment().get_value()
		#DBG print 'DBG xScroll =', xScroll, '  yScroll =', yScroll
		return xScroll, yScroll
		

	"""
	Add new connector to diagram.
	fromId: origin block id.
	fromIdOut: origin block output id.
	returns: connector
	"""
	def addConnector(self, fromId, fromIdOut):
		idx = self.m_nConnectorCountId
		self.m_nConnectorCountId +=1
		connector = GcdConnector.GcdConnector(self, idx, fromId, fromIdOut)
		self.m_oConnectors[idx] = connector
		return connector

	def InsertReadyConnector(self, a_nFromId, a_nFromIdOut, a_nToId, a_nToIdIn):
		#print a_nFromId,",",a_nFromIdOut,",",a_nToId,",",a_nToIdIn
		t_oNewConn = self.addConnector(a_nFromId, a_nFromIdOut)
		t_oNewConn.SetEnd(a_nToId, a_nToIdIn)

		# check if connector is valid

		if not self.ValidConnector(t_oNewConn):
			print "Invalid Connector, not adding"
			t_oNewConn.DeleteConnector()
			return

		if not self.ConnectorTypesMatch(t_oNewConn):
			print "Output and Input types don't match"
			t_oNewConn.DeleteConnector()
			return

		# everything ok, keep connector
		self.UpdateFlows()
		
	def ClickedInput(self, a_nBlockCountId, a_nInput):
		#print "block" + str(a_nBlockCountId) + "_In" + str(a_nInput)
		if self.m_oCurrConnector <> None:
			self.m_oCurrConnector.SetEnd(a_nBlockCountId, a_nInput)

			# check if connector is valid

			if not self.ValidConnector(self.m_oCurrConnector):
				print "Invalid Connector, not adding"
				self.AbortConnection()
				return

			if not self.ConnectorTypesMatch(self.m_oCurrConnector):
				print "Output and Input types don't match"
				self.AbortConnection()
				return
					
			# everything ok, keep connector
			self.m_oCurrConnector = None
			self.UpdateFlows()
			self.setUndoSlot()

	def ConnectorTypesMatch(self, a_oConnector):
		outType = self.m_oBlocks[a_oConnector.fromBlock].m_oDictBlock["OutTypes"][a_oConnector.fromBlockOut + 1]['type']
		inType = self.m_oBlocks[a_oConnector.toBlock].m_oDictBlock["InTypes"][a_oConnector.toBlockIn + 1]['type']
		if not outType == inType:
			print "Types mismatch"
		return outType == inType
			

	def ValidConnector(self, newCon):
		#checks whether the new Cn links to a already used input (in this case, also invalidating cloned connectors)
		for oldCon in self.m_oConnectors.values():
			if oldCon == newCon:
				# skip the new one
				continue
			if oldCon.toBlock == newCon.toBlock \
					and oldCon.toBlockIn == newCon.toBlockIn:
				print "Cloned Connector"
				return False
		if newCon.toBlock == newCon.fromBlock:
			print "Recursive \"from future\" connector"
			return False
		return True

	def ClickedOutput(self, a_nBlockCountId, a_nOutput):
		#abort any possibly running connections
		self.AbortConnection()
		#print "block" + str(a_nBlockCountId) + "_Out" + str(a_nOutput)
		self.m_oCurrConnector = self.addConnector(a_nBlockCountId, a_nOutput)
		self.UpdateFlows()

	def AbortConnection(self):
		if self.m_oCurrConnector <> None:
			undoState = self.enableUndo(False)
			self.m_oCurrConnector.DeleteConnector()
			self.enableUndo(undoState)
			self.m_oCurrConnector = None

	"""
	Delete one connector.
	idx: connector index.
	"""
	def DeleteConnector(self, idx):
		self.m_oConnectors[idx].removeWidgets()
		connector = self.m_oConnectors.pop(idx)
		del connector
		self.UpdateFlows()
		self.setUndoSlot()

	"""
	Delete one block.
	blockCountId: block index.
	"""
	def DeleteBlock(self, blockCountId):
		#print "removing block ", blockCountId
		# removing related connectors
		for idx in self.m_oConnectors.keys():
			undoState = self.enableUndo(False)
			if self.m_oConnectors[idx].fromBlock == blockCountId or self.m_oConnectors[idx].toBlock == blockCountId:
				self.DeleteConnector(idx)
			self.enableUndo(undoState)

		#removing the block itself
		blockAtLimbo = self.m_oBlocks.pop(blockCountId)
		blockAtLimbo.removeWidgets()
		del blockAtLimbo
		
		self.UpdateFlows()
		self.setUndoSlot()

	"""
	Delete all blocks.
	"""
	def DeleteAllBlocks(self):
		blockIndexes = self.m_oBlocks.keys()
		for blockIdx in blockIndexes:
			self.DeleteBlock(blockIdx)

	"""
	"""
	def UpdateFlows(self):
		for checkTimeShifter in [False, True]:
			prevCount = -1
			newCount = self.CountFlowingComponents()
			while prevCount <> newCount:
				#print "newCount:",newCount
				#print "prevCount:",prevCount
				for blockIdx in self.m_oBlocks:#self.m_oBlocks is a dict!
					self.m_oBlocks[blockIdx].UpdateFlow(checkTimeShifter)
				#print "--------"
				
				for conn in self.m_oConnectors.values():
					conn.UpdateFlow()
				#print "-----------------"
				prevCount = newCount
				newCount = self.CountFlowingComponents()
		self.UpdateFlowsDisplays()
		
	def UpdateFlowsDisplays(self):
		for blockIdx in self.m_oBlocks:#self.m_oBlocks is a dict!
			self.m_oBlocks[blockIdx].UpdateFlowDisplay()
		for conn in self.m_oConnectors.values():
			conn.UpdateFlowDisplay()
	
	def GetConnectorsTo(self, a_nBlockCountId):
		result = []
		for conn in self.m_oConnectors.values():
			if conn.toBlock == a_nBlockCountId:
				result.append(conn)
		return result
	
	def CountFlowingComponents(self):
		count = 0
		for blockIdx in self.m_oBlocks:
			if self.m_oBlocks[blockIdx].m_bHasFlow:
				count += 1
		for conn in self.m_oConnectors.values():
			if conn.m_bHasFlow:
				count += 1
		return count
	
	def __BlockXMLOut(self, t_oBlockIdx, Properties, Network, a_bKeepNonFlowing=False):
		if self.m_oBlocks[t_oBlockIdx].GetState() or a_bKeepNonFlowing:
				#Properties += self.m_oBlocks[t_oBlockIdx].GetPropertiesXML().toString('./block') + "\n  "
				Properties += self.m_oBlocks[t_oBlockIdx].GetPropertiesXML().toString() + "\n  "
				Network += '<block type="' + str(self.m_oBlocks[t_oBlockIdx].GetType()) + '" id="' + str(self.m_oBlocks[t_oBlockIdx].GetId()) + '">\n'
				Network += "<inputs>\n"
				for t_nInputIdx in range(self.m_oBlocks[t_oBlockIdx].m_oDictBlock["Inputs"]):
					Network += '<input id="' + str(t_nInputIdx+1) + '"/>\n' #+1 pois o range eh de 0..x (precisamos do id 1...x+1)
				Network += "</inputs>\n"
	
				Network += "<outputs>\n"
				t_dConnectedOuts = {}
				for t_oConnector in self.m_oConnectors.values():
					if t_oConnector.toBlock == -1:
						# skip connector in progress
						continue
					if t_oConnector.fromBlock == self.m_oBlocks[t_oBlockIdx].GetId() and (self.m_oBlocks[t_oConnector.toBlock].GetState() or a_bKeepNonFlowing):
						Network += '<output id="' + str(t_oConnector.fromBlockOut+1) + '" inBlock="' + str(t_oConnector.toBlock) + '" input="' + str(t_oConnector.toBlockIn+1) + '"/>\n' #+1 pois o range eh de 0..x (precisamos do id 1...x+1)
						t_dConnectedOuts[t_oConnector.fromBlockOut] = 1
				for Output in range(self.m_oBlocks[t_oBlockIdx].m_oDictBlock["Outputs"]):
					if not t_dConnectedOuts.has_key(Output):
						Network += '<output id="' + str(Output+1) + '" inBlock="--" input="--"/>\n'
				Network += "</outputs>\n"
				Network += "</block>\n"
		return (Properties, Network)
	
	def GetProcessChain( self,a_bKeepNonFlowing=False ): #frontend will get only the valid chain although saving will include the invalid ones
		Properties = "<properties>\n  "
		Network = "<network>\n"

		##REAL TRICKY BUG solution here, source blocks must be processed in an earlier phase so assumptions as "live" or not will be valid 
		##throughout the whole code generation 
		
		for t_oBlockIdx in self.m_oBlocks:
			if self.m_oBlocks[t_oBlockIdx].m_bIsSource:
				(Properties, Network) = self.__BlockXMLOut(t_oBlockIdx,Properties, Network,a_bKeepNonFlowing)

		for t_oBlockIdx in self.m_oBlocks:
			if not self.m_oBlocks[t_oBlockIdx].m_bIsSource:
				(Properties, Network) = self.__BlockXMLOut(t_oBlockIdx,Properties, Network,a_bKeepNonFlowing)
		
		Properties += "</properties>\n"
		Network += "</network>\n"
		
		return Properties + Network

	def SetFilename( self, a_sFilename ):
		self.m_sFilename = a_sFilename

	def GetFilename( self ):
		return self.m_sFilename

	"""ELunused
	def LoadFromPopup(self, *args):
		filename = str(raw_input("Xunxo; Enter Filename:"))
		self.loadFromFile(filename)
	"""

	"""
	Reset diagram.
	"""
	def reset(self):
		self.m_oBlocks = {}
		self.m_oConnectors = {}
		self.m_oCurrConnector = None
		self.m_nSessionId = 0
		self.m_nBlockCountId = 1   # next block id
		self.m_nConnectorCountId = 1   # next connector id
		self.SetSessionManager(None)

	"""
	Load a processing chain from file.
	"""
	def loadFromFile(self, a_sFilename=None ):
		if a_sFilename <> None:
			self.SetFilename(a_sFilename)
		else:
			if self.m_sFilename == None:
				self.m_sFilename = "Cannot Load without filename"
				return False
		
		# reset diagram 
		self.reset()
		self.initUndo()
		# load .hrp project file
		t_oLoad = xmltree.xmlTree()
		t_oLoad.load(self.m_sFilename)
		assert t_oLoad.isValid(), 'failed to load file ' + self.m_sFilename
		undoState = self.enableUndo(False)
		result = self.loadFromXml(t_oLoad)
		self.savedXml = self.ToXml() # capture the current state
		self.enableUndo(undoState)
		self.setUndoSlot()
		return result
		
	"""
	Load a processing chain from an XML string. Used for undo feature.
	"""
	def loadFromString(self, xmlString):
		if xmlString is None:
			return
		# reset diagram
		self.reset()
		# load .hrp project file
		t_oLoad = xmltree.xmlTree()
		t_oLoad.fromString(xmlString)
		assert t_oLoad.isValid(), 'failed to load from xml string ' + xmlString
		undoState = self.enableUndo(False)
		self.loadFromXml(t_oLoad)
		self.enableUndo(undoState)

	"""
	Load a processing chain from an XML object.
	"""
	def loadFromXml(self, t_oLoad):
		#loading blocks on canvas
		blocks = t_oLoad.findSubTrees('./GcState/block')
		assert blocks != [], 'no ./GcState/block structure: %r'
		for block in blocks:
			id = int(block.getAttribute('.', 'id'))
			type = int(block.getAttribute('.', 'type'))
			posx = float(block.getAttribute('./position', 'x'))
			posy = float(block.getAttribute('./position', 'y'))
			self.InsertBlockPosId(type, posx, posy, id)
			self.m_nBlockCountId = max(self.m_nBlockCountId, id)
		self.m_nBlockCountId += 1
			
		#loading connectors on canvas
		blocks = t_oLoad.findSubTrees('./network/block')
		assert blocks != [], 'no ./network/block structure: %r'
		for block in blocks:
			blockId = int(block.getAttribute('.', 'id'))
			outputs = block.findAttributes('./outputs/output')
			for output in outputs:
				outputId = int(output['id'])
				inBlock = output['inBlock']
				input = output['input']
				if inBlock <> "--" and input <> "--":
					self.InsertReadyConnector(blockId, outputId-1, int(inBlock), int(input)-1) 
					#this "-1" are "paired" with those "+1" at line 286 (GetProcessChain:offset=14)
		
		#loading properties
		blocks = t_oLoad.findSubTrees('./properties/block')
		assert blocks != [], 'no ./properties/block structure: %r'
		for block in blocks:
			blockId = int(block.getAttribute('.', 'id'))
			t_sBlockProperties = '<?xml version="1.0" encoding="UTF-8"?>\n' + block.toString() + '\n'
			blockProperties = xmltree.xmlTree()
			blockProperties.fromString(t_sBlockProperties)
			assert blockProperties.isValid(), 'invalid block properties: %r'
			self.m_oBlocks[blockId].SetPropertiesXML(blockProperties)

		return True

	def SaveFromPopup( self, *args):
		self.Save()
		
	def Save(self, a_sFilename=None): #saving project
		if a_sFilename <> None:
			self.SetFilename(a_sFilename)
		if self.m_sFilename == None:
			self.m_sFilename = "Cadeia_" + str(time.time()) + ".hrp"
			
		t_sOutFile = self.ToXml()
		
		if self.m_sFilename.find(".hrp") == -1:
			self.m_sFilename += ".hrp"
		
		t_oSaveFile = open( str(self.m_sFilename) , "w" )
		t_oSaveFile.write(t_sOutFile)
		t_oSaveFile.close()

		self.savedXml = t_sOutFile # capture the current state
	
	def ToXml(self):
		"""
		Create one XML string fully representing the current diagram.
		"""
		# saving blocks current state 
		t_sGcState = "<GcState>\n"
		for blockIdx in self.m_oBlocks:
			t_sGcState += '\t<block type="' + str(self.m_oBlocks[blockIdx].GetType()) + '" id="' + str(self.m_oBlocks[blockIdx].GetId()) + '">\n'
			t_tPos = self.m_oBlocks[blockIdx].GetPos()
			t_sGcState += '\t\t<position x="' + str(t_tPos[0]) + '" y="' + str(t_tPos[1]) + '"/>\n'
			t_sGcState += '\t</block>\n'
		t_sGcState += "</GcState>\n"
		
		# saving processing chain (which includes blocks properties and connectors)
		t_sProcessingChain = self.GetProcessChain(True)
		
		xmlRepr = "<harpia>\n" + t_sGcState + t_sProcessingChain + "</harpia>\n"
		return xmlRepr

	def HasChanged(self):
		"""
		Checks if the diagram has been modified since last save.
		Returns True if the diagram has been modified, else False.
		"""
		if self.savedXml != self.ToXml():
			return True
		else:
			return False

	#------------------ Undo management ------------------------------

	"""
	Init undo states list.
	"""
	def initUndo(self):
		self.undoSlots = [ None ] * UNDO_LEVELS_CNT
		self.undoIndex = 0
		self.enableUndo()

	"""
	Move undo index forward or backward.
	move: +1 or -1
	redoMode: are we in redo mode ?
	"""
	def moveUndoIndex(self, move, redoMode=False):
		newIndex = self.undoIndex + move
		# validate move 
		if redoMode:
			# in redo mode we must stay inside filled slots range
			newIndex = max(newIndex, 0)
			newIndex = min(newIndex, UNDO_LEVELS_CNT - 1)
			# moving to an empty slot is not allowed
			if self.undoSlots[newIndex] is None:
				return 
		else:
			# write slot mode
			# don't move forward if current slot is empty
			if move > 0 and self.undoSlots[self.undoIndex] is None:
				return
			# ensure moving into valid boundaries, rotate queue if necessary
			newIndex = max(newIndex, 0)
			if newIndex >= UNDO_LEVELS_CNT:
				# rotate queue
				# ie remove the older slot and add a new slot
				self.undoSlots.pop(0)
				self.undoSlots.append(None)
				newIndex = UNDO_LEVELS_CNT - 1
		# move validated, update index
		self.undoIndex = newIndex
		#DBG print 'self.undoIndex=', self.undoIndex

	""" 
	Capture the current state in the undo states list.
	"""
	def setUndoSlot(self):
		if self.isUndoEnabled():
			# increment undo slot
			self.moveUndoIndex(+1)
			#DBG print 'set undo slot', self.undoIndex
			# store current processing chain 
			self.undoSlots[self.undoIndex] = self.ToXml()

	"""
	Restore undo slot at current undo index.
	"""
	def restoreUndoSlot(self):
		if self.undoSlots[self.undoIndex] is None:
			return
		undoState = self.enableUndo(False)
		self.DeleteAllBlocks()
		self.loadFromString(self.undoSlots[self.undoIndex])
		self.enableUndo(undoState)

	"""
	Undo, aka get the previous undo state in the (circular) list.
	"""
	def undo(self):
		# decrement undo slot
		self.moveUndoIndex(-1)
		# restore state
		#DBG print 'undo, restore slot', self.undoIndex
		self.restoreUndoSlot()

	"""
	Redo, aka get the next undo state in the (circular) list.
	"""
	def redo(self):
		# go to the next non-empty undo slot
		self.moveUndoIndex(+1, redoMode=True)
		#DBG print 'redo, restore slot', self.undoIndex
		self.restoreUndoSlot()

	"""
	Enable or disable undo recording.
	Return previous enabled state (True or False).
	"""
	def enableUndo(self, newState=True):
		prevState = self.bIsUndoEnabled
		self.bIsUndoEnabled = newState
		#DBG print 'self.bIsUndoEnabled=', self.bIsUndoEnabled
		return prevState

	"""
	Check if undo is currently enabled.
	"""
	def isUndoEnabled(self):
		return self.bIsUndoEnabled
	
	#----------------------------------------------------------------

	"""
	Display debug informations.
	"""
	def displayDebugInfos(self):
		# display infos on blocks
		print 'Debug informations:'
		#print 'in', __file__, 'self.m_oBlocks=', self.m_oBlocks
		for id in self.m_oBlocks:
			print '  block', id, 'of type', self.m_oBlocks[id].GetType(), '(' + self.m_oBlocks[id].Label + ')' 
			#print '  ', self.m_oBlocks[id].m_oDictBlock
		# display infos on connectors
		#print 'in', __file__, 'self.m_oConnectors=', self.m_oConnectors
		for id in self.m_oConnectors:
			print "  connector", str(id), 'from block', self.m_oConnectors[id].fromBlock, 'to block', self.m_oConnectors[id].toBlock
		
	"""
	Return index of block with focus.
	Return None if no block has focus.
	"""
	def GetBlockOnFocus(self):
		for blockIdx in self.m_oBlocks:
			if self.m_oBlocks[blockIdx].hasFocus():
				return blockIdx

	def SetIDBackendSession(self, a_nSessionId):
		self.m_nSessionId = a_nSessionId

	def GetIDBackendSession(self):
		return self.m_nSessionId
	
	def setDirName(self, dirName):
		"""
		Set working dir name.
		"""
		self.m_sDirName = dirName

	def getDirName(self):
		"""
		Get working dir name.
		"""
		return self.m_sDirName

	def removeDir(self):
		"""
		Remove working dir.
		"""
		shutil.rmtree(self.getDirName())
	
	def createWorkingDir(self):
		"""
		Create working dir.
		"""
		dirNamePattern = 'starling_'
		fullPattern = dirNamePattern
		workingDirsPlace = lvExtensions.getWorkingDirsPlace()
		if workingDirsPlace:
			fullPattern = os.path.join(workingDirsPlace, dirNamePattern)
		try:
			# try to use the given directories place 
			dirName = tempfile.mkdtemp(prefix=fullPattern)
		except:
			# if it failed use the standard place
			print 'Warning: failed to create temporary working directory in \'' + workingDirsPlace + '\'. Using default location.'
			dirName = tempfile.mkdtemp(prefix=dirNamePattern)
		self.setDirName(dirName)

	def Export2Png(self, filepath="diagrama.png"):
		(x,y,t_nWidth,t_nHeight,t_nDepth) = self.window.get_geometry()
		
		t_oPixbuf = Gtk.gdk.Pixbuf(Gtk.gdk.COLORSPACE_RGB,False,8,t_nWidth,t_nHeight)
		t_oBuffer = t_oPixbuf.get_from_drawable(self.window, self.get_colormap(),0, 0, 0, 0, t_nWidth, t_nHeight)
		# get_from_drawable(GdkWindow src, GdkColormap cmap, int src_x, int src_y, int dest_x, int dest_y, int width, int height);
		t_oBuffer.save(filepath, "png")
		#bugs:
		# *nao considera o que estiver fora do scroll region
		# *da um printScreen somente então pega qlqr outra coisa q estiver no caminho (incluindo o proprio menu ali do FILE)
		# *aparentemente é a maneira errada.

	def SetErrorLog(self, a_sErrorLog):
		self.m_sErrorLog = a_sErrorLog
	
	def Append2ErrorLog(self, a_sErrorLog):
		self.m_sErrorLog += a_sErrorLog
	
	def GetErrorLog(self):
		return self.m_sErrorLog
		
	def ZoomIn(self):
		self.m_fPixels_per_unit *= 1.1
		self.set_pixels_per_unit(self.m_fPixels_per_unit)
	
	def ZoomOut(self):
		self.m_fPixels_per_unit *= 0.9
		self.set_pixels_per_unit(self.m_fPixels_per_unit)
	
	def ZoomOrig(self):
		self.m_fPixels_per_unit = 1.0
		self.set_pixels_per_unit(self.m_fPixels_per_unit)

	#def RightClick(self, a_oEvent):
		#pass
		#t_oMenu = Gtk.Menu()
	
		#t_oMenuItem = Gtk.MenuItem("Save Diagram")
		#t_oMenuItem.connect("activate", self.SaveFromPopup)
		#t_oMenu.append(t_oMenuItem)

		#t_oMenuItem = Gtk.MenuItem("Load Diagram")
		#t_oMenuItem.connect("activate", self.LoadFromPopup)
		#t_oMenu.append(t_oMenuItem)
		
		#t_oMenuItem = Gtk.SeparatorMenuItem()
		#t_oMenu.append(t_oMenuItem)
		
		#t_oMenuItem = Gtk.MenuItem("Delete Diagram")
		#t_oMenuItem.connect("activate", self.SaveFromPopup)
		#t_oMenu.append(t_oMenuItem)

		#t_oMenuItem = Gtk.SeparatorMenuItem()
		#t_oMenu.append(t_oMenuItem)
		
		## Shows the menu
		#t_oMenu.show_all()
		#t_oMenu.popup(None, None, None, a_oEvent.button, a_oEvent.time)

	def root_add(self, item, position=-1):
		#self.get_root_item().add_child(item) #TODO-rm
		self.wGroup.add_child(item, position)

	"""
	Called when a block is moved.
	blockId: index of moved block.
	"""
	def onBlockMoved(self, blockId):
		for idx in self.m_oConnectors.keys():
			if self.m_oConnectors[idx].fromBlock == blockId or self.m_oConnectors[idx].toBlock == blockId:
				self.m_oConnectors[idx].UpdateConnector()

	"""
	Called when the block stop being moved by user.
	blockId: index of moved block.
	"""
	def onBlockStopMoving(self, blockId):
		self.setUndoSlot()
	
	"""
	Called when one block properties have changed.
	"""
	def onBlockPropertiesChanged(self, blockId):
		self.setUndoSlot()

	"""
	Display event info to help debugging.
	"""
	def displayEvent(self, event):
		if event.type == Gdk.EventType.BUTTON_PRESS:
			print 'event.type= BUTTON_PRESS'
			print '     .button=', event.button
		elif event.type == Gdk.EventType.MOTION_NOTIFY:
			print 'event.type= MOTION_NOTIFY'
		elif event.type == Gdk.EventType.BUTTON_RELEASE:
			print 'event.type= BUTTON_RELEASE, button=', event.button
		elif event.type == Gdk.EventType._2BUTTON_PRESS:
			print 'event.type= _2BUTTON_PRESS'
		elif event.type == Gdk.EventType.ENTER_NOTIFY:
			print 'event.type= ENTER_NOTIFY'
		elif event.type == Gdk.EventType.LEAVE_NOTIFY:
			print 'event.type= LEAVE_NOTIFY'
		elif event.type == Gdk.EventType.KEY_PRESS:
			print 'event.type= KEY_PRESS'
			print '     .keyval=', event.keyval
		else:
			print 'event.type= ?'

		try: 
			print '     .x_root=', event.x_root
		except AttributeError:
			pass

		try: 
			print '     .y_root=', event.y_root
		except AttributeError:
			pass

		try: 
			print '     .x=', event.x
		except AttributeError:
			pass

		try: 
			print '     .y=', event.y
		except AttributeError:
			pass

	def SetSessionManager(self, sessionManager):
		#print 'GcDiagram.SetSessionManager'
		# delete current session manager if any
		try:
			self.sessionManager.close()
		except AttributeError:
			pass

		self.sessionManager = sessionManager


def ColorFromList(rgba):
	color = int(rgba[0])*0x1000000+int(rgba[1])*0x10000+int(rgba[2])*0x100+(int(rgba[3])*0x01)
	return color


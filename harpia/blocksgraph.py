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
# Store a blocks graph in memory.
# Manage block properties and connections between blocks
#

class blocksGraph:

	def __init__(self):
		self.graph = {}
	
	"""
	Build blocks list, and set properties.
	"""
	def setPropertiesFromXml(self, blocks):
		for block in blocks:
			blockId = int(block.getAttribute('.', 'id'))
			self.graph[blockId] = {}
			self.graph[blockId]['type'] = int(block.getAttribute('.', 'type'))
			self.graph[blockId]['inputs'] = []
			self.graph[blockId]['outputs'] = []
			self.graph[blockId]['properties'] = {}
			self.graph[blockId]['depth'] = 0
			for prop in block.findAttributes('./property'):
				self.graph[blockId]['properties'][prop['name']] = prop['value']
			# we don't need 'state' property
			#self.graph[blockId]['properties'].pop('state')

	"""
	Set connections between blocks.
	"""
	def setConnectionsFromXml(self, blocks):
		for block in blocks:
			blockId = int(block.getAttribute('.', 'id'))

			# parse outputs
			for output in block.findAttributes('./outputs/output'):
				if output['inBlock'] != '--':
					outputId = int(output['id'])
					toBlockId = int(output['inBlock'])
					toInputId = int(output['input'])
					# ouput is stored as (output id, target block id, target block input id)
					self.graph[blockId]['outputs'].append((outputId,toBlockId, toInputId))
					# input is stored as (input id, origin block id, origin ouput id)
					self.graph[toBlockId]['inputs'].append((toInputId,blockId, outputId))

	"""
	Compute each block depth inside graph.
	"""
	def computeDepth(self):
		# search blocks without input
		blocksToMark = set()
		for blockId, block in self.graph.iteritems():
			if not block['inputs']:
				blocksToMark.add(blockId)
		# go through graph and set depth, starting by blocks with no input
		depth = 1
		while blocksToMark:
			nextBlocks = set()
			for blockId in blocksToMark:
				self.graph[blockId]['depth'] = depth
				for outId, toBlock, inId in self.graph[blockId]['outputs']:
					nextBlocks.add(toBlock)

			depth += 1
			blocksToMark = nextBlocks
			"""
			# debugging
			print '-------------------'
			for blockId, block in self.graph.iteritems():
				print 'blockId =', blockId, '  depth=', block['depth']	
			print 'blocksToMark=', blocksToMark
			"""

	"""
	Return a list of block Ids, sorted accordingly to their depth.
	"""
	def getSortedBlocks(self):
		sortedBlocks = []
		depth = 1
		found = True
		while found:
			found = False
			for blockId, block in self.graph.iteritems():
				if block['depth'] == depth:
					sortedBlocks.append(blockId)
					found = True
			depth += 1
		return sortedBlocks

	"""
	Build blocks graph from Xml representation.
	"""
	def buildFromXml(self, xmlChain):
		self.setPropertiesFromXml(xmlChain.findSubTrees('./properties/block'))
		self.setConnectionsFromXml(xmlChain.findSubTrees('./network/block'))
		self.computeDepth()
		#print 'in', __file__, '.buildFromXml(), self.graph=', self.graph

	"""
	Get block from graph by id
	"""
	def getBlock(self, blockId):
		return self.graph[blockId]

	"""
	Get blocks list from graph
	"""
	def getBlocksList(self):
		return self.graph
	

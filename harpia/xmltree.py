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
# Parse, store and give access to an xml structure.
#

import xml.etree.ElementTree as ET

class xmlTree:

	def __init__(self):
		self.root = None
	
	"""
	Load xml structure from file.
	"""
	def load(self, fileName):
		try:
			tree = ET.parse(fileName)
			self.root = tree.getroot()
		except:
			self.root = None

	"""
	Load xml structure from string.
	"""
	def fromString(self, string):
		try:
			self.root = ET.fromstring(string)
		except:
			self.root = None

	"""
	Convert xml structure to string.
	"""
	def toString(self, path=None):
		try:
			if not path:
				start = self.root
			else:
				start = self.root.find(path) 
			return ET.tostring(start)
		except:
			return None

	"""
	Find elements attributes.
	@param  path  path to element(s) as a string.
	@return  list of dictionnaries.
	"""
	def findAttributes(self, path):
		try:
			elements = self.root.findall(path)
			attributes = []
			for elt in elements:
				if elt.attrib:
					attributes.append(elt.attrib)
			return attributes
		except:
			return []

	"""
	Find elements text.
	@param  path  path to element(s) as a string. 
	"""
	def findTexts(self, path):
		try:
			elements = self.root.findall(path)
			texts = []
			for elt in elements:
				texts.append(elt.text)
			return texts
		except:
			return []

	"""
	Get attribute value.
	@param  path  path to element
	@param  attribute  attribute name
	"""
	def getAttribute(self, path, attribute):
		element = self.root.find(path)
		return element.get(attribute)

	"""
	Get text value.
	Return None if element does not exist.
	@param  path  path to element
	"""
	def getText(self, path):
		element = self.root.find(path)
		if element is None:
			return None
		else:
			return element.text

	"""
	Set attribute value.
	@param  path  path to element
	@param  attribute  attribute name
	@param  value  attribute value. 
	"""
	def setAttribute(self, path, attribute, value):
		element = self.root.find(path)
		element.set(attribute, value)

	"""
	Find xml subtrees matching the path.
	@param  path  path to match
	@return  subtrees list 
	"""
	def findSubTrees(self, path):
		try:
			elements = self.root.findall(path)
			subtrees = []
			for elt in elements:
				subtree = xmlTree()
				subtree.fromString(ET.tostring(elt))
				if subtree.isValid():
					subtrees.append(subtree)
			return subtrees
		except:
			return []
		
	"""
	Returns True if object contains a valid xml tree.
	"""
	def isValid(self):
		if self.root is not None:
			return True
		else:
			return False


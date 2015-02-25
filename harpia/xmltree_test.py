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
# Test xml parser.
#

import xmltree

doc = xmltree.xmlTree()
print doc.toString()

doc.load('../app_data/blocks.public/read_image.xml')
print doc.toString()
print doc.toString('./block')


print 'block attrib=', doc.findAttributes('./block')
print 'property attrib=', doc.findAttributes('./block/property')
print 'input attrib=', doc.findAttributes('./input')
print 'output attrib=', doc.findAttributes('./output')
print 'label attrib=', doc.findAttributes('./label')

print 'block text=', doc.findTexts('./block')
print 'label text=', doc.findTexts('./label')

print 'set existing attribute value'
print 'before=', doc.getAttribute('./block', 'id')
doc.setAttribute('./block', 'id', '25')
print 'after=', doc.getAttribute('./block', 'id')
print 'block attrib=', doc.findAttributes('./block')

print 'set NON existing attribute value'
doc.setAttribute('./label', 'id', '25')

print 'ok'

print
print 'test2'
hrp = xmltree.xmlTree()
hrp.load('../test/01_readfile-savefile.hrp')
for subtree in hrp.findSubTrees('./network/block'):
	print
	print subtree.toString()
	print 'block attrib=', subtree.findAttributes('.')
	print 'inputs=', subtree.findAttributes('./inputs/input')
	print 'outputs=', subtree.findAttributes('./outputs/output')

print 'ok2'

"""
print doc.getAttrib(['block', 'type'])
print doc.getAttrib(['block', 'property', 'name'])
print doc.getAttrib(['output', 'type'])
print doc.getAttrib(['output', 'bidon'])

doc.setAttrib(['block', 'property', 'name'], 'test1')
print doc.getAttrib(['block', 'property', 'name'])

print doc.getAttrib(['bidon', 'type'])
"""

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

import time
import sys
import os
import subprocess
import xmltree
import glib
import gtk

import codegenerator

class s2iSessionManager:
	
	def __init__(self, workingDir):
		self.m_sSessionId = str(time.time())
		self.m_sDirName = workingDir  # full path tmp dir
		self.m_sOldPath = os.path.realpath(os.curdir)
		self.subProcess = None

	def close(self):
		#print 's2iSessionManager.close'
		self.killSubProcess()

	def StoreXML(self , a_lsXML = ["<harpia></harpia>"]):
		#try:
		os.chdir(self.m_sDirName)
		t_oStoreFile = file('processingChain.xml', 'w')
		t_oStoreFile.write(a_lsXML[0])
		t_oStoreFile.close()
		#except:
			#print "Problems Saving xml"
		#comes back to original dir
		os.chdir(self.m_sOldPath)
		return
	
	def RunProject(self, batchModeOn):
		#changes dir...
		os.chdir(self.m_sDirName)
		print
		self.subProcess = codegenerator.buildAndRunProject('processingChain.xml')
		if batchModeOn:
			# batch mode: wait end of subprocess
			try:
				self.subProcess.wait()
			except AttributeError:
				pass

		#comes back to original dir
		os.chdir(self.m_sOldPath)
		return

	def killSubProcess(self):
		#print 'killSubProcess'
		# kill currently running subprocess, if any 
		if os.name != 'nt':
			# linux
			# use python subprocess.kill
			try:
				if self.subProcess.poll() is None:
					self.subProcess.kill()
			except AttributeError:
				pass
		else:
			# windows
			# use system kill
			try:
				if self.subProcess.poll() is None:
					subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.subProcess.pid)])
			except AttributeError:
				pass

		# force events processing
		while gtk.events_pending():
			gtk.main_iteration()

	def NewInstance(self , batchModeOn, a_lsXML = ["<harpia></harpia>"]):
		self.StoreXML(a_lsXML)
		self.RunProject(batchModeOn)
		return


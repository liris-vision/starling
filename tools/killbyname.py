#!/usr/bin/env python
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
#
# Kill one process given its name, if it is unique.
# Return:
#   0 if the process was running and has been killed
#   1 if the process is not running
#   2 if several processes have the same name (they are not killed)
#

import argparse
import subprocess
import sys
import os
import signal


def getProcessList(processName):
	"""
	Get processes list by name.
	"""

	# get processes list
	if os.name == 'posix':
		# Linux & MacOS
		command = 'ps -e | grep " %s$"' % processName
	elif os.name == 'nt':
		# Windows 7
		command = 'tasklist /NH /FI "imagename eq %s"' % processName

	p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
	output = p.communicate()[0]

	# transform command output into list and remove empty lines
	output = [s for s in output.splitlines() if s]
	
	if os.name == 'nt' and output and 'aucune' in output[0]:
		# on Windows tasklist returns an error message
		# if the process is not found
		output = []

	return output

	
def getPID(psInfo):
	"""
	Extract the PID form the process informations.
	"""
	if os.name == 'posix':
		# Linux & MacOS
		pid = int(psInfo.split()[0])
	elif os.name == 'nt':
		# Windows 7
		pid = int(psInfo.split()[1])

	return pid


def kill(pid):
	"""
	Kill a process given its PID.
	"""
	if os.name == 'posix':
		# Linux & MacOS
		os.kill(pid, signal.SIGTERM)
	elif os.name == 'nt':
		# Windows 7
		os.system('taskkill /PID ' + str(pid))


def main(argv):
	# parse command line arguments
	argParser = argparse.ArgumentParser(description='Kill one running process.')
	argParser.add_argument('process_name')
	args, unknown = argParser.parse_known_args()

	# check that the process is running
	processList = getProcessList(args.process_name)

	if not processList:
		# process is not running
		sys.exit(1)

	# check that the process is unique
	if len(processList) > 1:
		# there are several processes of the same name
		sys.exit(2)

	# get process id
	pid = getPID(processList[0])

	# kill process
	kill(pid)

	# everything is ok
	sys.exit(0)


if __name__ == '__main__':
    main(sys.argv)


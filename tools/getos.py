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
# Get OS version informations.
#

import platform

fullOsVersion = platform.platform()

if 'x86_64-with-Ubuntu-14.04' in fullOsVersion:
	shortVersion = 'u1404-64'
elif 'x86_64-with-Ubuntu-12.04' in fullOsVersion:
	shortVersion = 'u1204-64'
elif 'Windows-7' in fullOsVersion:
	shortVersion = 'w7'
else:
	shortVersion = 'unknown'

print shortVersion


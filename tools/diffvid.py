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
# Compare two videos image by image.
# Return 0 if the videos are identical, 
# return 1 if they are different.
#

import sys
import cv2
import numpy

import diffimg


def areIdentical(vid1, vid2):
	vid1FrameCnt = vid1.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)
	vid2FrameCnt = vid2.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)
	if not vid1FrameCnt == vid2FrameCnt:
		print 'Size mismatch.'
		print 'Video1 has', vid1FrameCnt, 'frames.'
		print 'Video2 has', vid2FrameCnt, 'frames.'
		return False

	vid1Definition = (vid1.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH), vid1.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))
	vid2Definition = (vid2.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH), vid2.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))
	if not vid1Definition == vid2Definition:
		print 'Image definition mismatch.'
		print 'Video1 has definition', vid1Definition, '.'
		print 'Video2 has definition', vid2Definition, '.'
		return False

	frameCnt = 0
	while vid1.grab() and vid2.grab():
		frameCnt += 1
		retval1, img1 = vid1.retrieve()
		retval2, img2 = vid2.retrieve()
		if not diffimg.areIdentical(img1, img2):
			print 'Videos are different.'
			print 'First difference at frame #' + str(frameCnt)
			return False

	# videos are identical
	return True

def diffVideos(name1, name2):
	vid1 = cv2.VideoCapture(name1)
	if not vid1.isOpened():
		print 'Failed to read', name1, '.'
		sys.exit(1)
	
	vid2 = cv2.VideoCapture(name2)
	if not vid2.isOpened():
		print 'Failed to read', name2, '.'
		sys.exit(1)
	
	if areIdentical(vid1, vid2):
		sys.exit(0)
	else:
		sys.exit(1)
	

def main(argv):
	if len(argv) != 3:
		print 'Compare two videos, image by image.'
		print 'Usage: ', argv[0], ' path_to_video1 path_to_video2'
		sys.exit(1)
	
	diffVideos(argv[1], argv[2])


if __name__ == '__main__':
    main(sys.argv)

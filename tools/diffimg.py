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
# Compare two images pixel by pixel.
# Return 0 if the images are identical, 
# return 1 if they are different.
#

import sys
import cv2
import numpy
import argparse


def printFirstDifferences(im1, im2, maxCount=10):
	"""
	Display maxCount first differences between image 1 and 2.
	"""
	print 'Differences between images:'
	print ' ' + '(row,col)'.ljust(16) + 'image1'.ljust(20) + 'image2'.ljust(20)

	try:
		# multi-channels image
		height, width, nbChannel = im1.shape
	except ValueError:
		# single channel image, no depth dimension
		height, width = im1.shape
		nbChannel = 1

	count = 0
	for r in range(0, height):
		for c in range(0, width):
			if not numpy.array_equal(im1[r,c], im2[r,c]):
				print ' ' + ('(' + str(r) + ',' + str(c) + ')').ljust(16) + \
					str(im1[r,c]).ljust(20) + str(im2[r,c]).ljust(20)
				count += 1
				if count >= 10:
					print ' ...'
					return


def areIdentical(im1, im2):
	if im1.shape != im2.shape:
		print 'Size mismatch.'
		print 'Size of image1 is', im1.shape, '.'
		print 'Size of image2 is', im2.shape, '.'
		return False

	if numpy.array_equal(im1, im2):
		return True
	else:
		printFirstDifferences(im1, im2)
		return False


def main(argv):
	# parse command line arguments
	argParser = argparse.ArgumentParser(description='Compare two images, pixel by pixel.')
	argParser.add_argument('path_to_image1')
	argParser.add_argument('path_to_image2')
	argParser.add_argument('-d', '--display', help='display images', action='store_true')
	args, unknown = argParser.parse_known_args()

	# load first image
	im1 = cv2.imread(args.path_to_image1, -1)
	if im1 is None:
		print 'Failed to read ', args.path_to_image1
		sys.exit(1)

	# load second image
	im2 = cv2.imread(args.path_to_image2, -1)
	if im2 is None:
		print 'Failed to read ', args.path_to_image2
		sys.exit(1)

	# compare images
	identical = areIdentical(im1, im2)
	
	# display images
	if args.display:
		cv2.imshow(args.path_to_image1, im1)
		cv2.imshow(args.path_to_image2, im2)
		cv2.waitKey(0)

	# set exit status
	if identical:
		sys.exit(0)
	else:
		sys.exit(1)


if __name__ == '__main__':
    main(sys.argv)


# material

"""
# diff img avec OpenCV
# pb: cmp est 3 canaux, countNonZero veut 1 seul canal 
cmp = cv2.compare(im1, im2, cv2.CMP_NE)
print 'cmp=', cmp
print 'cmp.shape=', cmp.shape
diffCnt = cv2.countNonZero(cmp)
if diffCnt > 0:
	print 'Images are different (', diffCnt, ' pixels).'
	sys.exit(1)
else:
	# images are identical
	sys.exit(0)
"""

"""
# diff img détaillé anev numpy
# pb : résultat en désordre, pas trivial à trier
def uniqRows(a):
	'''
	Remove duplicated lines from a numpy 2D array.
	'''
	ncols = a.shape[1]
	dtype = numpy.dtype((numpy.void, a.dtype.itemsize * ncols))
	b = numpy.ascontiguousarray(a).view(dtype)
	_, idx = numpy.unique(b, return_index=True)
	unique_a = a[idx]
	return unique_a

nonz = numpy.nonzero(im1 - im2)
print nonz
print "nonz=", nonz[0:2]
print "nonztr=", numpy.transpose(nonz[0:2])
print "uniq=", numpy.sort(uniqRows(numpy.transpose(nonz[0:2])), 1)
#pb : en désordre !
"""

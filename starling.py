#!/usr/bin/env python
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

#
# Starling launching script.
#

# Libraries 
import gobject
import gtk
import sys
import os
import argparse
import locale
import cairo

from harpia import harpiagcfrontend
from harpia import lvExtensions

from time import sleep

class splashScreen():
	def __init__(self):
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		
		self.window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_UTILITY)
		self.window.set_position(gtk.WIN_POS_CENTER)
		self.window.set_decorated(0)
		self.window.set_default_size(960, 650)
		
		self.window.set_events(gtk.gdk.ALL_EVENTS_MASK)
		
		# Initialize colors, alpha transparency		
		self.window.set_app_paintable(1)
		self.gtk_screen = self.window.get_screen()
		colormap = self.gtk_screen.get_rgba_colormap()
		if colormap == None:
			colormap = self.gtk_screen.get_rgb_colormap()
		gtk.widget_set_default_colormap(colormap)
		if not self.window.is_composited():
			self.supports_alpha = False
		else:
			self.supports_alpha = True
		
		self.w,self.h = self.window.get_size()
		
		self.window.connect("expose_event", self.expose)
		#self.window.connect("destroy", gtk.main_quit)
		
 
	def expose (self, widget, event):
		self.ctx = self.window.window.cairo_create()
		# set a clip region for the expose event, XShape stuff
		self.ctx.save()
		if self.supports_alpha == False:
			self.ctx.set_source_rgb(1, 1, 1)
		else:
			self.ctx.set_source_rgba(1, 1, 1,0)
		self.ctx.set_operator (cairo.OPERATOR_SOURCE)
		self.ctx.paint()
		self.ctx.restore()
		self.ctx.rectangle(event.area.x, event.area.y,
				event.area.width, event.area.height)
		self.ctx.clip()
		self.draw_image(self.ctx,0,0,'base.png')
 
	def setup(self):
		# Set menu background image
		self.background =  gtk.Image()
		self.frame = gtk.Fixed()
		self.window.add (self.frame)
		
		# Set window shape from alpha mask of background image
		w,h = self.window.get_size()
		if w==0: w = 800
		if h==0: h = 650
		self.w = w
		self.h = h
		self.pixmap = gtk.gdk.Pixmap (None, w, h, 1)
		ctx = self.pixmap.cairo_create()
		# todo: modify picture source
		#self.bgpb = gtk.gdk.pixbuf_new_from_file('base.png')
		ctx.save()
		ctx.set_source_rgba(1, 1, 1,0)
		ctx.set_operator (cairo.OPERATOR_SOURCE)
		ctx.paint()
		ctx.restore()
		self.draw_image(ctx,0,0,'base.png')
		
		if self.window.is_composited():
			ctx.rectangle(0,0,w,h)
			ctx.fill()			
			self.window.input_shape_combine_mask(self.pixmap,0,0)
		else:
			self.window.shape_combine_mask(self.pixmap, 0, 0)
 
	def draw_image(self,ctx,x,y, pix):
		"""Draws a picture from specified path with a certain width and height"""
 
		ctx.save()
		ctx.translate(x, y)	
		pixbuf = gtk.gdk.pixbuf_new_from_file(pix)
		format = cairo.FORMAT_RGB24
		if pixbuf.get_has_alpha():
			format = cairo.FORMAT_ARGB32
		#if Images.flip != None:
		#	pixbuf = pixbuf.flip(Images.flip)
	
		iw = pixbuf.get_width()
		ih = pixbuf.get_height()
		image = cairo.ImageSurface(format, iw, ih)
		image = ctx.set_source_pixbuf(pixbuf, 0, 0)
		
		ctx.paint()
		puxbuf = None
		image = None
		ctx.restore()
		ctx.clip()
 
	def show_window(self):
		self.window.show_all()
		while gtk.events_pending():
			gtk.main_iteration()
		self.window.present()
		self.window.grab_focus()
		self.p = 1


def main(argv):

	"""
	Parse the command line arguments, then start the application.
	"""

	# set working directory to current script directory
	os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))
	lvExtensions.init()

	# force locale to US to avoid (partial) translation of menus and buttons
	locale.setlocale(locale.LC_ALL, 'C')

	# avoid threads + gtk issues
	gobject.threads_init()

	# initializations
	os.environ['HARPIA_DATA_DIR'] = lvExtensions.harpia_data_dir
	batchMode = False
	experimentalMode = False
	userFiles = []

	# parse command line arguments
	argParser = argparse.ArgumentParser()
	argParser.add_argument('-b', '--batch', help='turn batch mode on', action='store_true')
	argParser.add_argument('-e', '--experimental', help='active experimental blocks', action='store_true')
	argParser.add_argument('-c', '--config-file', help='configuration file')
	args, unknown = argParser.parse_known_args()
	userFiles = unknown
	if args.batch and userFiles:
		batchMode = True
	if args.experimental:
		experimentalMode = True
	if args.config_file:
		lvExtensions.setConfigurationFileName(os.path.abspath(args.config_file))
	
	if not batchMode:
		m = splashScreen()
		m.setup()
		m.show_window()
		sleep ( 2 )

	## initialize the frontend
	HarpiaFrontend = harpiagcfrontend.S2iHarpiaFrontend(userFiles, batchMode, experimentalMode)
	
	if not batchMode:
		m.window.set_transient_for(HarpiaFrontend.gtkTopWindow)
		HarpiaFrontend.show( center=0 )
		sleep ( 1 )
		m.window.destroy ()
		#splScr.window.destroy() 
		gtk.main()
	
	#----------------------------------------------------------------------

if __name__ == '__main__':
    main(sys.argv)
    
    #----------------------------------------------------------------------

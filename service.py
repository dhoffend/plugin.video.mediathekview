# -*- coding: utf-8 -*-
#
# MIT License
#
# Copyright (c) 2017-2018, Leo Moll
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# -- Imports ------------------------------------------------
from __future__ import unicode_literals

from resources.lib.kodi.KodiAddon import KodiService
from resources.lib.kodi.KodiAddon import KodiInterlockedMonitor

from resources.lib.notifier import Notifier
from resources.lib.settings import Settings
from resources.lib.updater import MediathekViewUpdater

# -- Classes ------------------------------------------------
class MediathekViewMonitor( KodiInterlockedMonitor ):
	def __init__( self, service, setting_id ):
		super( MediathekViewMonitor, self ).__init__( service, setting_id )
		self.logger		= service.getNewLogger( 'Monitor' )

	def onSettingsChanged( self ):
		self.service.ReloadSettings()

class MediathekViewService( KodiService ):
	def __init__( self ):
		super( MediathekViewService, self ).__init__()
		self.setTopic( 'Service' )
		self.settings	= Settings()
		self.notifier	= Notifier()
		self.monitor	= MediathekViewMonitor( self, 'instanceid' )
		self.updater	= MediathekViewUpdater( self.getNewLogger( 'Updater' ), self.notifier, self.settings, self.monitor )

	def Init( self ):
		self.info( 'Init (instance id: {})', self.monitor.instance_id )
		self.monitor.RegisterInstance()
		self.updater.Init()
		self.settings.ResetUserActivity()

	def Run( self ):
		self.info( 'Starting up... (instance id: {})', self.monitor.instance_id )
		while not self.monitor.abortRequested():
			if self.settings.Reload() is True:
				# database configuration changed
				self.info( '===== Database Configuration has changed - Reloading the updater =====')
				self.updater.Reload()

			updateop = self.updater.GetCurrentUpdateOperation()
			if updateop == 1:
				# full update
				self.info( 'Initiating full update...' )
				self.updater.Update( True )
			elif updateop == 2:
				# differential update
				self.info( 'Initiating differential update...' )
				self.updater.Update( False )
			# Sleep/wait for abort for 60 seconds
			if self.monitor.waitForAbort( 15 ):
				# Abort was requested while waiting. We should exit
				break
		self.info( 'Shutting down... (instance id: {})', self.monitor.instance_id )

	def Exit( self ):
		self.info( 'Exit (instance id: {})', self.monitor.instance_id )
		self.updater.Exit()
		self.monitor.UnregisterInstance()

	def ReloadSettings( self ):
		# self.info("===== RELOAD SETTINGS =====")
		# TODO: support online reconfiguration
		#       currently there is a bug in Kodi: this event is only
		#       triggered if the reconfiguration happen inside the
		#       addon (via setSetting). If teh user changes something
		#       via the settings page, NOTHING WILL HAPPEN!
		pass

# -- Main Code ----------------------------------------------
if __name__ == '__main__':
	service = MediathekViewService()
	service.Init()
	service.Run()
	service.Exit()
	del service

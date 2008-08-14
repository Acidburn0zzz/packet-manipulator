#!/usr/bin/env python                                   
# -*- coding: utf-8 -*-                                 
# Copyright (C) 2008 Adriano Monteiro Marques           
#                                                       
# Author: Francesco Piccinno <stack.box@gmail.com>      
#                                                       
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or   
# (at your option) any later version.                                 
#                                                                     
# This program is distributed in the hope that it will be useful,     
# but WITHOUT ANY WARRANTY; without even the implied warranty of      
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the       
# GNU General Public License for more details.                        
#                                                                     
# You should have received a copy of the GNU General Public License   
# along with this program; if not, write to the Free Software         
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

from __future__ import with_statement

from datetime import datetime
from threading import Thread, Lock

from Backend.Scapy import *
from umitCore.I18N import _

def register_sniff_context(BaseSniffContext):
    class SniffContext(BaseSniffContext):
        """
        A sniff context for controlling various options.
        """
        has_stop = True
        has_pause = False
        has_restart = True

        def __init__(self, *args, **kwargs):
            BaseSniffContext.__init__(self, *args, **kwargs)

            self.lock = Lock()
            self.prevtime = None
            self.socket = None
            self.internal = True

            self.summary = _('Sniffing on %s') % self.iface
            self.thread = None

        def get_all_data(self):
            with self.lock:
                return BaseSniffContext.get_all_data(self)

        def get_data(self):
            with self.lock:
                return BaseSniffContext.get_data(self)

        def set_data(self, val):
            with self.lock:
                self.data = val

        def get_percentage(self):
            if self.state != self.RUNNING:
                return 100.0
            else:
                if self.stop_count or \
                   self.stop_time or \
                   self.stop_size:
                    return self.percentage
                else:
                    return None

        def _start(self):
            self.prevtime = datetime.now()

            if self.iface and not self.socket:
                try:
                    self.socket = conf.L2listen(type=ETH_P_ALL, iface=self.iface, filter=self.filter)
                except socket.error, (errno, err):
                    self.summary = str(err)
                    return False
                except Exception, err:
                    self.summary = str(err)
                    return False

            self.summary = _('Sniffing on %s') % self.iface
            self.state = self.RUNNING
            self.internal = True
            self.data = []

            self.thread = Thread(target=self.run)
            self.thread.setDaemon(True)
            self.thread.start()

            return True
        
        def _stop(self):
            self.internal = False
            return True

        def _restart(self):
            if self.thread and self.thread.isAlive():
                return False

            # Ok reset the counters and begin a new sniff session
            self.tot_size = 0
            self.tot_time = 0
            self.tot_count = 0

            return self._start()

        def run(self):
            while self.internal:
                packet = self.socket.recv(MTU)

                if not packet:
                    continue

                packet = MetaPacket(packet)

                self.tot_count += 1
                self.tot_size += packet.get_size()

                now = datetime.now()
                delta = now - self.prevtime
                self.prevtime = now

                if delta == abs(delta):
                    self.tot_time += delta.seconds

                self.data.append(packet)

                if self.callback:
                    self.callback(MetaPacket(packet), self.udata)

                lst = []

                if self.stop_count:
                    lst.append(float(float(self.tot_count) / float(self.stop_count)))
                if self.stop_time:
                    lst.append(float(float(self.tot_time) / float(self.stop_time)))
                if self.stop_size:
                    lst.append(float(float(self.tot_size) / float(self.stop_size)))

                if lst:
                    self.percentage = float(float(sum(lst)) / float(len(lst))) * 100.0

                    if self.percentage >= 100:
                        self.internal = False
                else:
                    # ((goject.G_MAXINT / 4) % gobject.G_MAXINT)
                    self.percentage = (self.percentage + 536870911) % 2147483647

            self.state = self.NOT_RUNNING
            self.percentage = 100.0
            status = ""

            if self.tot_size >= 1024 ** 3:
                status = "%.1f GB/" % (self.tot_size / (1024.0 ** 3))
            elif self.tot_size >= 1024 ** 2:
                status = "%.1f MB/" % (self.tot_size / (1024.0 ** 2))
            else:
                status = "%.1f KB/" % (self.tot_size / (1024.0))

            if self.tot_time >= 60 ** 2:
                status += "%d h/" % (self.tot_time / (60 ** 2))
            elif self.tot_time >= 60:
                status += "%d m/" % (self.tot_time / 60)
            else:
                status += "%d s/" % (self.tot_time)

            status += "%d pks" % (self.tot_count)

            self.summary = _('Finished sniffing on %s (%s)') % (self.iface, status)

            if self.callback:
                self.callback(None, self.udata)

    return SniffContext
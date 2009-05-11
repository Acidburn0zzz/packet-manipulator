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

from threading import Lock

from PM.Core.I18N import _
from PM.Core.Logger import log
from PM.Core.Atoms import with_decorator
from PM.Backend.Scapy.serialize import load_sequence, save_sequence
from PM.Backend.Scapy.utils import execute_sequence

def register_sequence_context(BaseSequenceContext):

    class SequenceContext(BaseSequenceContext):
        file_types = [(_('Scapy sequence'), '*.pms')]

        def __init__(self, seq, count=1, inter=0, iface=None, strict=True, \
                     report_recv=False, report_sent=True, \
                     scallback=None, rcallback=None, sudata=None, rudata=None):

            BaseSequenceContext.__init__(self, seq, count, inter, iface,
                                         strict, report_recv, report_sent,
                                         scallback, rcallback, sudata, rudata)

            self.sequencer = None
            self.internal = False
            self.lock = Lock()

            if count:
                self.summary = _('Executing sequence (%d packets %d times)') % \
                                (self.tot_packet_count, count)
            else:
                self.summary = _('Looping sequence (%d packets)') % \
                                self.tot_packet_count

        def load(self, operation=None):
            log.debug("Loading sequence from %s" % self.cap_file)

            if self.cap_file:
                self.seq = None

                try:
                    plen = 0
                    fsize = None

                    for tree, tlen, perc, size in load_sequence(self.cap_file):
                        if operation and tlen % 10 == 0 :

                            if not fsize:
                                if size >= 1024 ** 3:
                                    fsize = "%.1f GB" % (size / (1024.0 ** 3))
                                elif size >= 1024 ** 2:
                                    fsize = "%.1f MB" % (size / (1024.0 ** 2))
                                else:
                                    fsize = "%.1f KB" % (size / 1024.0)

                            operation.summary = \
                                _('Loading sequence %s - %d packets (%s)') % \
                                 (self.cap_file, tlen, fsize)
                            operation.percentage = perc

                        self.seq = tree
                        plen = tlen

                    if operation:
                        operation.summary = \
                            _('Sequence %s loaded - %d packets (%s)') % \
                             (self.cap_file, plen, fsize)
                        operation.percentage = 100.0

                except Exception, err:
                    self.summary = str(err)

                    if operation:
                        operation.summary = str(err)
                        operation.percentage = 100.0

                if self.seq is not None:
                    self.status = self.SAVED
                    return True

            self.status = self.NOT_SAVED
            return False

        def save(self, operation=None):
            log.debug("Saving sequence to %s" % self.cap_file)

            if self.cap_file and self.seq is not None and \
               save_sequence(self.cap_file, self.seq):

                try:
                    idx = 0
                    size = 0

                    for idx, perc, size in save_sequence(self.cap_file):
                        if operation and tlen % 10 == 0 :

                            if size >= 1024 ** 3:
                                fsize = "%.1f GB" % (size / (1024.0 ** 3))
                            elif size >= 1024 ** 2:
                                fsize = "%.1f MB" % (size / (1024.0 ** 2))
                            else:
                                fsize = "%.1f KB" % (size / 1024.0)

                            operation.summary = \
                                _('Saving sequence to %s - %d packets (%s)') % \
                                 (self.cap_file, idx, fsize)
                            operation.percentage = perc

                    if operation:
                        if size >= 1024 ** 3:
                            fsize = "%.1f GB" % (size / (1024.0 ** 3))
                        elif size >= 1024 ** 2:
                            fsize = "%.1f MB" % (size / (1024.0 ** 2))
                        else:
                            fsize = "%.1f KB" % (size / 1024.0)

                        operation.summary = \
                                _('Sequence %s saved - %d packets (%s)') % \
                                 (self.cap_file, idx, fsize)
                        operation.percentage = 100.0

                    self.status = self.SAVED
                    return True

                except Exception, err:
                    self.summary = str(err)

                    if operation:
                        operation.summary = str(err)
                        operation.percentage = 100.0

                    self.status = self.NOT_SAVED
                    return False

            self.status = self.NOT_SAVED
            return False

        @with_decorator
        def get_all_data(self):
            return BaseSequenceContext.get_all_data(self)

        @with_decorator
        def get_data(self):
            return BaseSequenceContext.get_data(self)

        @with_decorator
        def set_data(self, val):
            return BaseSequenceContext.set_data(self)

        # We really need this lock here?
        @with_decorator
        def get_sequence(self):
            return BaseSequenceContext.get_sequence(self)

        @with_decorator
        def set_sequence(self, val):
            return BaseSequenceContext.set_sequence(self, val)

        def _start(self):
            if not self.tot_loop_count or \
               self.tot_packet_count - self.packet_count > 0 or \
               self.tot_loop_count - self.loop_count > 0:

                self.internal = True
                self.state = self.RUNNING

                self.sequencer = execute_sequence(
                    self.seq,
                    self.tot_loop_count - self.loop_count,
                    self.inter, self.iface, self.strict,
                    self.__send_callback, self.__recv_callback,
                    self.sudata, self.rudata, self.__exc_callback
                )

                return True

            return False

        def _resume(self):
            if self.sequencer and self.sequencer.isAlive():
                return False

            return self._start()

        def _restart(self):
            if self.sequencer and self.sequencer.isAlive():
                return False

            self.packet_count = 0
            self.loop_count = 0
            self.percentage = 0.0
            self.answers = 0
            self.received = 0

            return self._start()

        def _stop(self):
            self.internal = False

            if self.sequencer:
                self.sequencer.stop()
            else:
                self.state = self.NOT_RUNNING

            return True

        _pause = _stop

        def __exc_callback(self, exc):
            self.internal = False
            self.state = self.NOT_RUNNING
            self.summary = str(exc)

        def __send_callback(self, packet, want_reply, udata):
            if not packet:
                self.loop_count += 1

                if self.tot_loop_count:
                    self.summary = _('Running sequence %d of %d times') % \
                                    (self.loop_count, self.tot_loop_count)
                else:
                    self.summary = _('Sequence runned for %d times') % \
                                    self.loop_count
            else:
                self.packet_count += 1

                if want_reply:
                    self.summary = _('Sending packet %s and waiting a reply') \
                                   % packet.summary()
                else:
                    self.summary = _('Sending packet %s') % packet.summary()

                if self.report_sent:
                    self.data.append(packet)

            pkts = self.packet_count % self.tot_packet_count

            if self.packet_count >= self.tot_packet_count and pkts == 0 and \
               not self.tot_loop_count:
                pkts = 1
            else:
                pkts /= float(self.tot_packet_count)

            # Calculate percentage using also the loop counter if we
            # are not in infinite loop.

            if self.tot_loop_count:
                self.percentage = \
                        ((pkts * (1.0 / self.tot_loop_count)) + \
                        (float(self.loop_count) /
                         float(self.tot_loop_count))) * 100.0
            else:
                self.percentage = pkts * 100.0

            if self.scallback:
                # FIXME: THIS FUCKING UDATA also in other files
                self.scallback(packet, want_reply, self.loop_count,
                               self.packet_count, udata)

            if not self.internal:
                self.state = self.NOT_RUNNING

            return self.state == self.NOT_RUNNING or \
                   self.state == self.PAUSED

        def __recv_callback(self, packet, reply, is_reply, udata):
            if reply is None:
                if self.loop_count == self.tot_loop_count:
                    self.internal = False
                    self.summary = _('Sequence finished with %d packets sent '
                                     'and %d received') % (self.packet_count,
                                                           self.received)
                else:
                    self.summary = _('Looping sequence')
            else:
                self.received += 1
                self.summary = _('Received %s') % reply.summary()

                if is_reply or self.report_recv:
                    self.data.append(reply)

            if self.rcallback:
                self.rcallback(packet, reply, udata)

            if not self.internal:
                self.state = self.NOT_RUNNING

            return self.state == self.NOT_RUNNING or \
                   self.state == self.PAUSED

        def join(self):
            if self.sequencer and self.sequencer.isAlive():
                self.sequencer.stop()

    return SequenceContext

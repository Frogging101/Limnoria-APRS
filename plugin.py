###
# Copyright (c) 2015, John Brooks
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.ircmsgs as ircmsgs
import supybot.log as log

import threading
import re
import APRSMessage
import socket
import sys
import traceback

APRS_SERVER = "noam.aprs2.net"
APRS_PORT = 14580
CALLSIGN = "VE3HCF-10"

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('APRS')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

class APRS(callbacks.Plugin):
    """Add the help for "@plugin help APRS" here
    This should describe *how* to use this plugin."""
    pass

    def __init__(self, irc):
        self.__parent = super(APRS, self)
        self.__parent.__init__(irc)
        self.broken = False
        self.sockMutex = threading.Lock()
        self.outboxMutex = threading.Lock()
        self.outbox = []
        self.run = True
        self.irc = irc
        self.thread = threading.Thread(target=self.APRSThread)
        self.thread.start()
        #self.APRSThread()
    def getPackets(self):
        data = ''
        packets = []
        while True:
            self.sockMutex.acquire()
            recv = self.sock.recv(1024)
            self.sockMutex.release()
            data += recv
            if not recv:
                self.broken = True
                break
            if data[-1] == '\n':
                break
        log.info(data)
        lines = data.split('\r\n')
        msgPattern = re.compile("^(.*?)>.*?::([A-Za-z0-9-]*).*?:(.*?)$",re.M)
        idPattern = re.compile("^(.*){(.*)$",re.M)
        for line in lines:
            if not line:
                continue
            if line[0] == '#':
                continue
            msgMatch = msgPattern.match(line)
            if not msgMatch:
                continue
            content = msgMatch.group(3)
            idMatch = idPattern.match(content)
            if idMatch:
                ident = idMatch.group(2)
                content = idMatch.group(1)
            else:
                ident = ''
            newPacket = APRSMessage.APRSMessage(msgMatch.group(1),msgMatch.group(2),content,ident)
            packets.append(newPacket)
            log.info("append")
        return packets

    def tryConnect(self):
        self.sockMutex.acquire()
        self.sock = socket.socket()
        self.sock.settimeout(60)
        log.info("making sock")
        while True:
            try:
                self.sock.connect(socket.getaddrinfo(APRS_SERVER,APRS_PORT,socket.AF_INET)[0][4])
            except TimeoutError:
                continue
            break
        self.sock.send("user VE3HCF-10 pass -1 filter r/45.396537/-75.731115/20\n")
        self.sockMutex.release()
        log.info("sock made")

    def processPackets(self,inbox):
        for packet in inbox:
            log.info("packet from "+packet.source+" to "+packet.dest+" containing "+packet.content)
            if packet.dest == CALLSIGN:
                s = "\x0307[APRS]\x03 "
                s += packet.source+":"
                s += packet.content
                self.irc.reply(s,to="#fastquake-test")

        """self.outboxMutex.acquire()
        outbox = self.outbox
        self.outbox = []
        self.outboxMutex.release()"""
        

    def APRSThread(self):
        try:
            self.tryConnect()
            while self.run:
                packets = self.getPackets()
                log.info("got packets")
                self.processPackets(packets)        
                log.info("run")
                if self.broken:
                    log.error("it broke")
                    self.sock.close()
                    self.tryConnect()
        except:
            ex_type,ex,tb = sys.exc_info()
            log.info("".join(traceback.format_tb(tb)))
            log.info(ex_type.__name__+": "+str(ex))

Class = APRS


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:

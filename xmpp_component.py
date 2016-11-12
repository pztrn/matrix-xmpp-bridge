import configparser
import getpass
import json
import logging
from optparse import OptionParser
import requests
import sleekxmpp
import sys
import threading

logging.basicConfig(level=logging.DEBUG, format='%(levelname)-8s %(message)s')

class BridgeBot(sleekxmpp.ClientXMPP):
    def __init__(self, jid, password, room, nick):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)
        self.room = room
        self.nick = nick

        self.add_event_handler("session_start", self.start)
        self.add_event_handler("groupchat_message", self.muc_message)

    def set_config(self, config):
        self.__config = config

    def set_queue(self, queue):
        self.__queue = queue

    def start(self, event):
        self.get_roster()
        self.send_presence()
        self.plugin["xep_0045"].joinMUC(self.room,
                                        self.nick,
                                        wait=True)

    def muc_message(self, msg):
        print("Received message: {0}".format(msg))
        if(msg["mucnick"] != self.nick):
            data = {"from_component": "xmpp", "from": msg["mucnick"], "to": self.__config["Matrix"]["room_id"], "body": msg["body"], "id": msg["id"]}
            print("Adding item to queue: {0}".format(data))
            self.__queue.append(data)
            print("Queue len: " + str(len(self.__queue)))

class XMPPConnection(threading.Thread):
    def __init__(self, config, queue):
        threading.Thread.__init__(self)
        self.__config = config
        self.__queue = queue
        self.__xmpp = None

    def connect_to_server(self):
        print("Connecting to XMPP server...")
        jid = self.__config["XMPP"]["username"]
        room = self.__config["XMPP"]["muc_room"]
        nick = self.__config["XMPP"]["nick"]

        try:
            password = self.__config["XMPP"]["password"]
        except ConfigParser.NoOptionError:
            password = getpass.getpass("Password: ")

        self.__xmpp = BridgeBot(jid, password, room, nick)
        self.__xmpp.set_config(self.__config)
        self.__xmpp.set_queue(self.__queue)
        self.__xmpp.register_plugin("xep_0045")

        print("Connecting...")
        if self.__xmpp.connect(address = (self.__config["XMPP"]["server_address"], 5222), reattempt = False):
            try:
                self.__xmpp.process(block=True)
            except TypeError:
                self.__xmpp.process(threaded=False) # Used for older versions of SleekXMPP
            print("Done")
        else:
            print("Unable to connect.")

    def run(self):
        self.connect_to_server()

    def send_message(self, from_name, to, message):
        print("Sending message to MUC: from '{0}' - {1}".format(from_name, message))
        self.__xmpp.send_message(mtype = "groupchat", mto = to, mbody = from_name + ": " + message)

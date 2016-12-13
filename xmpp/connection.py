import json
#import logging
import sleekxmpp
import threading
import uuid

#logging.basicConfig(level=logging.DEBUG, format='%(levelname)-8s %(message)s')

class XMPPConnection(sleekxmpp.ClientXMPP):
    """
    This class responsible for single XMPP connection and run in
    separate thread than ConnectionManager.

    It connects to XMPP with desired login, password and nickname,
    joins XMPP room.
    """
    def __init__(self, jid, password, room, nick):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)
        self.room = room
        self.nick = nick
        # Are we connected?
        self.__connected = False
        # Should we process messages received by this connection?
        # We should process (for now) only messages that received by
        # master user.
        self.__should_process = False

        self.add_event_handler("session_start", self.start_session)
        self.add_event_handler("groupchat_message", self.muc_message)

    def connected(self):
        return self.__connected

    def set_config(self, config):
        self.__config = config

    def set_queue(self, queue):
        self.__queue = queue

    def set_should_process(self):
        self.__should_process = True

    def start_session(self, event):
        self.get_roster()
        self.send_presence()
        self.plugin["xep_0045"].joinMUC(self.room, self.nick, wait=True)
        self.__connected = True

    def muc_message(self, msg):
        # We should not send messages from XMPP which have "@Matrix" in
        # username.
        if self.__should_process and not "@Matrix" in msg["mucnick"]:
            print("Received message: {0}".format(msg))
            data = {"from_component": "xmpp", "from": msg["mucnick"], "to": self.__config["Matrix"]["room_id"], "body": msg["body"], "id": msg["id"]}
            print("Adding item to queue: {0}".format(data))
            self.__queue.add_message(data)
            print("Queue len: " + str(self.__queue.items_in_queue()))

class XMPPConnectionWrapper(threading.Thread):
    """
    This is a wrapper around XMPPConnection for launching later in
    separate thread.
    """
    def __init__(self, config, queue, muc_nick, should_process):
        threading.Thread.__init__(self)
        self.__config = config
        self.__queue = queue
        # MUC nick
        self.__muc_nick = muc_nick
        # XMPP connection.
        self.__xmpp = None
        # Should messages be processed?
        self.__should_process = should_process

    def connect_to_server(self):
        jid = self.__config["XMPP"]["username"]
        room = self.__config["XMPP"]["muc_room"]
        nick = self.__config["XMPP"]["nick"]
        password = self.__config["XMPP"]["password"]
        resource = uuid.uuid4().urn[9:]

        self.__xmpp = XMPPConnection(jid + "/" + resource, password, room, self.__muc_nick)
        self.__xmpp.set_config(self.__config)
        self.__xmpp.set_queue(self.__queue)
        self.__xmpp.register_plugin("xep_0045")

        if self.__should_process:
            self.__xmpp.set_should_process()

        print("Connecting...")
        if self.__xmpp.connect(address = (self.__config["XMPP"]["server_address"], 5222), reattempt = True):
            try:
                self.__xmpp.process(block=True)
            except TypeError:
                self.__xmpp.process(threaded=False) # Used for older versions of SleekXMPP
            print("Done")
        else:
            print("Unable to connect.")

    def run(self):
        self.connect_to_server()

    def send_message(self, to, message):
        while True:
            if self.__xmpp and self.__xmpp.connected():
                self.__xmpp.send_message(mtype = "groupchat", mto = to, mbody = message)
                break

    def status(self):
        if self.__xmpp and self.__xmpp.connected():
            return True
        else:
            return False

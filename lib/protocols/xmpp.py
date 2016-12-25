import threading
import time

from lib.common_libs.library import Library

from lib.protocols.xmpp_conn.connection import XMPPConnection, XMPPConnectionWrapper

class Xmpp(threading.Thread, Library):
    """
    This is a connection manager - thing that ruling all XMPP connections
    we create.
    """

    _info = {
        "name"          : "XMPP connections manager library",
        "shortname"     : "xmpp_library",
        "description"   : "Library responsible for handling XMPP connections."
    }

    def __init__(self):
        Library.__init__(self)
        threading.Thread.__init__(self)

        # XMPP mapped nicks.
        # Format:
        # {"nickname": XMPPClient connection}
        self.__xmpp_nicks = {}

        # Shutdown marker.
        self.__shutdown = False

    def connect_to_server(self):
        print("Connecting to XMPP server...")
        # This will connect our "master client", which will watch
        # for new messages.
        conn = XMPPConnectionWrapper(self.__config, self.__matrix_cfg, self.__queue, self.__config["nick"], True)
        self.__xmpp_nicks[self.__config["nick"]] = conn
        conn.start()

    def init_library(self):
        self.__queue = self.loader.request_library("common_libs", "msgqueue")
        self.__config = self.config.get_temp_value("xmpp")
        self.__matrix_cfg = self.config.get_temp_value("matrix")

    def run(self):
        self.connect_to_server()

        return

    def send_message(self, from_name, to, raw_message):
        # Check if we have "from_name" in XMPP mapped nicks.
        xmpp_nick = from_name[1:].split(":")[0] + "@Matrix"
        if not xmpp_nick in self.__xmpp_nicks or not self.__xmpp_nicks[xmpp_nick].status():
            print("Creating mapped connection for '{0}'...".format(xmpp_nick))

            conn = XMPPConnectionWrapper(self.__config, self.__matrix_cfg, self.__queue, xmpp_nick, False)
            self.__xmpp_nicks[xmpp_nick] = conn
            conn.start()

        # Check if we have "(XMPP MUC)" in body. If so - remove it.
        if "(XMPP MUC)" in raw_message:
            message = raw_message.replace(" (XMPP MUC)", "")
        else:
            message = raw_message

        print("Sending message to MUC: from '{0}' - {1}".format(xmpp_nick, message))
        msg = {
            "mucnick": xmpp_nick,
            "body": message
        }

        self.__xmpp_nicks[xmpp_nick].send_message(to, message)

    def on_shutdown(self):
        """
        Disconnecting from XMPP.
        """
        for nick in self.__xmpp_nicks:
            self.__xmpp_nicks[nick].shutdown()

        self.__shutdown = True

import threading

from xmpp.connection import XMPPConnection, XMPPConnectionWrapper

class ConnectionManager(threading.Thread):
    """
    This is a connection manager - thing that ruling all XMPP connections
    we create.
    """
    def __init__(self, config, queue):
        threading.Thread.__init__(self)
        self.__config_instance = config
        self.__config = config.get_config()
        self.__queue = queue
        # XMPP mapped nicks.
        # Format:
        # {"nickname": XMPPClient connection}
        self.__xmpp_nicks = {}

    def connect_to_server(self):
        print("Connecting to XMPP server...")
        # This will connect our "master client", which will watch
        # for new messages.
        conn = XMPPConnectionWrapper(self.__config, self.__queue, self.__config["XMPP"]["nick"], True)
        self.__xmpp_nicks[self.__config["XMPP"]["nick"]] = conn
        conn.start()

    def run(self):
        self.connect_to_server()

    def send_message(self, from_name, to, message):
        # Check if we have "from_name" in XMPP mapped nicks.
        xmpp_nick = from_name[1:].split(":")[0] + "@Matrix"
        if not xmpp_nick in self.__xmpp_nicks:
            print("Creating mapped connection for '{0}'...".format(xmpp_nick))

            conn = XMPPConnectionWrapper(self.__config, self.__queue, xmpp_nick, False)
            self.__xmpp_nicks[xmpp_nick] = conn
            conn.start()

        print("Sending message to MUC: from '{0}' - {1}".format(xmpp_nick, message))
        msg = {
            "mucnick": xmpp_nick,
            "body": message
        }
        self.__xmpp_nicks[xmpp_nick].send_message(to, message)

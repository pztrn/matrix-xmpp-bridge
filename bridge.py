#!/usr/bin/env python3

import configparser
import time
import _thread

import appservice
import xmpp_component

class Bridge:
    """
    Main class for bridge.
    """
    def __init__(self):
        # App service for communication with Matrix.
        self.__appservice = None
        # Configuration.
        self.__config = None
        # Message queue.
        self.__queue = []
        # XMPP.
        self.__xmpp = None

    def go(self):
        self.read_config()
        self.launch_webservice()
        self.launch_xmpp_connection()

        while True:
            if len(self.__queue) == 0:
                time.sleep(1)
            else:
                print("Items in queue: {0}".format(str(len(self.__queue))))
                print("Processing item from queue...")
                item = self.__queue.pop()
                if item["from_component"] == "xmpp":
                    self.__appservice.send_message_to_matrix(item["from"], item["body"], item["id"])
                if item["from_component"] == "appservice":
                    self.__xmpp.send_message(item["from"], item["to"], item["body"])

                time.sleep(1)


    def launch_webservice(self):
        print("Launching flask webservice...")

        self.__appservice = appservice.AppService(self.__config, self.__queue)
        as_view = appservice.AppServiceViewTransactions()
        appservice.register_app(as_view, "/transactions/")
        self.__appservice.start()

    def launch_xmpp_connection(self):
        self.__xmpp = xmpp_component.XMPPConnection(self.__config, self.__queue)
        self.__xmpp.start()

    def read_config(self):
        print("Reading configuration from mxbridge.conf...")

        self.__config = configparser.ConfigParser()
        self.__config.read('mxbridge.conf')

if __name__ == "__main__":
    b = Bridge()
    b.go()

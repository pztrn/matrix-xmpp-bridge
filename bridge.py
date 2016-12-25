#!/usr/bin/env python3

import json
import os
import sys
import time
import threading

# Load Regius.
system_regius = 0
try:
    from regius.regius import Regius
    system_regius = 1
except:
    pass

if not system_regius:
    if os.path.exists("config.json"):
        preseed = json.loads(open("config.json", "r").read())
        if "paths" in preseed and "regius" in preseed["paths"]:
            print("Using regius from {0}".format(preseed["paths"]["regius"].replace("CURPATH", sys.path[0])))
            sys.path.insert(1, preseed["paths"]["regius"].replace("CURPATH", sys.path[0]))
            print(sys.path)

            try:
                import regius
            except ImportError:
                print("Failed to import Regius!")
                print("Paths:")
                print(sys.path[0], sys.path[1])

class Bridge:
    """
    Main class for bridge.
    """
    def __init__(self, regius_instance):
        # App service for communication with Matrix.
        self.__appservice = None
        # Configuration.
        self.__config = None
        # Database.
        self.__database = None
        # Message queue.
        self.__queue = None
        # XMPP's connections manager.
        self.__xmpp = None

        # Framework initialization.
        self.__regius = regius_instance
        self.loader = self.__regius.get_loader()
        self.config = self.loader.request_library("common_libs", "config")

        self.log = self.loader.request_library("common_libs", "logger").log
        self.log(0, "Framework initialization complete.")

    def go(self):
        self.__queue = self.loader.request_library("common_libs", "msgqueue")
        self.initialize_database()
        self.initialize_commands()
        self.launch_webservice()
        self.launch_xmpp_connection()

        while True:
            try:
                if self.__queue.is_empty():
                    time.sleep(1)
                else:
                    print("Items in queue: {0}".format(str(self.__queue.items_in_queue())))
                    print("Processing item from queue...")
                    item = self.__queue.get_message()
                    if item["from_component"] == "xmpp":
                        # Messages from XMPP.
                        self.__appservice.process_message(item)
                    if item["from_component"] == "appservice":
                        if item["type"] == "invite" or item["type"] == "command_room_message":
                            # Invites and command room's messages should be
                            # processed by appservice.
                            self.__appservice.process_message(item)
                        else:
                            # Messages to XMPP.
                            self.__xmpp.send_message(item["from"], item["to"], item["body"])

                    time.sleep(1)
            except KeyboardInterrupt:
                self.log(0, "Keyboard interrupt!")

    def initialize_commands(self):
        """
        Initializes command room's commands.
        """
        pass

    def initialize_database(self):
        """
        """
        self.database = self.loader.request_library("common_libs", "database")
        self.database.load_mappings()
        self.database.create_connection("production")

        self.migrator = self.loader.request_library("database_tools", "migrator")
        self.migrator.migrate()

    def launch_webservice(self):
        self.log(0, "Launching Matrix protocol listener...")

        self.__appservice = self.loader.request_library("protocols", "matrix")

        as_view = self.loader.request_library("flaskviews", "transactions")
        self.__appservice.register_app(as_view, "/transactions/<int:txid>", "transactions")

        shutdown_view = self.loader.request_library("flaskviews", "shutdown")
        self.__appservice.register_app(shutdown_view, "/shutdown/", "shutdown")

        self.__appservice.start()

    def launch_xmpp_connection(self):
        self.__xmpp = self.loader.request_library("protocols", "xmpp")
        self.__xmpp.start()

    def read_config(self):
        print("Initializing configuration...")
        self.__config = Config()

        # Bridge path.
        PATH = sys.modules["config.config"].__file__
        PATH = os.path.sep.join(PATH.split(os.path.sep)[:-2])
        self.__config.set_temp_value("BRIDGE_PATH", PATH)

        self.__config.parse_config()

if __name__ == "__main__":
    print("Starting Matrix-XMPP bridge...")
    app_path = os.path.abspath(__file__).split(os.path.sep)[:-1]
    app_path = os.path.sep.join(app_path)
    sys.path.insert(0, app_path)
    r = regius.init(preseed, app_path)
    b = Bridge(r)
    exit(b.go())




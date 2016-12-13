import configparser
import os
import sys

class Config:
    def __init__(self):
        # Main configuration, parsed with configparser.
        self.__config = {}
        # Temporary runtime configuration.
        self.__temp_config = {}

    def get_config(self):
        return self.__config

    def get_temp_value(self, key):
        if key in self.__temp_config:
            return self.__temp_config[key]

        return True

    def parse_config(self):
        print("Reading configuration...")
        self.__config = configparser.ConfigParser()

        # Get configuration file name from command line.
        cfg_filename = os.path.join(self.__temp_config["BRIDGE_PATH"], "mxbridge.conf")
        if len(sys.argv) > 1  and "bridge.py" in sys.argv[0]:
            cfg_filename = sys.argv[1]
        elif len(sys.argv) > 2 and "bridge.py" in sys.argv[1]:
            cfg_filename = sys.argv[2]

        print("Configuration file: {0}".format(cfg_filename))

        self.__config.read(cfg_filename)

    def set_temp_value(self, key, value):
        if key in self.__temp_config:
            return True

        self.__temp_config[key] = value

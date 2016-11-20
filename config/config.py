import configparser
import os

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
        print("Reading configuration from mxbridge.conf...")
        self.__config = configparser.ConfigParser()
        self.__config.read(os.path.join(self.__temp_config["BRIDGE_PATH"], "mxbridge.conf"))

    def set_temp_value(self, key, value):
        if key in self.__temp_config:
            return True

        self.__temp_config[key] = value

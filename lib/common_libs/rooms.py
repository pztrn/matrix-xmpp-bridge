import threading

from lib.common_libs.library import Library

class Rooms(Library):

    _info = {
        "name"          : "Rooms library",
        "shortname"     : "rooms_library",
        "description"   : "Library responsible for handling rooms."
    }

    def __init__(self):
        Library.__init__(self)
        self.__command_rooms = []
        self.__lock = threading.Lock()

    def add_command_room(self, room_id):
        self.__lock.acquire(blocking = True)
        self.__command_rooms.append(room_id)
        self.__lock.release()

    def init_library(self):
        """
        """
        pass

    def is_command_room(self, room_id):
        """
        Checks if passed room ID is a command room.
        """
        if room_id in self.__command_rooms:
            return True

        return False

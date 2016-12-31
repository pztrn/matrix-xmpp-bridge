import threading

# Regius's database.get_database_mapping() thing do something wrong,
# so we should instantiate mapping normally.
from lib.database_mappings.rooms import Rooms as RoomsMap
from lib.common_libs.library import Library

class Rooms(Library):

    _info = {
        "name"          : "Rooms handling library",
        "shortname"     : "rooms_library",
        "description"   : "Library responsible for handling rooms."
    }

    def __init__(self):
        Library.__init__(self)
        # Rooms list.
        self.__rooms = {}
        # Rooms types we accept.
        self.__rooms_types = {}

        # Threading lock :).
        self.__lock = threading.Lock()

    def add_command_room(self, room_id, user_id):
        self.__lock.acquire(blocking = True)
        if not room_id in self.__rooms.keys():
            self.log(1, "Adding command room {CYAN}{room_id}{RESET} for user {YELLOW}{user_id}{RESET}", {"room_id": room_id, "user_id": user_id})
            self.__rooms[room_id] = {
                "id": room_id,
                "type": "Command room",
                "commander": user_id,
                "in_database": True
            }
            room = RoomsMap()
            room.room_id = room_id
            room.room_type = self.__rooms_types["Command room"]["id"]
            room.commander = user_id
            sess = self.__database.get_session()
            sess.add(room)
            sess.commit()
        self.__lock.release()

    def check_room_type(self, room_id):
        """
        Checks for room type and returns approriate type in string
        representation (i.e. "Bridged room" or "Command room").
        """
        if room_id in self.__rooms.keys():
            return self.__rooms[room_id]["type"]
        else:
            # If room ID is unknown - assuming command room.
            return "Command room"

    def init_library(self):
        """
        """
        self.log(0, "Initializing rooms handling library...")

        self.__database = self.loader.request_library("common_libs", "database")

        # Get rooms types.
        sess = self.__database.get_session()
        rooms_types_mapping = self.__database.get_database_mapping("roomstypes")
        rooms_types = sess.query(rooms_types_mapping).order_by(rooms_types_mapping.id).all()
        for room_type in rooms_types:
            self.__rooms_types[room_type.name] = {
                "id": room_type.id,
                "name": room_type.name,
                "description": room_type.description
            }

        # Get rooms.
        rooms_mapping = self.__database.get_database_mapping("rooms")
        data = sess.query(rooms_mapping).all()
        # Convert rooms list into dictionary.
        for item in data:
            self.__rooms[item.room_id] = {
                "id": item.room_id,
                "commander": item.commander,
                "in_database": True
            }
            # Room type.
            for rt in self.__rooms_types:
                if self.__rooms_types[rt]["id"] == item.room_type:
                    self.__rooms[item.room_id]["type"] = self.__rooms_types[rt]["name"]

    def on_shutdown(self):
        """
        """
        self.log(0, "Updating rooms list in database...")

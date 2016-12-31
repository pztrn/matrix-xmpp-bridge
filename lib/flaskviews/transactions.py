from flask import jsonify
from flask import request
from flask.views import MethodView

from lib.common_libs.library import Library

class Transactions(MethodView, Library):

    _info = {
        "name"          : "Incoming transactions handler library",
        "shortname"     : "matrix_transactions_library",
        "description"   : "Library responsible for handling incoming Matrix transactions."
    }

    def __init__(self, loader = None):
        Library.__init__(self)
        MethodView.__init__(self)

        self.__loader = loader
        self.__bridge_username = None
        self.log = None
        self.__queue = None
        self.__rooms = None
        self.__config = None
        self.__rooms_types = None
        self.__rooms = None
        self.config = None
        self.__bridge_username = None

    def put(self, txid):
        if not self.__config:
            self.__config = self.__loader.request_library("common_libs", "config")

        if not self.__rooms_types:
            self.__rooms_types = self.__config.get_temp_value("/rooms/types")

        if not self.__rooms:
            self.__rooms = self.__config.get_temp_value("/rooms/rooms")

        if not self.config:
            self.config = self.__config.get_temp_value("app_config")

        if not self.__queue:
            self.__queue = self.__loader.request_library("common_libs", "msgqueue")

        if not self.log:
            self.log = self.__loader.request_library("common_libs", "logger").log

        if not self.__bridge_username:
            self.__bridge_username = self.__config.get_temp_value("/matrix/bridge_username")

        if not self.__rooms:
            self.__rooms = self.__loader.request_library("rooms", "rooms")

        events = request.get_json()["events"]
        for event in events:
            self.log(2, "Event: {event}", {"event": event})

            # Check room type, if any.
            # None if room wasn't found.
            room_type = self.__rooms.check_room_type(event["room_id"])
            self.log(2, "Detected room type: {type}", {"type": room_type})

            # Room message.
            if event['type'] == 'm.room.message' and event["age"] < 10000 and room_type:
                # If we have message's body.
                if "content" in event and "body" in event["content"]:
                    # If we have this message in bridged room.
                    if room_type == "Bridged room" and not self.config["matrix"]["users_prefix"] in event["user_id"]:
                        data = {"type": "bridged_room_message", "from_component": "appservice", "from": event["user_id"], "from_room": event["room_id"]}
                        if event["content"]["msgtype"] in ["m.image", "m.file", "m.video"]:
                            # Craft image URL.
                            domain = event["content"]["url"].split("/")[2]
                            media_id = event["content"]["url"].split("/")[3]
                            body = "http://" + domain + "/_matrix/media/r0/download/" + domain + "/" + media_id
                            data["body"] = body
                        elif event["content"]["msgtype"] == "m.emote":
                            data["body"] = "/me" + event["content"]["body"]
                        else:
                            data["body"] = event["content"]["body"]
                        self.log(2, "Adding message to queue: {msg}", {"msg": data})
                        self.__queue.add_message(data)

                        self.log(1, "User: {user}, Room: {room}", {"user": event["user_id"], "room": event["room_id"]})
                        self.log(1, "Event Type: {event_type}", {"event_type": event["type"]})
                        self.log(1, "Content: {content}", {"content": event["content"]})

                    # If we have command room message.
                    if room_type == "Command room" and not event["user_id"] == "@" + self.__bridge_username:
                        self.log(0, "Received command room message from {user}", {"user": event["user_id"]})
                        data = {"type": "command_room_message", "from_component": "appservice", "from": event["user_id"], "room_id": event["room_id"], "body": event["content"]["body"], "msgtype": event["content"]["msgtype"]}
                        self.log(2, "Adding message to queue: {msg}", {"msg": data})
                        self.__queue.add_message(data)

            # Inviting.
            if event["type"] == "m.room.member" and "content" in event and event["content"]["membership"] == "invite":
                self.log(0, "Received invite into: {room} from: {user}", {"room": event["room_id"], "user": event["user_id"]})
                data = {"type": "invite", "from_component": "appservice", "user_id": event["user_id"], "room_id": event["room_id"]}
                self.log(1, "Adding message to queue: {msg}", {"msg": data})
                self.__queue.add_message(data)

        return jsonify({})

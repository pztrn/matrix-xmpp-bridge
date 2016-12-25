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

    def __init__(self, loader = None, bridge_username = None):
        Library.__init__(self)
        MethodView.__init__(self)

        self.loader = loader
        self.__bridge_username = bridge_username

    def put(self, txid):
        self.config = self.loader.request_library("common_libs", "config")
        self.matrix_cfg = self.config.get_temp_value("matrix")
        self.xmpp_cfg = self.config.get_temp_value("xmpp")
        self.log = self.loader.request_library("common_libs", "logger").log
        self.__queue = self.loader.request_library("common_libs", "msgqueue")
        print(dir(self))
        events = request.get_json()["events"]
        for event in events:
            # Was this event processed?
            event_processed = False
            self.log(1, "Event: {event}", {"event": event})
            # Bridged room message.
            if event['type'] == 'm.room.message' and event["room_id"] == self.matrix_cfg["room_id"] and event["age"] < 1000 and not "mxbridge" in event["user_id"] and "content" in event and "body" in event["content"] and not self.matrix_cfg["users_prefix"] in event["user_id"]:

                data = {"type": "message_to_room", "from_component": "appservice", "from": event["user_id"], "to": self.xmpp_cfg["muc_room"]}
                if event["content"]["msgtype"] == "m.image" or event["content"]["msgtype"] == "m.file":
                    # Craft image URL.
                    domain = event["content"]["url"].split("/")[2]
                    media_id = event["content"]["url"].split("/")[3]
                    body = "http://" + domain + "/_matrix/media/r0/download/" + domain + "/" + media_id
                    data["body"] = body
                elif event["content"]["msgtype"] == "m.emote":
                    data["body"] = "/me" + event["content"]["body"]
                else:
                    data["body"] = event["content"]["body"]
                print("Adding message to queue: {0}".format(data))
                self.__queue.add_message(data)

                print("User: %s Room: %s" % (event["user_id"], event["room_id"]))
                print("Event Type: %s" % event["type"])
                print("Content: %s" % event["content"])

                event_processed = True

            # Inviting.
            if event["type"] == "m.room.member" and "content" in event and event["content"]["membership"] == "invite":
                print("Received invite into: {0} from: {1}".format(event["room_id"], event["user_id"]))
                data = {"type": "invite", "from_component": "appservice", "user_id": event["user_id"], "room_id": event["room_id"]}
                print("Adding message to queue: {0}".format(data))
                self.__queue.add_message(data)

            # Invited room message.
            #if event["type"] == "m.room.message" and not event_processed and not event["user_id"] == "@" + self.__bridge_username:
            #    data = {"type": "command_room_message", "from_component": "appservice", "from": event["user_id"], "room_id": event["room_id"], "body": event["content"]["body"], "msgtype": event["content"]["msgtype"]}
            #    self.__queue.add_message(data)

        return jsonify({})

from flask import Flask
import json
import os
import requests
import threading
import time

from lib.common_libs.library import Library

CONFIG = None
QUEUE = None
BRIDGE_USERNAME = None
COMMAND_ROOMS = []
BRIDGED_ROOMS = []

class Matrix(threading.Thread, Library):

    _info = {
        "name"          : "Matrix connection library",
        "shortname"     : "matrix_library",
        "description"   : "Library responsible for handling connection to Matrix homeserver."
    }

    def __init__(self):
        Library.__init__(self)
        threading.Thread.__init__(self)

        # Flask App.
        self.__app = Flask("matrix-xmpp-bridge")

        self.__joined = {}

        # Transaction ID for Matrix's homeserver.
        self.__txid = 100

        # Shutdown marker.
        self.__shutdown = False


    def command(self, message):
        """
        """
        self.log(0, "Processing command room message...")
        data = self.__send_message(message["room_id"], "@" + self.__bridge_username, "m.text", "Echoing message: " + message["body"])
        self.log(2, data)

    def init_library(self):
        """
        """
        self.log(0, "Initializing Matrix protocol handler...")

        self.__matrix_cfg = self.config.get_temp_value("matrix")

        # API URL to which messages will be pushed.
        self.__msg_api_url = self.__matrix_cfg["api_url"] + "/rooms/{0}/send/m.room.message"
        # Authentication parameters.
        self.__params = {
            "access_token": self.__matrix_cfg["token"]
        }
        # Bridge's username
        self.__bridge_username = "{0}_bridge:{1}".format(self.__matrix_cfg["users_prefix"], self.__matrix_cfg["domain"])

    def join_room(self, room_id, full_username):
        """
        Joins to Matrix room.
        WARNING: full_username should start with "@"!
        """
        if len(full_username) < 4:
            self.log(0, "{RED}Error:{RESET} User ID not specified!")
            return

        if len(room_id) < 4:
            self.log(0, "{RED}Error:{RESET} Room ID not specified!")
            return

        self.log(1, "Trying to join {room_id} as {user}...", {"room_id": room_id, "user": full_username})

        # Join room.
        if not room_id in self.__joined:
            self.__joined[room_id] = {}

        if not full_username in self.__joined[room_id]:
            data = {
                "user_id": full_username,
                "access_token": self.__params["access_token"]
            }
            r = requests.post(self.__matrix_cfg["api_url"] + '/join/' + room_id, params = data, data = json.dumps(data))
            self.log(2, "Join request output from Matrix: {output}", {"output": r.json()})
        else:
            self.log(1, "User already in room, will not re-join.")

        # Get members list.
        d = requests.get(self.__matrix_cfg["api_url"] + "/rooms/" + room_id + "/members", params = self.__params)
        data = d.json()

        if "errcode" in data and data["errcode"] == "M_GUEST_ACCESS_FORBIDDEN":
            self.log(0, "{RED}Error:{RESET} Failed to join Matrix room: permissions error!")
            return

        if not room_id in self.__joined:
            self.__joined[room_id] = {}

        for item in data["chunk"]:
            if item["content"]["membership"] == "join":
                self.__joined[room_id][item["state_key"][1:]] = {
                    "username": item["state_key"]
                }

        self.log(2, "All joined users: {users}", {"users": self.__joined})

    def on_shutdown(self):
        """
        Executes on bridge shutdown.
        """
        # Execute HTTP GET request to Flask to shut it down.
        # Compose URL first.
        url = "http://{0}:{1}/shutdown/".format(self.__matrix_cfg["listen_address"], self.__matrix_cfg["listen_port"])
        requests.get(url)

        self.__shutdown = True

    def process_message(self, message):
        """
        Processes passed message.
        """
        if message["type"] == "command_room_message":
            if message["room_id"] not in BRIDGED_ROOMS and message["room_id"] not in COMMAND_ROOMS:
                global COMMAND_ROOMS
                COMMAND_ROOMS.append(message["room_id"])
                self.command(message)
        elif message["type"] == "invite":
            self.join_room(message["room_id"], "@" + self.__bridge_username)
        elif message["type"] == "message_to_room":
            self.send_message_to_matrix(message)

    def register_app(self, instance, base, view_name):
        """
        Registers Flask view with Flask app.
        """
        #instance.register(self.__app, route_base = base, trailing_slash = False)
        self.__app.add_url_rule(base, view_func = instance.as_view(view_name, loader = self.loader, bridge_username = self.__bridge_username))

    def run(self):
        """
        Run App Service thread.
        """
        # Try to register our master user.
        self.__register_user("@" + self.__bridge_username, self.__bridge_username.split(":")[0], "XMPP bridge")
        self.join_room(self.__matrix_cfg["room_id"], "@" + self.__bridge_username)
        self.__app.config['TRAP_BAD_REQUEST_ERRORS'] = True
        self.__app.run(host = self.__matrix_cfg["listen_address"], port = int(self.__matrix_cfg["listen_port"]))

        return

    def send_message_to_matrix(self, queue_item):
        """
        Tries to send message to Matrix.
        """
        self.log(0, "Sending message to Matrix...")
        # Splitting "@Matrix" from user highlight, if any.
        if "@Matrix" in queue_item["body"]:
            idx = 0
            body_s = queue_item["body"].split(" ")
            for item in body_s:
                if "@Matrix" in item:
                    idx = body_s.index(item)

            body_s[idx] = "@" + body_s[idx].split("@")[0]
            body = " ".join(body_s)
        else:
            body = queue_item["body"]

        # Get username for Matrix.
        full_username, username, nickname = self.__compose_matrix_username(queue_item["conference"], queue_item["from"])
        self.log(2, "Full username: {full_username}, username: {username}, nickname: {nickname}", {"full_username": full_username, "username": username, "nickname": nickname})

        # Check if we have this user in room. And then if user already
        # registered. And register user if not. Same for joining room.
        if not full_username[1:] in self.__joined[self.__matrix_cfg["room_id"]]:
            self.__register_user(full_username, username, nickname)

            # Join room.
            self.join_room(self.__matrix_cfg["room_id"], full_username)

        data = self.__send_message(self.__matrix_cfg["room_id"], full_username, "m.text", body)

        if "error" in data and data["errcode"] == "M_FORBIDDEN" and "not in room" in data["error"]:
            self.log(0, "{RED}Error:{RESET} user {user} not in room, joining and re-sending message...", {"user": full_username})
            self.join_room(self.__matrix_cfg["room_id"], full_username)

            self.__send_message(self.__matrix_cfg["room_id"], full_username, "m.text", body)

    def __compose_matrix_username(self, conference, username):
        """
        This method composes a username for Matrix, which will be used
        for pseudouser.
        """
        # Check if passed nickname is in ASCII range.
        is_ascii = True
        try:
            username.encode("ascii")
        except UnicodeEncodeError:
            is_ascii = False

        if is_ascii:
            matrix_username = "{0}_{1}_{2}".format(self.__matrix_cfg["users_prefix"],
                username, conference)
            matrix_username_full = "@{0}:{1}".format(matrix_username, self.__matrix_cfg["domain"])
        else:
            matrix_username = "{0}_{1}_{2}".format(self.__matrix_cfg["users_prefix"],
                username.encode("punycode").decode("utf-8"), conference)
            matrix_username = "@{0}_{1}_{2}:{3}".format(self.__matrix_cfg["users_prefix"],
                username.encode("punycode").decode("utf-8"), conference, self.__matrix_cfg["domain"])

        matrix_nickname = "{0} (XMPP MUC)".format(username)
        return matrix_username_full, matrix_username, matrix_nickname

    def __register_user(self, full_username, username, nickname):
        """
        Registers user with Matrix server for later usage with bridge.
        """
        # Checking for profile existing.
        d = requests.get(self.__matrix_cfg["api_url"] + "/profile/" + full_username)
        rdata = d.json()
        if "displayname" in rdata:
            self.log(1, "User {user} already registered with nickname '{nickname}'", {"user": username, "nickname": rdata["displayname"]})

        if "error" in rdata and rdata["error"] == "No row found":
            self.log(0, "Registering user...")
            # Register user!
            # Try to register user and join the room.
            data = {
                "type": "m.login.application_service",
                "user": username
            }

            # Register user.
            url = self.__matrix_cfg["api_url"] + "/register"
            r = requests.post(url, params = self.__params, data = json.dumps(data))

            # Set display name.
            data_to_put = {
                "displayname": nickname
            }

            data = {
                "user_id": full_username
            }
            data.update(self.__params)
            url = self.__matrix_cfg["api_url"] + "/profile/{0}/displayname".format(full_username)
            d = requests.put(url, params = data, data = json.dumps(data_to_put), headers = {"Content-Type": "application/json"})

    def __send_message(self, room_id, user_id, msgtype, message):
        """
        Really sends message to room.
        """
        self.log(0, "Sending message...")

        if len(room_id) < 4:
            self.log(0, "{RED}Error:{RESET} Can't send message to undefined room ID!")
            return

        body_compiled = json.dumps({
            "msgtype": msgtype,
            "body": message
        })

        url = self.__msg_api_url.format(room_id) + "/" + str(self.__txid)

        data = {
            "user_id": user_id
        }
        data.update(self.__params)
        d = requests.put(url, data = body_compiled, params = data, headers = {"Content-Type": "application/json"})
        self.log(2, "URL: {url}, homeserver's output: {output}", {"url": d.url, "output": d.text})

        self.__txid += 1

        return d.json()

from flask import Flask
from flask import jsonify
from flask import request
from flask.ext.classy import FlaskView
import json
import os
import requests
import threading

CONFIG = None
QUEUE = None

class AppService(threading.Thread):
    def __init__(self, config, queue):
        threading.Thread.__init__(self)
        self.__config_instance = config
        self.__config = config.get_config()
        self.__app = Flask("matrix-xmpp-bridge")
        self.__msg_api_url = config.get_config()["Matrix"]["api_url"] + "/rooms/" + config.get_config()["Matrix"]["room_id"] + "/send/m.room.message"
        self.__params = {
            "access_token": config.get_config()["Matrix"]["token"]
        }
        self.__queue = queue
        self.__joined = {}
        self.__txid = 1

        global CONFIG
        CONFIG = config.get_config()
        global QUEUE
        QUEUE = queue

    def initialize(self):
        """
        Initializes App Service. For now it only loads pseudousers
        login details.
        """
        data_path = os.path.join(self.__config_instance.get_temp_value("BRIDGE_PATH"), "data", "appservice_mappings.json")
        if os.path.exists(data_path):
            self.__joined = json.loads(open(data_path, "r").read())

    def join_room(self):
        if(self.__config["Matrix"]["token"] != None and self.__config["Matrix"]["room_id"] != None):
            requests.post(self.__config["Matrix"]["api_url"] + '/join/' + self.__config["Matrix"]["room_id"], params = self.__params)
        elif(self.__config["Matrix"]["token"] == None):
            print("Must include access token!")
        elif(self.__config["Matrix"]["room_id"] == None):
            print("Must include roomid!")

    def register_app(self, instance, base):
        instance.register(self.__app, route_base = base, trailing_slash = False)

    def send_message_to_matrix(self, queue_item):
        print("Sending message to Matrix...")
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

        body_compiled = json.dumps({
            "msgtype": "m.text",
            "body": body
        })

        # Get username for Matrix.
        # We will encode username into punycode to get rid of any
        # errors we might encounter on nicknames that outside of
        # ASCII range.
        # Yet nickname (which is used for profile) will stay
        # unconverted, because Matrix have no limitations on it.
        username, nickname = self.__compose_matrix_username(queue_item["conference"], queue_item["from"])
        print(username, nickname)

        if not self.__config["Matrix"]["room_id"] in self.__joined:
            self.__joined[self.__config["Matrix"]["room_id"]] = {}

        if not username in self.__joined[self.__config["Matrix"]["room_id"]]:
            print("User not registered, registering...")
            # Try to register user and join the room.
            data = {
                "type": "m.login.application_service",
                "user": username
            }

            # Register user.
            url = self.__config["Matrix"]["api_url"] + "/register"
            r = requests.post(url, params = self.__params, data = json.dumps(data))
            d = r.json()
            print(d)
            token = d["access_token"]


            # Set display name.
            data = {
                "displayname": nickname,
            }
            params = {
                "access_token": token
            }
            url = self.__config["Matrix"]["api_url"] + "/profile/@{0}:{1}/displayname".format(username, self.__config["appservice"]["domain"])
            d = requests.put(url, params = params, data = json.dumps(data))
            print(d.text)

            # Join room.
            data = {
                "user_id": nickname,
                "access_token": token
            }
            url = self.__config["Matrix"]["api_url"] + '/join/' + self.__config["Matrix"]["room_id"]
            requests.post(url, params = self.__params, data = data)

            self.__joined[self.__config["Matrix"]["room_id"]][username] = {
                "username"  : username,
                "nickname"  : nickname,
                "token"     : token
            }

            data_path = os.path.join(self.__config_instance.get_temp_value("BRIDGE_PATH"), "data", "appservice_mappings.json")
            f = open(data_path, "w")
            f.write(json.dumps(self.__joined))
            f.close()

        url = self.__msg_api_url + "/" + str(self.__txid)

        data = {
            "user_id": username,
            "access_token": self.__joined[self.__config["Matrix"]["room_id"]][username]["token"]
        }
        d = requests.put(url, data = body_compiled, headers = {"Content-Type": "application/json"}, params = data)
        print(d.text)

        self.__txid += 1

    def run(self):
        """
        Run App Service thread.
        """
        self.join_room()
        self.__app.config['TRAP_BAD_REQUEST_ERRORS'] = True
        self.__app.run(host = self.__config["appservice_listener"]["listen_address"], port = int(self.__config["appservice_listener"]["listen_port"]))

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
            matrix_username = "{0}_{1}_{2}".format(self.__config["appservice"]["users_prefix"],
                username, conference)
        else:
            matrix_username = "{0}_{1}_{2}".format(self.__config["appservice"]["users_prefix"],
                username.encode("punycode").decode("utf-8"), conference)

        matrix_nickname = "{0} (XMPP MUC)".format(username)
        return matrix_username, matrix_nickname

class AppServiceViewTransactions(FlaskView):
    def put(self, transaction):
        events = request.get_json()["events"]
        for event in events:
            if event['type'] == 'm.room.message' and event["room_id"] == CONFIG["Matrix"]["room_id"] and event["age"] < 1000 and not "mxbridge" in event["user_id"] and "content" in event and "body" in event["content"] and not CONFIG["appservice"]["users_prefix"] in event["user_id"]:

                data = {"from_component": "appservice", "from": event["user_id"], "to": CONFIG["XMPP"]["muc_room"]}
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
                QUEUE.add_message(data)

                print("User: %s Room: %s" % (event["user_id"], event["room_id"]))
                print("Event Type: %s" % event["type"])
                print("Content: %s" % event["content"])

        return jsonify({})

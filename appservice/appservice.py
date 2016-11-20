from flask import Flask
from flask import jsonify
from flask import request
from flask.ext.classy import FlaskView
import json
import requests
import threading

CONFIG = None
QUEUE = None

class AppService(threading.Thread):
    def __init__(self, config, queue):
        threading.Thread.__init__(self)
        self.__app = Flask("matrix-xmpp-bridge")
        self.__api_url = config["Matrix"]["api_url"] + "/rooms/" + config["Matrix"]["room_id"] + "/send/m.room.message"
        self.__config = config
        self.__params = {
            "access_token": config["Matrix"]["token"]
        }
        self.__queue = queue

        global CONFIG
        CONFIG = self.__config
        global QUEUE
        QUEUE = queue

    def join_room(self):
        if(self.__config["Matrix"]["token"] != None and self.__config["Matrix"]["room_id"] != None):
            requests.post(self.__config["Matrix"]["api_url"] + '/join/' + self.__config["Matrix"]["room_id"], params = self.__params)
        elif(self.__config["Matrix"]["token"] == None):
            print("Must include access token!")
        elif(self.__config["Matrix"]["room_id"] == None):
            print("Must include roomid!")

    def register_app(self, instance, base):
        instance.register(self.__app, route_base = base, trailing_slash = False)

    def send_message_to_matrix(self, frm_user, body, id):
        print("Sending message to Matrix...")
        # Splitting "@Matrix" from user highlight, if any.
        if "@Matrix" in body:
            idx = 0
            body_s = body.split(" ")
            for item in body_s:
                if "@Matrix" in item:
                    idx = body_s.index(item)

            body_s[idx] = "@" + body_s[idx].split("@")[0]
            body = " ".join(body_s)

        body = json.dumps({
            "msgtype": "m.text",
            "body": frm_user + ": " + body
        })

        url = self.__api_url + "/" + str(id)
        requests.put(url, data = body, headers = {"Content-Type": "application/json"}, params = self.__params)

    def run(self):
        self.join_room()
        self.__app.config['TRAP_BAD_REQUEST_ERRORS'] = True
        self.__app.run(host = self.__config["appservice_listener"]["listen_address"], port = int(self.__config["appservice_listener"]["listen_port"]))

class AppServiceViewTransactions(FlaskView):
    def put(self, transaction):
        events = request.get_json()["events"]
        for event in events:
            if event['type'] == 'm.room.message' and event["room_id"] == CONFIG["Matrix"]["room_id"] and event["age"] < 1000 and not "mxbridge" in event["user_id"] and "content" in event and "body" in event["content"]:
                data = {"from_component": "appservice", "from": event["user_id"], "to": CONFIG["XMPP"]["muc_room"], "body": event["content"]["body"]}
                print("Adding message to queue: {0}".format(data))
                QUEUE.add_message(data)

                print("User: %s Room: %s" % (event["user_id"], event["room_id"]))
                print("Event Type: %s" % event["type"])
                print("Content: %s" % event["content"])

        return jsonify({})

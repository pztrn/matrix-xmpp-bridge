from flask import Flask, jsonify, request
from flask.ext.classy import FlaskView
import json
import requests
import threading
import xmpp_component

app = Flask("matrix-xmpp-bridge")
CONFIG = None
QUEUE = None

def register_app(as_instance, base):
    as_instance.register(app, route_base = base, trailing_slash = False)

class AppService(threading.Thread, FlaskView):
    def __init__(self, config, queue):
        FlaskView.__init__(self)
        threading.Thread.__init__(self)
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

    def send_message_to_matrix(self, frm_user, body, id):
        print("Sending message to Matrix...")
        body = json.dumps({
            "msgtype": "m.text",
            "body": frm_user + ": " + body
        })

        url = self.__api_url + "/" + str(id)
        requests.put(url, data = body, headers = {"Content-Type": "application/json"}, params = self.__params)

    def run(self):
        self.join_room()
        app.config['TRAP_BAD_REQUEST_ERRORS'] = True
        app.run(host = self.__config["appservice_listener"]["listen_address"], port = int(self.__config["appservice_listener"]["listen_port"]))

class AppServiceViewTransactions(FlaskView):
    def put(self, transaction):
        events = request.get_json()["events"]
        for event in events:
            print(event['type'], event["room_id"], event["age"])
            if event['type'] == 'm.room.message' and event["room_id"] == CONFIG["Matrix"]["room_id"] and event["age"] < 100 and not "mxbridge" in event["user_id"]:
                data = {"from_component": "appservice", "from": event["user_id"], "to": CONFIG["XMPP"]["muc_room"], "body": event["content"]["body"]}
                print("Adding message to queue: {0}".format(data))
                QUEUE.append(data)

                print("User: %s Room: %s" % (event["user_id"], event["room_id"]))
                print("Event Type: %s" % event["type"])
                print("Content: %s" % event["content"])

        return jsonify({})

if __name__ == "__main__":
    xmpp = xmpp_component.XMPPConnection(config)
    xmpp.connect_to_server()

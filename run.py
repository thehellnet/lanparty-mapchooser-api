import json
import random
import re
import socket
import time

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
from werkzeug.wrappers import response

app = Flask(__name__)
CORS(app)

MAPS = [
    "q3dm0",
    "q3dm1",
    "q3dm2",
    "q3dm3",
    "q3dm4",
    "q3dm5",
    "q3dm6",
    "q3dm7",
    "q3dm8",
    "q3dm9",
    "q3dm10",
    "q3dm11",
    "q3dm12",
    "q3dm13",
    "q3dm14",
    "q3dm15",
    "q3dm16",
    "q3dm17",
    "q3dm18",
    "q3dm19"
]

GAMETYPE = "0"


class CommandSender:
    def __init__(self, address, port, rcon_password):
        self._address = address
        self._port = port
        self._rcon_password = rcon_password

    def send(self, command=""):
        self.send_recv(command)

    def send_recv(self, command=""):
        if not command:
            return

        data = "rcon %s %s" % (self._rcon_password, command)
        data = data.encode()
        data = b"\xff\xff\xff\xff" + data

        sck = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        sck.sendto(data, (self._address, self._port))
        data = sck.recv(1024)
        sck.close()

        return data

    def map_change(self, g_gametype="", map_tag=""):
        if not g_gametype or not map_tag:
            return

        self.send("g_gametype %s" % g_gametype)

        time.sleep(1.5)

        self.send("map %s" % map_tag)

    def map_name(self):
        raw_data = self.send_recv("mapname").replace(b"\xff", b"").decode()

        map_tag = None

        rg = re.compile(".*is:\"([a-zA-Z0-9^]+)\".*", re.IGNORECASE | re.DOTALL)
        m = rg.search(raw_data)
        if m:
            map_tag = m.group(1).split("^")[0]

        return map_tag

    def map_restart(self):
        self.send("map_restart")

    def fast_restart(self):
        self.send("fast_restart")


sender = CommandSender(
    address="127.0.0.1",
    port=27960,
    rcon_password="password"
)


def response_ok(**data):
    response_body = json.dumps(data)

    headers = [
        ("Content-Type", "application/json")
    ]

    return response.Response(
        response=response_body,
        status=200,
        headers=headers
    )


@app.errorhandler(Exception)
def handle_error(e):
    code = 500
    if isinstance(e, HTTPException):
        code = e.code
    return jsonify(error=str(e)), code


@app.route(
    rule="/api/public/v1/fastRestart",
    methods=["POST"],
)
def fast_restart():
    sender.fast_restart()

    return response_ok()


@app.route(
    rule="/api/public/v1/mapRestart",
    methods=["POST"]
)
def map_restart():
    sender.map_restart()

    return response_ok()


@app.route(
    rule="/api/public/v1/randomMap",
    methods=["POST"]
)
def random_map():
    tag = random.choice(MAPS)
    g_gametype = GAMETYPE

    sender.map_change(
        g_gametype=g_gametype,
        map_tag=tag
    )

    return response_ok(map=tag)


@app.route(
    rule="/api/public/v1/mapRun",
    methods=["POST"]
)
def map_run():
    map_tag = request.json["map_tag"]
    g_gametype = GAMETYPE

    sender.map_change(
        g_gametype=g_gametype,
        map_tag=map_tag
    )

    return response_ok(map_tag=map_tag)


@app.route(
    rule="/api/public/v1/mapName",
    methods=["POST"]
)
def map_name():
    map_tag = sender.map_name()

    return response_ok(map_tag=map_tag)


if __name__ == "__main__":
    app.run(threaded=True)

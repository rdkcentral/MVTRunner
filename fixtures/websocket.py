##
# If not stated otherwise in this file or this component's LICENSE file the
# following copyright and licenses apply:
#
# Copyright 2025 Liberty Global B.V.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##

import json
import pytest
import threading
import socket
import fcntl
import struct
import ssl
import pathlib
import websockets
import os

from websockets.sync.server import serve
from time import sleep
from utils import HTTP_CONTENT_TYPE_JSON, wait_for, retry_on_failure
from cryptography.fernet import Fernet

def get_ip_address(ifname):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ip_address = socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15].encode())
        )[20:24])
        return ip_address
    except OSError:
        return None

key = b'Ki2SJWIXhuLG-4KrNhEdj3AFt_v72tmvgOH1_ExD16A='

class WebSocket:
    def __init__(self, logger, stb_ip, ws_nw_interface, device_type):
        self.logger = logger
        self.stb_ip = stb_ip
        self.device_type = device_type
        self.ws_nw_interface = ws_nw_interface
        self.client = None
        self.await_response = 0;
        self.command = ""
        self.response = ""
        self.server_thread = threading.Thread(target=self.thread_handler)
        self.server_thread.daemon = True
        self.server_thread.start()

    def msg_handler(self, websocket):
        self.client = websocket
        for message in websocket:
            val = json.loads(message)
            if self.command in val['cmd']:
                self.response = val['val'];
                self.await_response = 0

    def thread_handler(self):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_path = pathlib.Path(__file__).with_name("certs").joinpath(self.device_type)
        #ssl_cert = ssl_path.joinpath("mvtrunner.crt")
        with open(ssl_path.joinpath("mvtrunner.enc"), "rb") as file:
            encrypted_data = file.read()
        decrypted_data = Fernet(key).decrypt(encrypted_data)
        with open(ssl_path.joinpath("mvtrunner.key"), "wb") as file:
            file.write(decrypted_data)
        ssl_context.load_cert_chain(ssl_path.joinpath("mvtrunner.crt"), ssl_path.joinpath("mvtrunner.key"), password="mvtrunner")
        with serve(self.msg_handler, get_ip_address(self.ws_nw_interface) , 10199, ssl=ssl_context) as self.server:
            self.logger.debug("MVT runner : WSS created")
            self.server.serve_forever()

    @retry_on_failure(3)
    def send_message(self, message):
        if self.client == None:
            return
        self.await_response = 1
        self.response = ""
        self.command = message
        self.client.send(message)
        client_timeout = 20
        while(self.await_response):
            sleep(0.5)
            client_timeout -= 1
            if client_timeout <= 0:
                break
        return self.response

@pytest.fixture(scope="session")
def websocket(test_logger, stb_ip, ws_nw_interface, device_type):
    wsocket = WebSocket(test_logger, stb_ip, ws_nw_interface, device_type)
    yield wsocket

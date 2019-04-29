import logging
import networking.robust_mqtt as mqtt
import networking.http as http
import socket
from time import sleep

log = logging.getLogger("Remote_server")

DEFAULT_REMOTE_SERVER = ["MQTT", "172.17.60.2", "1883"]

class Remote_server:

    def __init__(self, protocol, ip, port, token):
        self.protocol = protocol
        self.ip = ip
        self.port = port
        self.token = token
        self.http = None
        self.mqtt = None
        self.initialize()

    def initialize(self):
        if self.protocol == "MQTT":
            log.info("Initializing remote_server MQTT:" + str(self.ip) +
            ":" + str(self.port))
            self.mqtt = mqtt.MQTTClient(self.token, self.ip,
            self.port, self.token, self.token)
        elif self.protocol == "HTTP":
            self.http = http.HTTP()
            self.http.host = self.ip
            self.http.port = self.port

    def restart_mqtt_obj(self):
        try:
            self.mqtt.sock.close()
        except:
            log.exception("Failed to close MQTT socket")
        self.initialize()

    # Initialize MQTT
    def initialize_mqtt(self, keepalive=0):
        self.mqtt.keepalive = keepalive
        try:
            if self.mqtt.sock is not None:
                log.info("Found existing socket. Closing it.")
                self.mqtt.sock.close()
            log.info("Trying to connect")
            self.mqtt.connect()
            log.info("successfully connected")
            self.subscribe_to_server(_type='initial')
            self.subscribe_to_server(_type='attribute')
            return True
        except OSError:
            log.exception("Could not connect to MQTT server.")
            return False

    # Subscribe to a server's action
    # (e.g the possibility to recieve attribute updates)
    def subscribe_to_server(self, _type='initial'):
        if _type == 'initial':
            path = mqtt.SUBSCRIBE_PATH
        else:
            path = mqtt.ATTRIBUTES_PATH
        if self.mqtt is not None:  # MQTT == primary protocol
            self.mqtt.subscribe(path)  # NEED work on what the server expects
        elif self.http is not None:
            path = token_into_path(self.token, http.SUBSCRIBE_PATH)
            packet = self.http.http_to_packet("GET", path, None, None)
            if packet:  # Send message
                self.http.send_message(packet)
            else:
                log.warning("Missing vital information for an HTTP message: "
                + packet)

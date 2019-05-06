import logging
import networking.robust_mqtt as mqtt
import networking.http as http

log = logging.getLogger("Remote_server")

DEFAULT_REMOTE_SERVER = ["MQTT", "172.17.60.2", "1883"]


class RemoteServer:

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

    # Initialize MQTT
    def initialize_mqtt(self, keepalive=0):
        self.mqtt.keepalive = keepalive
        log.info("Trying to connect")
        self.mqtt.connect()
        log.info("successfully connected")
        self.subscribe_to_server(_type='initial')
        self.subscribe_to_server(_type='attribute')

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
            pass
            # TODO - add HTTP support for device-server communication

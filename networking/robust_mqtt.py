import utime
from networking import mqtt
import logging

log = logging.getLogger("robust_MQTT")

TELEMETRY_PATH = 'v1/devices/me/telemetry'
SUBSCRIBE_PATH = 'v1/devices/me/attributes/response/+'
ATTRIBUTES_PATH = 'v1/devices/me/attributes'
REQUEST_ATTR_PATH = 'v1/devices/me/attributes/request/'


class MQTTClient(mqtt.MQTTClient):

    DELAY = 2
    DEBUG = False
    RETRIES = 5

    def delay(self, i):
        utime.sleep(self.DELAY + i)

    def reconnect(self):
        i = 0
        while 1:
            if i >= self.RETRIES:
                break
            try:
                super().disconnect()
                return super().connect(False)
            except OSError:
                log.exception("MQTT Reconnect ERROR:")
                self.delay(i)
                i += 1

    def publish(self, topic, msg, retain=False, qos=0):
        while 1:
            try:
                return super().publish(topic, msg, retain, qos)
            except OSError:
                log.exception("MQTT Publish ERROR:")
            self.reconnect()

    def wait_msg(self):
        while 1:
            try:
                return super().wait_msg()
            except OSError:
                log.exception("MQTT wait_msg ERROR:")
            self.reconnect()

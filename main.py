from time import sleep
from lib.ue import UE
from networking.network_iot import initialize_wifi
import ujson
import lib.logging as logging
import lib.messages as messages
from machine import SD
import os

log = logging.getLogger("Main")

def _callback_message_to_config(topic, message):
    remote = ue.remote_server
    message = message.decode('UTF-8')
    topic = topic.decode('UTF-8')
    log.info("Recieved message {1} to topic {0}".format(topic, message))
    ue.turn_dict_to_config(ujson.loads(message))
    if ue.remote_server != remote:
        if ue.remote_server.mqtt is not None: # New server is communicating via MQTT
            ue.remote_server.mqtt.set_callback(_callback_message_to_config)
            ue.remote_server.initialize_mqtt(ue.attributes["uploadFrequency"] * 3)
    ue.remote_server.mqtt.check_msg()  # We successfully recieved one message, check if another is waiting.

def main():
    # Initial configuration
    # Check if WiFi needs to be configured (User or Access-Point)
    if ue.wifi is not None:
        initialize_wifi(ue)

    # Check if SIM is readable and LTE is configured
    if ue.lte and ue.sim.iccid:
        ue.lte.initialize_lte()
        ue.lte.lte_connect_procedure()

    # Wait untill connected to a network --> send initial messages
    while not ue.lte.lte.isconnected():
        sleep(1)

    # Send data while connected to a remote destination
    if ue.remote_server.http is not None:  # Send messages via http, untill reconfiguration
        # TODO to implement HTTP part
        pass
    elif ue.remote_server.mqtt is not None:  # Send messages via mqtt, untill reconfiguration
        ue.remote_server.mqtt.set_callback(_callback_message_to_config)
        log.info("Running mqtt first time")
        ue.remote_server.initialize_mqtt(ue.attributes["uploadFrequency"] * 3)
        # Initial configuration - ask for shared attributes
        messages.request_attributes(ue.remote_server, ue.client_attributes,
         ue.server_attributes, ue.shared_attributes)
        ue.remote_server.mqtt.wait_msg()
        # Get shared attributes for initial configuration
        messages.request_attributes(ue.remote_server, ue.client_attributes,
         ue.server_attributes, ue.shared_attributes)
        ue.remote_server.mqtt.wait_msg()
        if ue.lte.lte.isconnected() is False:
            ue.lte.lte_connect_procedure()
            sleep(1)

    # Everything has been initialized
    while True:
        if ue.lte.lte.isconnected() is True:
            # Send sensors telemetry
            if ue.remote_server.mqtt is not None:  # MQTT == primary protocol
                try:
                    log.info("Trying to send sensor")
                    messages.send_sensors_via_mqtt(ue)
                except OSError:
                    log.exception("Error sending MQTT message to server.")
                    ue.remote_server.restart_mqtt_obj()
                    ue.remote_server.mqtt.set_callback(_callback_message_to_config)
                    ue.remote_server.initialize_mqtt()
                    continue
            elif ue.remote_server.http is not None:
                messages.send_sensors_via_http(ue)
                # TODO - reconnect HTTP socket on disconnection
            ue.remote_server.mqtt.check_msg()
            sleep(ue.attributes['uploadFrequency'])
        else:
            # NEED to check LTE reconnection
            ue.lte.lte_connect_procedure()


# Initialize ue object and print it's data
sd = SD()
os.mount(sd,'/sd')
ue = UE()
ue.print_info()
# Wait untill initial configuration has been updated
sleep(2)
ue.start_sensors()
main()

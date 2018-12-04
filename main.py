from time import sleep
from lib.ue import UE
import lib.logging as logging
from lib.wifi import WLAN_AP
import lib.messages as messages
from lib.network_iot import initialize_wifi, initialize_lte, lte_connect_procedure
from lib.mqtt import MQTTException

log = logging.getLogger("Main")

def wait_for_answer():
    ue.config.http.open_socket()
    ue.config.http.s.settimeout(ue.config.upload_frequency)
    response = ''
    while True:
        try:
            data = str(ue.config.http.s.recv(100), 'utf8')
        except TimeoutError:
            ue.config.http.s.close()
            return False
        if data:
            response += data
        else:
            break
    print (data)
    ue.config.http.s.close()
    return True

def _callback_message_to_config(topic, message):
    message = message.decode('UTF-8')
    topic = topic.decode('UTF-8')
    log.info("Recieved message {1} to topic {0}".format(topic, message))
    ue.config.turn_message_to_config(message)
    ue.config.mqtt.check_msg() # We successfully recieved one message, check if another is waiting.

def main():
    # Initial configuration
    # Check if WiFi needs to be configured (User or Access-Point)
    if ue.config.wifi is not None:
        initialize_wifi(ue)

    # Check if SIM is readable and LTE is configured
    if ue.config.lte is True and ue.sim is True:
        initialize_lte(ue)
        lte_connect_procedure(ue)

    # Wait untill connected to a network --> send initial messages
    while ue.isconnected() is False:
        sleep(1)

    if ue.has_alarms() is True:
        ue.start_sensors()

    # Send data while connected to a remote destination
    if ue.config.http is not None: # Send messages via http, untill reconfiguration
        pass
    elif ue.config.mqtt is not None: # Send messages via mqtt, untill reconfiguration
        ue.config.mqtt.set_callback(_callback_message_to_config)
        ue.config.mqtt.connect()
        messages.subscribe_to_server(ue.config, _type='initial')
        messages.subscribe_to_server(ue.config, _type='attribute')
    messages.send_attribute(ue, str({'Name':ue.config.deviceName}))
    messages.request_attributes(ue) # Initial configuration - ask for shared attributes
    ue.config.mqtt.wait_msg()
    messages.request_attributes(ue) # Get shared attributes for initial configuration
    ue.config.mqtt.wait_msg()
    while True:
        if (ue.isconnected() is True):
            # Send sensors telemetry
            if ue.config.mqtt is not None: # MQTT == primary protocol
                messages.send_sensors_via_mqtt(ue)
            elif ue.config.http is not None:
                messages.send_sensors_via_http(ue)
            ue.config.mqtt.check_msg()
            sleep(ue.config.uploadFrequency)
        else:
            # reconnect
            pass


##########################################
###########    BEGGINING    ##############
##########################################
# Initialize ue object and print it's data
ue = UE()
ue.print_info()
# Wait untill initial configuration has been updated
sleep(2)
main()

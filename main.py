from time import sleep
from lib.ue import UE
import lib.logging as logging
from lib.wifi import WLAN_AP
import lib.messages as messages
from lib.network_iot import initialize_wifi, initialize_lte, lte_connect_procedure

log = logging.getLogger("Main")

def wait_for_answer():
    ue.config.http.open_socket()
    ue.config.http.s.settimeout(ue.config.sleep_timer)
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

def send_messages_while_connected(protocol):
    while(ue.isconnected() is True):
        # Start sending sensors telemetry
        if protocol == "HTTP":
            messages.send_sensors_via_http(ue)
        elif protocol == "MQTT":
            messages.send_sensors_via_mqtt(ue)
        sleep(ue.config.sleep_timer)

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
        send_alarm_attribute()

    # Send data while connected to a remote destination
    if ue.config.http is not None: # Send messages via http, untill reconfiguration
        send_messages_while_connected("HTTP")
    elif ue.config.mqtt is not None: # Send messages via mqtt, untill reconfiguration
        send_messages_while_connected("MQTT")

##########################################
###########    BEGGINING    ##############
##########################################
# Initialize ue object and print it's data
ue = UE()
ue.print_info()
# Wait untill initial configuration has been updated
sleep(2)

main()

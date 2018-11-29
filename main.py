from lib.ue import UE
from lib.network_iot import Network
import lib.http as http
from time import sleep
import lib.logging as logging
from lib.wifi import WLAN_AP
log = logging.getLogger("Main")

def subscribe_to_server():
    try:
        path = http.SUBSCRIBE_PATH.replace('token', ue.config.token)
    except AttributeError as e:
        log.exception()
    packet = ue.config.http.http_to_packet("GET", path, None, None)
    if packet is not False:
        ue.config.http.send_message(packet)
    else:
        log.warning("Missing vital information for an HTTP message: " + packet)

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

def send_sensors_via_mqtt():
    mqtt_message = ue.sensors_into_message()
    mqtt_client.publish(mqtt_message)

def config_lte():
    # Check if LTE is configured to be turned on
    if ue.lte.isconnected() is False:
        # Create LTE network instance
        lte_network = Network(ue, "LTE", ue.config.lte_bands)
        # Make initial configuration to modem
        ue.p('AT!="setDbgPerm full"')
        lte_network.configure_network()
        # lte_network.print_info()

def config_wifi():
    # Check if WiFi is configured to be turned on
    if ue.config.wifi.mode == WLAN_AP:
        # Create access point for wifi
        ue.config.wifi.print_wifi()
    else: # Device needs to connect to a remote wifi gateway
        # Try to connect to wifi gateway and get ip adress and gw info
        ue.config.wifi.print_wifi()

def lte_connect_procedure():
    ue.attach()
    if ue.lte.isattached():
        ue.print_network_info()
        ue.connect(cid=1) # Need to check if it's possible to get a different cid

def send_messages_while_connected():
    while ue.lte.isconnected() is True:
        # Try to open HTTP socket
        ue.send_sensors_via_http()
        sleep(ue.config.sleep_timer)

def send_alarm_attribute():
    try:
        path = http.SUBSCRIBE_PATH.replace('token', ue.config.token)
    except AttributeError as e:
        log.exception()
    content_type = "application/json"
    packet = ue.config.http.http_to_packet("POST", path, content_type, {'alarms':True})
    if packet is not False:
        ue.config.http.send_message(packet)
    else:
        log.warning("Missing vital information for an HTTP message: " + packet)

def has_alarms():
    for sensor in ue.config.sensors:
        if "Alarm" in sensor.type:
            return True
    return False

def start_sensors():
    for sensor in ue.config.sensors:
        if "Alarm" in sensor.type:
            sensor.start_sensor(ue)

def main():
    while(True):
        if ue.config.wifi is not None:
            config_wifi()
        # Check if SIM is readable and LTE is configured
        if ue.config.lte is True and ue.sim is True:
            config_lte()
            lte_connect_procedure()
            if has_alarms() is True:
                start_sensors()
                send_alarm_attribute()
            send_messages_while_connected()

# Initialize ue object and print it's data
ue = UE()
ue.print_info()
# Wait untill initial configuration has been updated
sleep(5)

main()

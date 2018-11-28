from lib.ue import UE
from lib.network_iot import Network
import lib.http as http
from time import sleep
import lib.logging as logging
from lib.wifi import WLAN_AP
log = logging.getLogger("Main")

# Initialize ue object and print it's data
ue = UE()
ue.print_info()

# Wait untill initial configuration has been updated
sleep(5)

def send_sensors_via_http():
    message = ue.sensors_into_message()
    type = "POST"
    try:
        path = http.TELEMETRY_PATH.replace('token', ue.config.token)
    except AttributeError as e:
        log.exception()
    content_type = "application/json"
    packet = ue.config.http.http_to_packet(type, path, content_type, message)
    if packet is not False:
        ue.config.http.send_message(packet)
        #wait_for_answer
            #if ack good
            #else if 400 bad http request
            #else if 401 bad token
            #  else if 404 resource not found
    else:
        log.warning("Missing vital information for an HTTP message: " + packet)

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

# Check if LTE is configured to be turned on
if ue.config.lte is True:
    if ue.lte.isconnected() is False:
        # Create LTE network instance
        lte_network = Network(ue, "LTE", ue.config.lte_bands)
        # Make initial configuration to modem
        ue.p('AT!="setDbgPerm full"')
        lte_network.configure_network()
        lte_network.print_info()

# Check if WiFi is configured to be turned on
if ue.config.wifi is not None:
    if ue.config.wifi.mode == WLAN_AP:
        # Create access point for wifi
        ue.config.wifi.print_wifi()
    else: # Device needs to connect to a remote wifi gateway
        # Try to connect to wifi gateway and get ip adress and gw info
        ue.config.wifi.print_wifi()

# Check if SIM is readable
if (ue.sim is True):
    print (ue.attach())
    if ue.lte.isattached():
        ue.print_network_info()
    print(ue.create_info_list())
    print (ue.connect(cid=1))

if ue.lte.isconnected() is True:
    # Try to open HTTP socket
    try:
        ue.config.http.open_socket()
    except AttributeError:
        try:
            ue.config.mqtt.connect()
        except AttributeError:
            log.exception()

    # Subscribe to attributes updates

    #subscribe_to_server()
    # Try to open socket and wait
    #while (True):
        # Send periodic message over HTTP and listen to upcoming messages
        #send_sensors_via_http()
        #wait_for_answer()
    #ue.add_sensor('T-1', 'Temperature', 0)
    #ue.add_sensor('Location-1', 'GPS', 0)
    #ue.add_sensor('Door-LAB1', 'Boolean', 0)

    #send_sensors_via_mqtt()
    #listen_http(80)
    #download_config()
    #update_config()
    pass

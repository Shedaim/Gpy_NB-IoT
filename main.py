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
    content_type = "application/json"
    packet = ue.config.http.http_to_packet(type, content_type, message)
    if packet is not False:
        ue.config.http.send_post_message(packet)
        #wait_for_answer
            #if ack good
            #else if 400 bad http request
            #else if 401 bad token
            #  else if 404 resource not found 
    else:
        log.warning("Missing vital information for an HTTP message: " + packet)

def send_sensors_via_mqtt():
    mqtt_message = ue.sensors_into_message()
    client = MQTTClient("GPy-Roni", "172.17.60.2", port=1883)
    client.connect()
    while(True):
        mqtt_client.publish(mqtt_message)
        sleep(10)

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
    while (True):
        send_sensors_via_http()
        sleep(ue.config.sleep_timer)
    #ue.add_sensor('T-1', 'Temperature', 0)
    #ue.add_sensor('Location-1', 'GPS', 0)
    #ue.add_sensor('Door-LAB1', 'Boolean', 0)

    #send_sensors_via_mqtt()
    #listen_http(80)
    #download_config()
    #update_config()
    pass

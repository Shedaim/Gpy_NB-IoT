from lib.ue import UE
from lib.network_iot import Network
import lib.http as http
from time import sleep
import lib.logging as logging

log = logging.getLogger("Main")

# Initialize ue object and print it's data
ue = UE()
ue.print_info()

# Wait untill initial configuration has been updated
sleep(5)

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
    print("-----WIFI SETUP-----")
    ue.config.wifi.wifi_metadata()
    print("-----WIFI SETUP END-----")

# Check if SIM is readable
if (ue.sim is True):
    print (ue.attach())
    if ue.lte.isattached():
        ue.print_network_info()
    print(ue.create_info_list())
    print (ue.connect(cid=1))

if ue.lte.isconnected() is True:
    #ue.add_sensor('T-1', 'Temperature', 0)
    #ue.add_sensor('Location-1', 'GPS', 0)
    #ue.add_sensor('Door-LAB1', 'Boolean', 0)
    #send_sensors_via_http():
    #send_sensors_via_mqtt()
    #listen_http(80)
    #open_mgmt_socket()
    #download_config()
    #update_config()
    pass

def send_sensors_via_http():
    http_message = ue.sensors_into_message()
    http.http_msg(http_message, type="POST")

def send_sensors_via_mqtt():
    mqtt_message = ue.sensors_into_message()
    client = MQTTClient("GPy-Roni", "172.17.60.2", port=1883)
    client.connect()
    while(True):
        mqtt_client.publish(mqtt_message)
        sleep(10)

from lib.ue import UE
from lib.network_iot import Network
from lib.http import listen_http
from time import sleep

ue = UE()
lte_network = Network(ue, "LTE", bands=[28])

ue.p('AT!="setDbgPerm full"')
ue.print_info()
lte_network.configure_network()
lte_network.print_info()

if (ue.sim is True):
    print (ue.attach(True))
    ue.print_network_info()
    print(ue.create_info_list())
    print (ue.connect(True))


if ue.lte.isconnected() is True:
    #start_mqtt()
    #listen_http(80)
    #open_mgmt_socket()
    #download_config()
    #update_config()
    pass

def start_mqtt():
    import random
    client = MQTTClient("GPy-Roni", "172.17.60.2", port=1883)
    client.connect()
    while(True):
        mqtt_client.publish("Temperature", random.uniform(20,30))
        sleep(10)

# Class created for storing, sending and recieving configuration variables
import lib.logging as logging
import ujson
import lib.http as http
from lib.sensor import Sensor
import lib.wifi as wifi
import lib.mqtt as mqtt

log = logging.getLogger("Config")

class Configuration():

    def __init__(self):
        self.deviceName = "Pycom-Default"
        self.uploadFrequency = None
        self.lte = None
        self.wifi = None
        self.bt = None
        self.remoteServer = list()
        self.sensors = set()
        self.http = None
        self.token = None
        self.sharedKeys = ['sharedKeys']
        self.clientKeys = []
        self.serverKeys = []

    # Create HTTP message to download configurations or read from saved file
    def get_config(self, initial=False):
        if initial is True:
            with open('Initial_configuration.json', 'r') as f:
                result = f.read()
        else:
            # NEED to Get all attributes
            pass
        log.info('Read initial configuration: ' + result)
        self.turn_message_to_config(result)

    def update_initial_file(self, json_string):
        with open('Initial_configuration.json', 'w') as f:
            f.write(json_string)

    # Convert dictionary to specific object configurations
    def turn_message_to_config(self, message):
        dictionary = ujson.loads(message)
        if self.token is None:
            try:
                self.token = dictionary['Token']
            except AttributeError:
                pass
        for val in dictionary:
            if val == "deviceName":
                self.deviceName = dictionary[val]
            elif val == "uploadFrequency":
                self.uploadFrequency = int(dictionary[val])
                # NEED to add implementation of sleep (eDRX?)
            elif val == "remoteServer":
                # Data in the form 'Protocol:IP:port:path'
                self.config_remote(dictionary[val].split(':'))
            elif val == "LTE":
                self.lte = True
                self.lte_bands = dictionary[val]
            elif val == "WIFI":
                self.config_wifi(dictionary[val])
            elif val == "BT":
                self.bt = True
                pass # NEED to parse variables.
            elif val == "Sensors":
                for sensor in dictionary[val]:
                    self.config_sensor(sensor.split(','))
            elif val == "shared":
                if 'sharedKeys' in dictionary[val]:
                    self.turn_keys_to_list(dictionary[val]['sharedKeys'])
                if 'clientKeys' in dictionary[val]:
                    self.turn_keys_to_list(ictionary[val]['clientKeys'])
                if 'serverKeys' in dictionary[val]:
                    self.turn_keys_to_list(dictionary[val]['serverKeys'])

    def turn_keys_to_list(self, keys_string):
        assert keys_string[0] == '[' and keys_string[-1] == ']', "Keys recieved are not a list"
        keys_string = keys_string[1:-1]
        return keys_string.split(',')


    # Config the Wifi module
    def config_wifi(self, data):
        # 0 - mode         # 1 - ssid                       # 2 - password
        # 3 - channel      # 4 - antenna pin or internal    # 5 - Default GW
        # 6 - GW subnet    # 7 - ip address                 # 8 - subnet
        try:
            self.wifi = wifi.WIFI(data[0],data[1],(wifi.WLAN_WPA2,data[2]),data[3],data[4])
            if data[0] == wifi.WLAN_AP: # WiFi in AP mode
                self.wifi.ip_configuration(data[5], data[6])
            else: # WiFi in Station mode
                self.wifi.ip_configuration(data[5], data[6], data[0], data[7], data[8])
        except AttributeError:
            log.exception("WiFi configuration is wrong.")

    # Config the remote server details given configuration data
    def config_remote(self, data):
        self.remoteServer.append(data)
        if data[0] == "HTTP":
            self.http = http.HTTP()
            self.http.host = data[1]
            self.http.port = int(data[2])
        elif data[0] == "MQTT":
            self.mqtt = mqtt.MQTTClient(self.token, data[1], int(data[2]), self.token, self.token)

    # Config a sensor given it's configuration data
    def config_sensor(self, data):
        # Name, Model, Pins
        # Pins = 0 --> internal sensor
        # Pins = [Ground, VCC, Data]
        for sensor in self.sensors:
            if sensor.name == data[0] and sensor.model == data[1] and sensor.pins == data[2:]: # Sensor already configured.
                log.info("Sensor {0} already exists. No changes done.".format(data[0]))
                return
            elif sensor.name == data[0]: # Found sensor with the same name but different configuration.
                log.warning("Sensor with the same name ({0}), already exists, changing sensor values.")
                self.delete_sensor(data[0]) # Delete old sensor details
                self.add_sensor(data[0], data[1], data[2:])
                return
        # No similar sensor found.
        self.add_sensor(data[0], data[1], data[2:])
        return

    # Function used to configure a new sensor
    def add_sensor(self, name, model, pins=0):
        for sensor in self.sensors:
            if sensor.name == name: # Duplicate name --> do not add sensor
                log.error("Sensor {0} already exists.".format(name))
                return False
        sensor = Sensor(name, model, pins)
        self.sensors.add(sensor)
        log.info("Sensor {0} added successfully.".format(name))
        return True

    # Function used to remove an old sensor - Also used if sensor's type
    # or pins need to change, as there is no update_sensor method
    def delete_sensor(self, name):
        for sensor in self.sensors:
            if sensor.name == name:
                self.sensors.remove(sensor)
                log.info("Sensor {0} removed successfully.".format(name))
                return True
        lof.info("Sensor {0} not found.".format(name))
        return False

    # Print configuration variables and it's values
    def print_config(self):
        if self.deviceName is not None:
            print ("Name: " + self.deviceName)
        if self.uploadFrequency is not None:
            print ("Sleep timer (seconds): " + str(self.uploadFrequency))
        if self.remoteServer is not None:
            for server in self.remoteServer:
                print ("Remote server (Protocol:IPaddress:Port:path): " + str(server))
        if self.lte is True:
            print ("LTE bands: " + str(self.lte_bands))
        if sekf.wifi is not None:
            print ("WiFi configuration:\n" + self.wifi.print_wifi())

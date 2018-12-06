# Class created for storing, sending and recieving configuration variables
import lib.logging as logging
import ujson
import lib.http as http
from lib.sensor import Sensor
import lib.wifi as wifi

log = logging.getLogger("Config")


class Configuration:

    def __init__(self):
        self.deviceName = "Pycom-Default"
        self.uploadFrequency = 60
        self.lte = False
        self.lte_bands = None
        self.wifi = None
        self.bt = None
        self.remoteServer = list()
        self.sensors = set()
        self.http = None
        self.mqtt = None
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
            result = 'Not implemented Yet'
        log.info('Read initial configuration: ' + result)
        self.turn_message_to_config(result)

    # Convert dictionary to specific object configurations
    def turn_message_to_config(self, message):
        dictionary = ujson.loads(message)
        if self.token is None:
            try:
                self.token = dictionary['Token']
                del dictionary['Token']
            except AttributeError:
                pass
        for key in dictionary:
            if key == "shared":  # Got shared attributes from server
                for attr in dictionary[key]:  # go over attributes in response (dict inside a dict)
                    assert isinstance(dictionary[key], dict), "shared attributes recieved not as a dictionary"
                    self.value_to_config(attr, dictionary[key][attr])
            else:
                self.value_to_config(key, dictionary[key])

    def value_to_config(self, key, val):
        log.info("Updating attribute '{0}' to value '{1}'".format(key, val))
        if key == "deviceName":
            self.deviceName = val
        elif key == "uploadFrequency":
            self.uploadFrequency = int(val)
            # NEED to add implementation of sleep (eDRX?)
        elif key == "remoteServer":
            # Data in the form 'Protocol:IP:port'
            self.config_remote(val.split(':'))
        elif key == "LTE":
            self.lte = True
            self.lte_bands = val
        elif key == "WIFI":
            self.config_wifi(val)
        elif key == "BT":
            self.bt = True
            pass  # NEED to parse variables.
        elif key == "Sensors":
            for sensor in val:
                self.config_sensor(sensor.split(','))
        elif key == 'sharedKeys':
            self.sharedKeys = list_string_to_list(val)
        elif key == 'clientKeys':
            self.clientKeys = list_string_to_list(val)
        elif key == 'serverKeys':
            self.serverKeys = list_string_to_list(val)
        else:
            log.warning("Key '{0}' does not match any configure key.".format(key))

    # Config the Wifi module
    def config_wifi(self, data):
        # 0 - mode         # 1 - ssid                       # 2 - password
        # 3 - channel      # 4 - antenna pin or internal    # 5 - Default GW
        # 6 - GW subnet    # 7 - ip address                 # 8 - subnet
        try:
            self.wifi = wifi.WIFI(data[0], data[1], (wifi.WLAN_WPA2, data[2]), data[3], data[4])
            if data[0] == wifi.WLAN_AP:  # WiFi in AP mode
                self.wifi.ip_configuration(data[5], data[6])
            else:  # WiFi in Station mode
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
            import lib.mqtt as mqtt
            if self.mqtt is None:  # First time configuration
                self.mqtt = mqtt.MQTTClient(self.token, data[1], int(data[2]), self.token, self.token)
            else:
                import socket
                import lib.messages as messages
                self.mqtt.disconnect()
                self.mqtt.addr = socket.getaddrinfo(data[1], int(data[2]))[0][-1]
                self.mqtt.connect()
                messages.subscribe_to_server(self, _type='initial')
                messages.subscribe_to_server(self, _type='attribute')

    # Config a sensor given it's configuration data
    def config_sensor(self, data):
        # Name, Model, Pins
        # Pins = 0 --> internal sensor
        # Pins = [Ground, VCC, Data]
        for sensor in self.sensors:
            # Sensor already configured.
            if sensor.name == data[0] and sensor.model == data[1] and sensor.pins == data[2:]:
                log.info("Sensor {0} already exists. No changes done." + data[0])
            # Sensor already configured but changes need to be done.
            elif sensor.name == data[0]:  # Found sensor with the same name but different configuration.
                log.warning("Sensor with the same name ({0}), already exists, changing sensor values.")
                self.delete_sensor(data[0])  # Delete old sensor details
                self.add_sensor(data[0], data[1], data[2:])
        # No similar sensor found.
        self.add_sensor(data[0], data[1], data[2:])

    # Function used to configure a new sensor
    def add_sensor(self, name, model, pins: []):
        for sensor in self.sensors:
            if sensor.name == name:  # Duplicate name --> do not add sensor
                log.error("Sensor {0} already exists.".format(name))
        sensor = Sensor(name, model, pins)
        self.sensors.add(sensor)
        log.info("Sensor {0} added successfully.".format(name))

    # Function used to remove an old sensor - Also used if sensor's type
    # or pins need to change, as there is no update_sensor method
    def delete_sensor(self, name):
        for sensor in self.sensors:
            if sensor.name == name:
                self.sensors.remove(sensor)
                log.info("Sensor {0} removed successfully.".format(name))
        log.info("Sensor {0} not found.".format(name))

    # Print configuration variables and it's values
    def print_config(self):
        if self.deviceName is not None:
            print(' '.join(["Name:", self.deviceName]))
        if self.uploadFrequency is not None:
            print(' '.join(["Sleep timer (seconds):", str(self.uploadFrequency)]))
        if self.remoteServer is not None:
            for server in self.remoteServer:
                print(' '.join(["Remote server (Protocol:IPaddress:Port:path):", str(server)]))
        if self.lte:
            print(' '.join(["LTE bands:", str(self.lte_bands)]))
        if self.wifi is not None:
            print(' '.join(["WiFi configuration:\n", self.wifi.print_wifi()]))


def update_initial_file(json_string):
    with open('Initial_configuration.json', 'w') as f:
        f.write(json_string)


def list_string_to_list(keys_string):
    assert keys_string.startswith('[') and keys_string.endswith(']'), "Keys received are not a list"
    keys_string = keys_string[1:-1]
    return keys_string.split(',')

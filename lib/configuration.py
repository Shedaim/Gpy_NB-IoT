# Class created for storing, sending and recieving configuration variables
import lib.logging as logging
import ujson
import lib.http as http

log = logging.getLogger("Config")

class Configuration():

    def __init__(self):
        self.name = None
        self.sleep_timer = None
        self.lte = None
        self.wifi = None
        self.bt = None
        self.remote_server = list()

    # Create HTTP message to download configurations or read from saved file
    def get_config(self, initial=False):
        if initial is True:
            with open('Initial_configuration.json', 'r') as f:
                result = f.read()
        else:
            full_path = http.REMOTE_SERVER_PATH + '/' + self.name
            result = http.http_msg('', type="GET", path=full_path)
        log.info('Read initial configuration: ' + result)
        self.turn_message_to_config(result)

    # Convert dictionary to specific object configurations
    def turn_message_to_config(self, message):
        dictionary = ujson.loads(message)
        for val in dictionary:
            if val == "Name":
                self.name = dictionary[val]
            elif val == "Sleep_timer":
                self.sleep_timer = dictionary[val]
                # NEED to add implementation of sleep (eDRX?)
            elif val == "Remote_server":
                # Should contain data in the form 'Protocol:IP:port:path'
                data = dictionary[val].split(':')
                self.remote_server.append(dictionary[val].split(':'))
                if data[0] == "HTTP":
                    http.http_config(data[1], data[2], data[3])
            elif val == "LTE":
                self.lte = True
                self.lte_bands = dictionary[val]
            elif val == "WIFI":
                self.wifi = True
                pass # NEED to parse ssid, channels, etc.
            elif val == "BT":
                self.bt = True
                pass # NEED to parse variables.

    # Print configuration variables and it's values
    def print_config(self):
        if self.name is not None:
            print ("Name: " + self.name)
        if self.sleep_timer is not None:
            print ("Sleep timer (seconds): " + str(self.sleep_timer))
        if self.remote_server is not None:
            for server in self.remote_server:
                print ("Remote server (Protocol:IPaddress:Port:path): " + str(server))
        if self.lte is True:
            print ("LTE bands: " + str(self.lte_bands))

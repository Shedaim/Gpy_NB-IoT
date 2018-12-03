# Class that contains functions and parameters used for network
# technologies and interfaces. This class will be used to configure
# the different Interfaces and interact between them.
import lib.logging as logging
from lib.wifi import WLAN_AP

log = logging.getLogger("Network")

SUPPORTED_TECHNOLOGIES = ["LTE", "WIFI", "BT"]

class Network():

    def __init__(self, ue, net_type, bands=False):
        self.lte = ue.lte
        self.lte_bands = bands
        self.net_type = net_type

    # Use the Network type and bands entered, to re-configure the modem
    def configure_network(self):
        log.info("Configuring network with variables: Network = {0}, bands = {1}".format(self.net_type, str(self.lte_bands)))
        if self.net_type not in SUPPORTED_TECHNOLOGIES:
            log.error("Unsupported network type in configure_network.")
            return False
        if self.net_type == "LTE":
            if self.lte_bands is not False:
                # Delete existing bands from scan list
                self.lte.send_at_cmd('AT+CFUN=0')
                self.lte.send_at_cmd('AT!="clearscanconfig"')
                self.lte.send_at_cmd('AT+CGDCONT=1,"IP","secure.motolab.com"')
                # Add required bands to scan list
                for band in self.lte_bands:
                    self.lte.send_at_cmd('AT!="addscanband band={0}"'.format(band))
                # Restart modem with new configuration
                self.lte.send_at_cmd('AT+CFUN=1')
                # Put UE in "Try to register" mode
                self.lte.send_at_cmd('AT+CEREG=2')
            else:
                log.error("No bands added to LTE scan list.")
                return False
        elif self.net_type == "WIFI":
            pass
        elif self.net_type == "BT":
            pass
        return True

    def print_info(self):
        print ("Network type: " + self.net_type)
        print ("Bands: " + ','.join([str(x) for x in self.lte_bands]))

class Cell():

    def __init__(self, lte):
        self.lte = lte
        self.cell_id = None
        self.cpi = None
        self.cell_type = None
        self.dlarfcn = None
        self.rsrp = None
        self.reject_cause = None
        self.registered = None
        self.tac = None
    # Create a list containing important data - Used if data
    # is needed to be sent to server/database
    def create_info_list(self):
        return [self.cell_id, self.dlarfcn, self.rsrp, self.tac, self.registered, self.reject_cause]

    # Gets details of the serving cell indexes the valued data into the class
    def get_details(self):
        if self.lte.isconnected() is False:
            info = self.lte.send_at_cmd('AT!="showDetectedCell"').split('|')
            if len(info) > 20:
                info = info[18:32]
            else:
                #print("Warning: Cell not found. Is the antenna connected?")
                return False
            # Some of the answers contain many unnecessary spaces.
            # Strip to get rid of them.
            self.cell_type = info[0].strip(" ")
            self.dlarfcn = info[1].strip(" ")
            self.cpi = info[2].strip(" ")
            self.rsrp = info[5].strip(" ")
            self.reject_cause = info[13].strip(" ")
            # Return the register state of a subscriber
            info = self.lte.send_at_cmd('AT+CEREG?').split(',')
            if info[1] in ['1','5']: # Both states indicate "Registered"
                self.registered = True
            else:
                self.registered = False
            self.tac = info[2].strip('"')
            self.cell_id = info[3].strip('"')
        else:
            print ("Can't send AT commands while connected. Disconnect first and try again.")
            return False
        return True

    # Print the cell details - for debugging purposes
    def print_all(self):
        if self.cell_id is not None:
            print ("Cell ID: " + self.cell_id)
            print ("Cell Type: " + self.cell_type)
            print ("Tracking Area Code: " + self.tac)
            print ("Earfcn: " + self.dlarfcn)
            print ("RSRP: " + self.rsrp)
            if self.registered is True:
                print ("Status: Registered")
            else:
                print ("Status: Not registered")
            print ("Reject cause: " + self.reject_cause)
        elif self.lte.isconnected() is False:
            print ("Warning: Cell not found. Is the antenna connected?")
            return False
        else:
            print ("Info: No data to display.")
        return True

# Initialize LTE network
def initialize_lte(ue):
    # Check if LTE is configured to be turned on
    if ue.lte.isconnected() is False:
        # Create LTE network instance
        lte_network = Network(ue, "LTE", ue.config.lte_bands)
        # Make initial configuration to modem
        ue.p('AT!="setDbgPerm full"')
        lte_network.configure_network()
        log.info("LTE network initialized.")

# Initialize WiFi
def initialize_wifi(ue):
    # Check if WiFi is configured to be turned on
    if ue.config.wifi.mode == WLAN_AP:
        # Create access point for wifi
        ue.config.wifi.print_wifi()
    else: # Device needs to connect to a remote wifi gateway
        # Try to connect to wifi gateway and get ip adress and gw info
        ue.config.wifi.print_wifi()
    log.info("WiFi network initialized in mode: " + str(ue.config.wifi.mode))

# Connect device to an LTE system
def lte_connect_procedure(ue):
    ue.lte_attach()
    if ue.lte.isattached():
        ue.print_network_info()
        ue.lte_connect(cid=1) # Need to check if it's possible to get a different cid

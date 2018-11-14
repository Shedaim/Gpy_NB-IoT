# Class that contains functions and parameters used for network
# technologies and interfaces. This class will be used to configure
# the different Interfaces and interact between them.

SUPPORTED_TECHNOLOGIES = ["LTE", "WIFI", "BT"]

class Network():

    def __init__(self, ue, net_type, bands=False):
        self.lte = ue.lte
        self.net_type = net_type
        self.bands = bands

    # Use the Network type and bands entered, to re-configure the modem
    def configure_network(self):
        print ("Info: Configuring network...")
        if self.net_type not in SUPPORTED_TECHNOLOGIES:
            print("Warning: Unsupported network type in configure_network.")
            return False
        if self.net_type == "LTE":
            if self.bands is not False:
                # Delete existing bands from scan list
                self.lte.send_at_cmd('AT+CFUN=0')
                self.lte.send_at_cmd('AT!="clearscanconfig"')
                # Add required bands to scan list
                for band in self.bands:
                    self.lte.send_at_cmd('AT!="addscanband band={0}"'.format(band))
                # Restart modem with new configuration
                self.lte.send_at_cmd('AT+CFUN=1')
                # Put UE in "Try to register" mode
                self.lte.send_at_cmd('AT+CEREG=2')
            else:
                print("Error: No bands added to LTE scan list.")
                return False
        elif self.net_type == "WIFI":
            pass
        elif self.net_type == "BT":
            pass
        return True

    def print_info(self):
        print ("Network type: " + self.net_type)
        print ("Bands: " + ','.join([str(x) for x in self.bands]))

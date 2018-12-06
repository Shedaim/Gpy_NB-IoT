from network import WLAN
import binascii

WLAN_STA = 1
WLAN_AP = 2
WLAN_INT_ANT = 0
WLAN_EXT_ANT = 1
WIFI_IP_GATEWAY = '192.168.0.1'
WIFI_MASK = '255.255.255.240'
REMOTE_SERVER_IP = '172.17.60.2'
WLAN_WPA2 = 3


class WIFI:

    wlan = WLAN()

    def __init__(self, mode=1, ssid="PycomAP", auth=(WLAN.WPA2, "PycomAP1"), channel=11,
                 ant=WLAN_INT_ANT, power=False, hidden=False):
        self.mode = mode
        self.ssid = ssid
        self.auth = auth
        self.channel = channel
        self.ant = ant
        self.power = power
        self.hidden = hidden
        self.ip_address = None
        self.subnet = None
        self.server_ip = None
        self.dns = None
        self.wlan.init(mode=self.mode, ssid=self.ssid, auth=self.auth, channel=self.channel,
                       antenna=self.ant, power_save=self.power, hidden=self.hidden)

    def ip_configuration(self, server_ip, dns, mode=1, ip_address=WIFI_IP_GATEWAY, subnet=WIFI_MASK):
        self.mode = mode
        self.ip_address = ip_address
        self.subnet = subnet
        self.server_ip = server_ip
        self.dns = dns
        self.wlan.ifconfig(id=self.mode, config=(self.ip_address, self.subnet, self.server_ip, self.dns))

    def print_wifi(self):
        print("------------Wifi configuration:------------")
        if self.wlan.mode() == 1:
            mode = "Station"
        else:
            mode = "Access Point"
        print("Mode:", mode)
        print("SSID:", self.wlan.ssid())
        print("Channel:", self.wlan.channel())
        print("Wifi gateway ip:", self.ip_address)
        print("Wifi netmask:", self.subnet)
        print("Server IP:", self.server_ip)
        print("DNS IP:", self.dns)
        print("MAC address:", self.mac_pretty_print())

    def mac_pretty_print(self):
        x = binascii.hexlify(self.wlan.mac()).decode('Ascii')
        s = iter(x)
        return '-'.join(x + next(s) for x in s)

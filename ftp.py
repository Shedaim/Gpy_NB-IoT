from machine import SD
import networking.wifi as wifi
import os
import ue
import ujson

try:
    sd = SD()
    os.mount(sd, '/sd')
except OSError:
    print("SD Card not found")

with open('Initial_configuration.json') as file:
    f = file.read()
dictionary = ujson.loads(f)
try:
    data = [2, dictionary['deviceName'],"p@ssw0rd",11,0,"192.168.0.1","255.255.255.0"]
except exception as e:
    print (e.message)
    data = [2, "PycomAP","p@ssw0rd",11,0,"192.168.0.1","255.255.255.0"]
w = wifi.WIFI(data[0], data[1], (wifi.WLAN_WPA2, data[2]), data[3], data[4])
w.ip_configuration(data[5], data[6])

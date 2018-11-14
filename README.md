# Gpy_NB-IoT
NB-IoT initial MicroPython code for use and configuration of the GPy development chip (LTE-NB-IoT, WiFi, BlueTooth) on an Ericsson vEPC.

# Useful information and known issues
1. When configuring the LTE network interface using Network.configure_network() followed by another call to an LTE() object, the call will fail as the LTE() object is being used by Network. To prevent this from happening, wait until network has been configured before calling another LTE() object.
2. Some of the function use 'debug' AT-Commands as part of their logic. Because of this, those functions require the use of 'AT!="setDbgPerm full"'. Currently the debug AT-Command is called on main.py, although this is a security risk. In production releases, this should only be called by permitted functions and users, and should be changed back to 'AT!="setDbgPerm publicOnly"' after completion.

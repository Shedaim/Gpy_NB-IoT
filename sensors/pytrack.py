from sensors.pycoproc import Pycoproc
import utime
from machine import RTC
from sensors.L76GNSS import L76GNSS

__version__ = '1.4.0'

class Pytrack(Pycoproc):

    def __init__(self, i2c=None, sda='P22', scl='P21'):
        Pycoproc.__init__(self, i2c, sda, scl)

    def get_location(self):
        self.rtc = RTC()
        rtc.ntp_sync("pool.ntp.org")
        l76 = L76GNSS(self, timeout=30)
        coord = l76.coordinates()
        return "{} - {} - {}".format(coord, rtc.now(), gc.mem_free())

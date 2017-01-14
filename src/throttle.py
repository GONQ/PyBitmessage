import threading
import time

from configparser import BMConfigParser
from singleton import Singleton
import state

class Throttle(object):
    def __init__(self, limit=0):
        self.limit = limit
        self.speed = 0
        self.txTime = int(time.time())
        self.txLen = 0
        self.total = 0
        self.timer = threading.Event()
        self.lock = threading.RLock()

    def recalculate(self):
        with self.lock:
            now = int(time.time())
            if now > self.txTime:
                self.speed = self.txLen / (now - self.txTime)
                self.txLen -= self.limit * (now - self.txTime)
                self.txTime = now
                if self.txLen < 0 or self.limit == 0:
                    self.txLen = 0

    def wait(self, dataLen):
        with self.lock:
            self.waiting = True
        with self.lock:
            self.txLen += dataLen
            self.total += dataLen
        while state.shutdown == 0:
            self.recalculate()
            if self.limit == 0:
                break
            if self.txLen < self.limit:
                break
            self.timer.wait(0.2)
        with self.lock:
            self.waiting = False

    def getSpeed(self):
        self.recalculate()
        return self.speed

@Singleton
class SendThrottle(Throttle):
    def __init__(self):
        Throttle.__init__(self, BMConfigParser().safeGetInt('bitmessagesettings', 'maxuploadrate')*1024)
    
    def resetLimit(self):
        with self.lock:
            self.limit = BMConfigParser().safeGetInt('bitmessagesettings', 'maxuploadrate')*1024

@Singleton
class ReceiveThrottle(Throttle):
    def __init__(self):
        Throttle.__init__(self, BMConfigParser().safeGetInt('bitmessagesettings', 'maxdownloadrate')*1024)

    def resetLimit(self):
        with self.lock:
            self.limit = BMConfigParser().safeGetInt('bitmessagesettings', 'maxdownloadrate')*1024

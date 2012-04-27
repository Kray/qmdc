import math
import random
import sys
import socket
import threading
import traceback

from PyQt4.QtCore import *
from PyQt4.QtGui import *

no_dbus = False
try:
    import dbus
    import dbus.service
    import dbus.mainloop.qt
except ImportError, e:
    print "unable to import DBus: " + e.__str__()
    print "DBus interface will be unavailable"
    no_dbus = True

no_notify = False
try:
    import pynotify
except ImportError, e:
    print "unable to import pynotify: " + e.__str__()
    print "notifications will be unavailable"
    no_notify = True

import mdc # Our audio sink


class MdError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

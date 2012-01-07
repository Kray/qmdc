import math
import random
import sys
import socket
import threading

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import dbus
import dbus.service
import dbus.mainloop.qt

import mdc # Our audio sink


class MdError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

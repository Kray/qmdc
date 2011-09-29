import math
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
        
def parseDict(line):
    result = {}
    next_escaped = False
    
    key = ""
    tmp = ""

    for c in line:
        if next_escaped:
            if c == ' ':
                tmp += ' '
            elif c == '\\':
                tmp += '\\'
            elif c == '=':
                tmp += '='
            else: pass # Unknown escape sequence, ignore
            next_escaped = False
            continue
        if c == '\\':
            next_escaped = True
        elif c == '=' and len(key) == 0:
            key = tmp
            tmp = ""
        elif c == ' ':
            if len(key) == 0:
                key = "id"
                
            result[key] = tmp
            key = ""
            tmp = ""
        else:
            tmp += c
    if len(key) > 0 or len(tmp) > 0:
        result[key] = tmp

    return result
    
def escape(src):
    result = ""
    
    for c in src:
        if c == " ":
            result += "\\ "
        elif c == "\\":
            result += "\\\\"
        elif c == "=":
            result += "\\="
        else:
            result += c
    return result

class Connection(socket.socket):
    def __init__(self, host, port):
        socket.socket.__init__(self, socket.AF_INET, socket.SOCK_STREAM)
        
        self.mutex = threading.RLock()
        self.running = False
        
        self.buffer = b''
        self.queue = []
        
        self.connect((host, port))
        self.send(b"hello 1 qmdc\n")
        line = self.receive(["hello"])
    
    def auth(self, user, passw):
        with self.mutex:
            self.send(u"auth {} {}\n".format(user, passw).encode("utf-8"))
            line = self.receive(["auth"])
    def search(self, string):
        with self.mutex:
            self.send(u"search {}\n".format(escape(string)).encode("utf-8"))
            
            result = []
            while 1:
                msg = self.receive(["track", "search"])
                if msg[0] == "search":
                    break
                if msg[0] != 'track':
                    print u"error: not track '{}'".format(msg)
                track = parseDict(msg[1])
                result.append(track)
            return result
    def open(self, trackid):
        if self.running:
            self.running = False
            self.thread.join()
            
        with self.mutex:
            self.send("open {}\n".format(trackid).encode("utf-8"))
            msg = self.receive(["open"])
            
            result = parseDict(msg[1])
            if len(msg) > 2:
                result["extradata"] = msg[2]
            
            self.queue = []
            
            self.thread = threading.Thread(target=self.process)
            self.thread.start()
            return result
    
    def seek(self, position):
        with self.mutex:
            self.send("seek {}\n".format(position).encode("utf-8"))
            msg = self.receive(["seek"])
            
            self.queue = []
            mdc.flush()
            
            if self.running == False:
                self.thread = threading.Thread(target=self.process)
                self.thread.start()
            
    
    def process(self):
        self.running = True
        while self.running:
            msg = self.receive(["packet"])
            if len(msg[2]) == 0:
                self.running = False
                return
            mdc.packet(msg[2])
    
    def receive(self, methods):
        with self.mutex:
            for item in self.queue:
                if item[0] in methods:
                    del self.queue[0]
                    return item
            while 1:
                msg = self._receive_next()
                if msg[0] == "error":
                    raise MdError(msg[1])
                if msg[0] in methods:
                    return msg
                
    def _receive_next(self):
        with self.mutex:
            lines = self.buffer.split(b'\n')
            if len(self.buffer) == 0 or (len(lines) == 1 and self.buffer[-1] != b'\n'):
                data = self.recv(1024)
                self.buffer += data
                if len(data) == 0:
                    QMessageBox.critical(qmdc, "Error", "Connection terminated.")
                    raise MdError("Connection terminated.")
                return self._receive_next()
            
            line = lines[0].decode("utf-8", errors="replace")
            lines.pop(0)
            self.buffer = b"\n".join(lines)
            msg = []
            split = line.split(" ")
            msg.append(split[0])
            dict = parseDict(line)
            if len(split) > 1:
                msg.append(" ".join(split[1:]))
                if "payload" in dict:
                    msg.append(self._receive_bin(int(dict["payload"])))
            return msg
                
    def _receive_bin(self, size):
        with self.mutex:
            if len(self.buffer) < size:
                data = self.recv(size - len(self.buffer))
                if len(data) == 0:
                    QMessageBox.critical(qmdc, "Error", "Connection terminated.")
                    raise MdError("Connection terminated.")
                self.buffer += data
                return self._receive_bin(size)
            result = self.buffer[:size]
            self.buffer = self.buffer[size:]
            return result



class NowPlaying(QWidget):
    def __init__(self, parent):
        super(NowPlaying, self).__init__(parent)
        
        self.vlayout = QVBoxLayout(self)
        self.setLayout(self.vlayout)

class TrackListView(QTreeView):
    def __init__(self, parent):
        super(TrackListView, self).__init__(parent)
      
        self.setRootIsDecorated(False)
        self.setSortingEnabled(True)
        self.setAllColumnsShowFocus(True)
        self.setSelectionBehavior(QTreeView.SelectRows)
        
        #self.connect(self.results, SIGNAL("activated(QModelIndex)"), self.onActivate)
        self.connect(self, SIGNAL("doubleClicked(QModelIndex)"), self.onDoubleClick)
        
        
        self.model = QStandardItemModel(self)
        self.model.setHorizontalHeaderItem(1, QStandardItem("#"))
        self.model.setHorizontalHeaderItem(2, QStandardItem("Title"))
        self.model.setHorizontalHeaderItem(3, QStandardItem("Artist"))
        self.model.setHorizontalHeaderItem(4, QStandardItem("Album"))
        self.model.setHorizontalHeaderItem(5, QStandardItem("Length"))
        
        self.setModel(self.model)
        
        self.setColumnHidden(0, True) # Column 0 stores track id
        self.setColumnWidth(1, QFontMetrics(QStandardItem().font()).width("000"));

    def dropEvent(self, event):
        dst = self.indexAt(event.pos()).row()
        srcDiff = 0
        if event.source() == self:
            for row in self.selectedRows():
                if dst == row + srcDiff: continue
                
                track = self.model.takeRow(row + srcDiff)
                
                if dst == -1 or dst > row + srcDiff: srcDiff = srcDiff - 1
                else: dst = dst + 1
                
                if dst == -1: self.model.appendRow(track)
                else: self.model.insertRow(dst, track)
        else:
            self.emit(SIGNAL("dropAction(QWidget, int)"), event.source(),
                      self.indexAt(event.pos()).row())

    
    def addTrack(self, track):
        line = [QStandardItem(""), QStandardItem(""), QStandardItem(""), QStandardItem(""), QStandardItem(""), QStandardItem("")]
        line[0] = QStandardItem(track.get("id"))
        
        if "number" in track:
            try:
                if int(track["number"]) > 0:
                    line[1] = QStandardItem("{:02d}".format(int(track["number"])))
                    line[1].setTextAlignment(Qt.AlignRight)
            except ValueError:
                pass
        if "title" in track:
            line[2] = QStandardItem(track.get("title"))
        if "artist" in track:
            line[3] = QStandardItem(track.get("artist"))
        if "album" in track:
            line[4] = QStandardItem(track.get("album"))
        if "duration" in track:
            line[5] = QStandardItem(track.get("duration"))
            
        for item in line:
            item.setEditable(False)
            
        self.model.appendRow(line)
    
    def trackByRow(self, row):
        track = {}
        track["id"] = self.model.item(row, 0).text()
        track["number"] = self.model.item(row, 1).text()
        track["title"] = self.model.item(row, 2).text()
        track["artist"] = self.model.item(row, 3).text()
        track["album"] = self.model.item(row, 4).text()
        track["duration"] = self.model.item(row, 5).text()
        
        return track

    def selectedRows(self):
        rows = {}
        for index in self.selectedIndexes():
            rows[index.row()] = 1
        return rows.keys()
        
    def onDoubleClick(self, index):
        track = self.trackByRow(index.row())
        
        self.emit(SIGNAL("trackActivated(PyQt_PyObject)"), track)
 
    def keyPressEvent(self, event):
        super(TrackListView, self).keyPressEvent(event)
        if event.key() == Qt.Key_Delete:
            self.emit(SIGNAL("deleteRequested()"))
        if event.key() == Qt.Key_Return:
            rows = self.selectedRows()
            if len(rows) > 0:
                self.emit(SIGNAL("trackActivated(PyQt_PyObject)"), self.trackByRow(rows[0]))
        
        
        
class PlayQueueTab(QWidget):
    def __init__(self, parent):
        super(PlayQueueTab, self).__init__(parent)
        
        self.mainLayout = QVBoxLayout(self)
        self.queue = TrackListView(self)
        
        self.queue.setDragEnabled(True)
        self.queue.setDragDropMode(QTreeView.DragDrop)
        self.queue.setSelectionMode(QTreeView.ExtendedSelection)
        
        self.mainLayout.addWidget(self.queue)
        
        self.setLayout(self.mainLayout)
        
        self.connect(self.queue, SIGNAL("trackActivated(PyQt_PyObject)"),
                               self.onActivated)
                               
        self.connect(self.queue, SIGNAL("deleteRequested()"),
                               self.onDelete)
    
    def addTrack(self, track):
        self.queue.addTrack(track)
        if qmdc.trackId == 0:
            qmdc.openTrack(int(track.get("id")))
    
    def prevTrack(self, trackid):
        for i in range(0, self.queue.model.rowCount()):
            if int(self.queue.model.item(i, 0).text()) == trackid:
                if i - 1 >= 0:
                    return int(self.queue.model.item(i - 1, 0).text())
                else: return 0
        if self.queue.model.rowCount() > 0:
            return int(self.queue.model.item(self.queue.model.rowCount() - 1, 0).text())
        return 0
    
    def nextTrack(self, trackid):
        for i in range(0, self.queue.model.rowCount()):
            if int(self.queue.model.item(i, 0).text()) == trackid:
                if i + 1 < self.queue.model.rowCount():
                    return int(self.queue.model.item(i + 1, 0).text())
                else: return 0
        if self.queue.model.rowCount() > 0:
            return int(self.queue.model.item(0, 0).text())
        return 
    
    def onActivated(self, row):
        qmdc.openTrack(int(row["id"]))
        
    def onDelete(self):
        diff = 0
        for row in self.queue.selectedRows():
            self.queue.model.takeRow(row - diff)
            diff = diff + 1
      
class SearchTab(QWidget):
    def __init__(self, parent):
        super(SearchTab, self).__init__(parent)

        self.mainLayout = QVBoxLayout(self)
        
        self.searchBar = QHBoxLayout()
        
        self.searchEdit = QLineEdit(self)
        self.connect(self.searchEdit, SIGNAL("returnPressed()"), self.search)
        self.searchButton = QPushButton("Search", self)
        self.connect(self.searchButton, SIGNAL("clicked()"), self.search)
        
        self.searchBar.addWidget(self.searchEdit)
        self.searchBar.addWidget(self.searchButton)
        
        self.mainLayout.addLayout(self.searchBar)
        
        self.results = TrackListView(self)
        self.results.setSelectionMode(QTreeView.ExtendedSelection)
        self.results.setDragDropMode(QTreeView.DragOnly)
        self.mainLayout.addWidget(self.results)
        
    def search(self):
        self.results.model.setRowCount(0)
        
        results = qmdc.search(self.searchEdit.text())
        for result in results:
            self.results.addTrack(result)

        self.results.sortByColumn(1, Qt.AscendingOrder)
        self.results.sortByColumn(4, Qt.AscendingOrder)
        


class TopBar(QWidget):
    def __init__(self, parent, qmdc):
        super(TopBar, self).__init__(parent)
        
        self.hlayout = QHBoxLayout(self)
        
        self.nowPlaying = QLabel("<b>Not playing</b>")
        
        self.positionL = QLabel("0:00")
        self.position = QSlider(Qt.Horizontal, self)
        self.position.setMaximum(100)
        self.durationL = QLabel("0:00")
        
        self.prevB = QPushButton("Prev")
        self.prevB.setFlat(True)
        self.stopB = QPushButton("Stop")
        self.stopB.setFlat(True)
        self.playB = QPushButton("Play")
        self.playB.setFlat(True)
        self.nextB = QPushButton("Next")
        self.nextB.setFlat(True)
        
        self.hlayout.addWidget(self.nowPlaying, 0, Qt.AlignLeft)
        self.hlayout.addSpacing(25)
        self.hlayout.addWidget(self.positionL, 0, Qt.AlignRight)
        self.hlayout.addWidget(self.position, 1)
        self.hlayout.addWidget(self.durationL, 0, Qt.AlignLeft)
        self.hlayout.addSpacing(25)
        self.hlayout.addWidget(self.prevB, 0, Qt.AlignRight)
        self.hlayout.addWidget(self.stopB, 0, Qt.AlignRight)
        self.hlayout.addWidget(self.playB, 0, Qt.AlignRight)
        self.hlayout.addWidget(self.nextB, 0, Qt.AlignRight)
        
        self.sliderMoving = False
        self.connect(self.position, SIGNAL("sliderPressed()"), self.onSliderPressed)
        self.connect(self.position, SIGNAL("sliderReleased()"), self.onSliderReleased)
        
        self.connect(self.prevB, SIGNAL("clicked()"), qmdc.prevTrack)
        self.connect(self.stopB, SIGNAL("clicked()"), qmdc.stopTrack)
        self.connect(self.playB, SIGNAL("clicked()"), qmdc.togglePause)
        self.connect(self.nextB, SIGNAL("clicked()"), qmdc.nextTrack)
        
        self.connect(qmdc, SIGNAL("trackOpened()"), self.trackChanged)
        self.connect(qmdc, SIGNAL("positionChanged(int)"), self.positionChanged)
        self.connect(qmdc, SIGNAL("trackFinished()"), self.trackFinished)
    
    def onSliderPressed(self):
        self.sliderMoving = True
    
    def onSliderReleased(self):
        self.sliderMoving = False
        qmdc.seek(int(self.position.value()))
    
    def trackChanged(self):
        self.nowPlaying.setText(u"<b>{}</b><br/>by <b>{}</b><br/>on <b>{}</b>"
            .format(qmdc.trackTitle, qmdc.trackArtist, qmdc.trackAlbum))
        self.durationL.setText(
            u"{}:{:02d}".format(int(math.floor(qmdc.trackDuration / 60)),
                           qmdc.trackDuration % 60))
        self.position.setMaximum(qmdc.trackDuration)

    def positionChanged(self, npos):
        if self.sliderMoving:
            return
        self.positionL.setText(
            u"{}:{:02d}".format(int(math.floor(npos / 60)), npos % 60))
        self.position.setSliderPosition(npos)
        
    def trackFinished(self):
        self.nowPlaying.setText(u"<b>Not playing</b>")


class MainView(QWidget):
    def __init__(self, parent):
        super(MainView, self).__init__(parent)
        
        self.vlayout = QVBoxLayout(self)
        
        self.topBar = TopBar(self, parent)
        
        self.vlayout.addWidget(self.topBar)
        
        #self.hlayout = QHBoxLayout(self)
        
        #self.tabs = QTabWidget(self)
        self.splitter = QSplitter(self)
        self.search = SearchTab(self.splitter)
        #self.splitter.setStretchFactor(0,1)
        self.playQueue = PlayQueueTab(self.splitter)
        
        self.playQueue.queue.connect(self.search.results, SIGNAL("trackActivated(PyQt_PyObject)"),
                               self.playQueue.addTrack)
                               
        self.connect(self.playQueue.queue, SIGNAL("dropAction(QWidget, int)"),
                               self.onPlayQueueDrop)
        
        self.vlayout.addWidget(self.splitter, 1)
        #self.tabs.insertTab(0, self.nowPlaying, "Now playing")
        #self.tabs.insertTab(1, QWidget(self), "Playlist")
        #self.tabs.insertTab(1, self.playQueue, "Play queue")
        #self.tabs.insertTab(2, self.search, "Search")
        #self.tabs.insertTab(3, QWidget(self), "musicd")
        
        #self.vlayout.addWidget(self.tabs)
        
    def onPlayQueueDrop(self, source, dst):
        if source == self.search.results:
            for row in source.selectedRows():
                self.playQueue.addTrack(source.trackByRow(row))
                

class ConnectDialog(QFrame):
    def __init__(self, parent):
        super(ConnectDialog, self).__init__(parent)
        
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(25,25,25,25)
        self.mainLayout.setSizeConstraint(QLayout.SetFixedSize)
        self.mainLayout.setAlignment(Qt.AlignVCenter)
        
        self.mainLayout.addWidget(QLabel("<b>Connect</b>"))
        self.mainLayout.setStretch(0, 0)
        
        
        self.form = QFormLayout()
        
        self.hostEdit = QLineEdit(self)
        self.hostEdit.setText("127.0.0.1")
        
        self.portBox = QSpinBox(self)
        self.portBox.setRange(1, 65536)
        self.portBox.setValue(6800)
        
        self.userEdit = QLineEdit(self)
        self.userEdit.setText("")
        
        self.passEdit = QLineEdit(self)
        self.passEdit.setText("")
        self.passEdit.setEchoMode(QLineEdit.Password)
        
        
        self.form.addRow("Host:", self.hostEdit)
        self.form.addRow("Port:", self.portBox)
        
        self.form.addRow("User:", self.userEdit)
        self.form.addRow("Password:", self.passEdit)
        
        self.mainLayout.addLayout(self.form)
        
        
        self.connectButton = QPushButton("Connect", self)
        self.connect(self.connectButton, SIGNAL("clicked()"), self.openConnection)
        self.connectButton.setSizePolicy(QSizePolicy(QSizePolicy.Fixed,
                                         QSizePolicy.Fixed))
        
        self.mainLayout.addWidget(self.connectButton, 0, Qt.AlignRight)
        
    def openConnection(self):
        qmdc.openConnection(self.hostEdit.text(), self.portBox.value(),
                             self.userEdit.text(), self.passEdit.text())

                             


class DbusObject(dbus.service.Object):

    @dbus.service.method("org.musicd.qmdc", in_signature='', out_signature='')
    def Next(self):
        qmdc.nextTrack()

    @dbus.service.method("org.musicd.qmdc", in_signature='', out_signature='')
    def Prev(self):
        qmdc.prevTrack()

    @dbus.service.method("org.musicd.qmdc", in_signature='', out_signature='')
    def Pause(self):
        qmdc.togglePause()
        
    @dbus.service.method("org.musicd.qmdc", in_signature='', out_signature='')
    def Stop(self):
        qmdc.stopTrack()


class QMdc(QMainWindow):
    
    def __init__(self):
        super(QMdc, self).__init__()
        
        self.session_bus = dbus.SessionBus()
        self.service_name = dbus.service.BusName("org.musicd.qmdc", self.session_bus)
        self.dbus_object = DbusObject(self.session_bus, '/qmdc')

        self.initUI()
        
        self.trackPosition = 0
        self.posTimer = QTimer()
        self.posTimer.setInterval(1000)
        self.connect(self.posTimer, SIGNAL("timeout()"), self.onPositionTimer)
        
        self.trackId = 0
        self.trackDuration = 0
        
        
    def initUI(self):               
        
        nextAction = QAction(self)
        nextAction.setShortcuts(QKeySequence.Open)
        nextAction.setShortcutContext(Qt.ApplicationShortcut)
        #nextAction.triggered.connect()
        
        exitAction = QAction(QIcon('exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(qApp.quit)
        
        self.statusBar()

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&Qmdc')
        fileMenu.addAction(exitAction)
        
        fileMenu.addAction(nextAction)

        
        self.mainView = MainView(self)
        self.mainView.hide()
        
        self.setCentralWidget(ConnectDialog(self))
        
        self.setGeometry(300, 300, 300, 200)
        self.setWindowTitle('QMdc')
        self.show()
        
    def openConnection(self, host, port, user, passw):
        print "Connect to {}:{}.".format(host, port)
        try:
            self.connection = Connection(host, port)
            self.connection.auth(user, passw)
        except socket.error as e:
            QMessageBox.critical(self, "Error", e.__str__())
            return
        except MdError as e:
            QMessageBox.critical(self, "Error", "Server error: {}".format(e.__str__()))
            return
        
        self.statusBar().showMessage("Connected.", 5000)
        self.setCentralWidget(self.mainView)
        self.mainView.show()
        
    def search(self, string):
        print u"Search '{}'".format(string)
        try:
            return self.connection.search(string)
        except MdError as e:
            QMessageBox.critical(self, "Error", "Server error: {}".format(e.__str__()))
            raise

    def openTrack(self, trackid):
        result = self.connection.open(trackid)
        if not "extradata" in result:
            result["extradata"] = b""
            
        mdc.open_sink(codec=result["codec"], samplerate=int(result["samplerate"]),
                      channels=int(result["channels"]),
                      bitspersample=int(result["bitspersample"]),
                      extradata=result["extradata"])

        self.posTimer.start()
        
        self.trackId = trackid
        
        self.trackPosition = 0
        self.trackDuration = 0
        self.trackTitle = ""
        self.trackArtist = ""
        self.trackAlbum = ""
        if "title" in result:
            self.trackTitle = result["title"]
        if "artist" in result:
            self.trackArtist = result["artist"]
        if "album" in result:
            self.trackAlbum = result["album"]
        if "duration" in result:
            self.trackDuration = int(result.get("duration"))

        self.emit(SIGNAL("trackOpened()"))
        self.emit(SIGNAL("positionChanged(int)"), 0)

    def seek(self, position):
        if self.trackId > 0:
            self.connection.seek(position)
        self.trackPosition = position
    
    def togglePause(self):
        mdc.toggle_pause()
        if self.posTimer.isActive():
            self.posTimer.stop()
        else:
            self.posTimer.start()
    
    def prevTrack(self):
        trackid = self.mainView.playQueue.prevTrack(self.trackId)
        if trackid:
            self.openTrack(trackid)
    def nextTrack(self):
        trackid = self.mainView.playQueue.nextTrack(self.trackId)
        if trackid:
            self.openTrack(trackid)
            
    def stopTrack(self):
        if self.trackId:
            self.trackId = 0
            mdc.toggle_pause()
            self.posTimer.stop()
            self.emit(SIGNAL("trackFinished()"))
    
    def onPositionTimer(self):
        self.trackPosition = self.trackPosition + 1
        if self.trackPosition > self.trackDuration:
            self.posTimer.stop()
            self.emit(SIGNAL("trackFinished()"))
            trackid = self.mainView.playQueue.nextTrack(self.trackId)
            if trackid > 0:
                self.openTrack(trackid)
            else:
                self.stopTrack()
        else:
            self.emit(SIGNAL("positionChanged(int)"), self.trackPosition)
        


app = QApplication(["qmdc"])
dbus.mainloop.qt.DBusQtMainLoop(set_as_default=True)
qmdc = QMdc()
app.exec_()

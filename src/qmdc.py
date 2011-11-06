
class QMdc(QMainWindow):
    
    def __init__(self):
        super(QMdc, self).__init__()

    def init(self):
        self.settings = QSettings("musicd", "qmdc")
        
        if len(self.settings.value("profiles").toStringList()) == 0:
            self.settings.setValue("profiles", ["Default"])
        #if !self.settings.contains("qmdc.configured"):
            
        
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
        
        self.selector = ProfileSelector(self)
        self.selector.show()
        
        self.connect(self.selector, SIGNAL("selected(PyQt_PyObject)"), self.profileSelected)
        self.connect(self.selector, SIGNAL("canceled()"), qApp.quit)
        
        #nextAction = QAction(self)
        #nextAction.setShortcuts(QKeySequence.Open)
        #nextAction.setShortcutContext(Qt.ApplicationShortcut)
        #nextAction.triggered.connect()
        
        exitAction = QAction(QIcon('exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(qApp.quit)
        
        self.statusBar()

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&Qmdc')
        fileMenu.addAction(exitAction)
        
        #fileMenu.addAction(nextAction)

        
        self.mainView = MainView(self)
        self.setCentralWidget(self.mainView)
        
        #self.setCentralWidget(ConnectDialog(self))
        
        #self.setGeometry(300, 300, 300, 200)
        self.setWindowTitle('QMdc')
        #self.show()
    def profileSelected(self, profile):
        self.selector.hide()
        self.openConnection(profile.host, profile.port, profile.user, profile.password)

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
        self.show()
        
    def search(self, string):
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


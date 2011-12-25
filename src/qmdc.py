
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
        self.selector.setWindowModality(Qt.WindowModal)
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
        
        
        transcodingOptionsAction = QAction('&Options', self)
        transcodingOptionsAction.setStatusTip('Transcoding options')
        transcodingOptionsAction.triggered.connect(self.showTranscodingOptions)
        
        transcodingMenu = menubar.addMenu('&Transcoding')
        transcodingMenu.addAction(transcodingOptionsAction)
        
        #fileMenu.addAction(nextAction)

        
        self.mainView = MainView(self)
        self.setCentralWidget(self.mainView)
        
        #self.setCentralWidget(ConnectDialog(self))
        
        #self.setGeometry(300, 300, 300, 200)
        self.setWindowTitle('QMdc')
        self.show()

    def profileSelected(self, profile):
        if self.openConnection(profile.host, profile.port, profile.user, profile.password):
            self.selector.hide()

    def showTranscodingOptions(self):
        self.transcodingOptions.show()
        
    def transcodingChanged(self, options):
        self.connection.transcoding = options
        
    def openConnection(self, host, port, user, passw):
        try:
            self.connection = Connection(host, port)
            self.connection.auth(user, passw)
        except socket.error as e:
            QMessageBox.critical(self, "Error", e.__str__())
            return False
        except MdError as e:
            QMessageBox.critical(self, "Error", "Server error: {}".format(e.__str__()))
            return False
        
        self.statusBar().showMessage("Connected.", 5000)
        
        self.transcodingOptions = TranscodingOptions(self.connection.codecs, self)
        self.connect(self.transcodingOptions, SIGNAL("changed(PyQt_PyObject)"), self.transcodingChanged)
        
        return True
        
    def search(self, string):
        try:
            return self.connection.search(string)
        except MdError as e:
            QMessageBox.critical(self, "Error", "Server error: {}".format(e.__str__()))
            raise

    def openTrack(self, trackid):
        stream, track = self.connection.open(trackid)
        if not "extradata" in stream:
            stream["extradata"] = b""
            
        mdc.open_sink(codec=stream["codec"], samplerate=int(stream["samplerate"]),
                      channels=int(stream["channels"]),
                      bitspersample=int(stream["bitspersample"]),
                      extradata=stream["extradata"])

        self.posTimer.start()
        
        self.trackId = trackid
        
        self.trackPosition = 0
        self.trackDuration = 0
        self.trackTitle = ""
        self.trackArtist = ""
        self.trackAlbum = ""
        if "title" in track:
            self.trackTitle = track["title"]
        if "artist" in track:
            self.trackArtist = track["artist"]
        if "album" in track:
            self.trackAlbum = track["album"]
        if "duration" in track:
            self.trackDuration = int(track.get("duration"))

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


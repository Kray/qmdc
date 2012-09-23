class TopBar(QWidget):
    def __init__(self, parent, qmdc):
        super(TopBar, self).__init__(parent)
        
        self.hlayout = QHBoxLayout(self)
        
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
        
        #self.hlayout.addWidget(self.nowPlaying, 0, Qt.AlignLeft)
        #self.hlayout.addSpacing(25)
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
    
    def onSliderPressed(self):
        self.sliderMoving = True
    
    def onSliderReleased(self):
        self.sliderMoving = False
        qmdc.seek(int(self.position.value()))
    
    def trackChanged(self):
        self.position.setMaximum(qmdc.trackDuration)

    def positionChanged(self, npos):
        if self.sliderMoving:
            return
        self.positionL.setText(
            u"{}:{:02d}".format(int(math.floor(npos / 60)), npos % 60))
        self.position.setSliderPosition(npos)


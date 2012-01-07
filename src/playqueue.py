class PlayMode:
    NORMAL = 0
    FULL_RANDOM = 1
    QUEUE_RANDOM = 2

class PlayQueue(QWidget):
    def __init__(self, parent):
        super(PlayQueue, self).__init__(parent)
        
        self.mainLayout = QVBoxLayout(self)
        
        self.modeLayout = QHBoxLayout()
        self.playMode = QComboBox(self)
        self.connect(self.playMode, SIGNAL("currentIndexChanged(QString)"), self.onPlayModeChange)
        self.playMode.addItem("Normal")
        self.playMode.addItem("Full random")
        self.playMode.addItem("Queue random")
        
        self.modeLayout.addWidget(QLabel("Mode"))
        self.modeLayout.addWidget(self.playMode)
        self.modeLayout.addStretch(1)
        
        self.mainLayout.addLayout(self.modeLayout)
        
        
        self.queue = TrackListView(self)
        
        self.queue.setDragEnabled(True)
        self.queue.setDragDropMode(QTreeView.DragDrop)
        self.queue.setSelectionMode(QTreeView.ExtendedSelection)
        
        self.mainLayout.addWidget(self.queue)
        
        self.connect(self.queue, SIGNAL("trackActivated(PyQt_PyObject)"),
                               self.onActivated)
                               
        self.connect(self.queue, SIGNAL("deleteRequested()"),
                               self.onDelete)
    
    def addTrack(self, track):
        self.queue.addTrack(track)
        if qmdc.trackId == 0:
            qmdc.openTrack(int(track.get("id")))
    def removeTrack(self, trackid):
        for i in range(0, self.queue.model.rowCount()):
            if int(self.queue.model.item(i, 0).text()) == trackid:
                self.queue.model.takeRow(i)
                return

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
    
    def popFront(self):
        if self.queue.model.rowCount() == 0:
            return 0
        return int(self.queue.model.takeRow(0)[0].text())

    def random(self):
        if self.queue.model.rowCount() == 0:
            return 0
        return int(self.queue.model.item(random.randint(0, self.queue.model.rowCount()) - 1, 0).text())
    
    def onActivated(self, row):
        qmdc.openTrack(int(row["id"]))
        
    def onDelete(self):
        diff = 0
        for row in self.queue.selectedRows():
            self.queue.model.takeRow(row - diff)
            diff = diff + 1
    def onPlayModeChange(self, mode):
        if mode == "Normal":
            qmdc.playMode = PlayMode.NORMAL
        elif mode == "Full random":
            qmdc.playMode = PlayMode.FULL_RANDOM
        elif mode == "Queue random":
            qmdc.playMode = PlayMode.QUEUE_RANDOM

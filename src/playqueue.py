class PlayQueue(QWidget):
    def __init__(self, parent):
        super(PlayQueue, self).__init__(parent)
        
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

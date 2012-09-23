class MainView(QSplitter):
    def __init__(self, parent):
        super(MainView, self).__init__(parent)
        
        self.trackInfo = TrackInfo(self)
        
        self.mainBox = QWidget(self)
        self.mainLayout = QVBoxLayout(self.mainBox)
        
        self.setStretchFactor(1, 1)
        
        self.topBar = TopBar(self.mainBox, parent)
        self.mainLayout.addWidget(self.topBar)
        
        self.splitter = QSplitter(self.mainBox)
        self.mainLayout.addWidget(self.splitter, 1)
        
        self.search = Search(self.splitter)
        
        self.playQueue = PlayQueue(self.splitter)
        self.playQueue.queue.connect(self.search.results, SIGNAL("trackActivated(PyQt_PyObject)"),
                                     self.playQueue.addTrack)
                               
        self.connect(self.playQueue.queue, SIGNAL("dropAction(QWidget, int)"),
                     self.onPlayQueueDrop)
        
    def onPlayQueueDrop(self, source, dst):
        if source == self.search.results:
            for row in source.selectedRows():
                self.playQueue.addTrack(source.trackByRow(row))

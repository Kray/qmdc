class MainView(QWidget):
    def __init__(self, parent):
        super(MainView, self).__init__(parent)
        
        self.vlayout = QVBoxLayout(self)
        
        self.topBar = TopBar(self, parent)
        
        self.vlayout.addWidget(self.topBar)
        
        #self.hlayout = QHBoxLayout(self)
        
        #self.tabs = QTabWidget(self)
        self.splitter = QSplitter(self)
        self.search = Search(self.splitter)
        #self.splitter.setStretchFactor(0,1)
        self.playQueue = PlayQueue(self.splitter)
        
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

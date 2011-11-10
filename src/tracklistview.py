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
        
        if "track" in track:
            try:
                if int(track["track"]) > 0:
                    line[1] = QStandardItem("{:02d}".format(int(track["track"])))
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
        

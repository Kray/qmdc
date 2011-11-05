class Search(QWidget):
    def __init__(self, parent):
        super(Search, self).__init__(parent)

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

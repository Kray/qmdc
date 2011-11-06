
class ProfileSelector(QDialog):
    def __init__(self, parent):
        super(ProfileSelector, self).__init__(parent)
        
        self.setWindowTitle("Select profile")
        
        self.mainLayout = QVBoxLayout(self)
        
        self.profileEdit = ProfileEdit(self)
        
        self.selectorLayout = QHBoxLayout()
        
        self.selectorBox = QComboBox(self)
        self.selectorBox.setEditable(True)
        self.connect(self.selectorBox, SIGNAL("currentIndexChanged(QString)"), self.onSelectionChange)
        
        for name in qmdc.settings.value("profiles").toStringList():
            self.selectorBox.addItem(name)

        self.selectorLayout.addWidget(self.selectorBox, 1)
            
        self.newButton = QPushButton("New")
        self.connect(self.newButton, SIGNAL("clicked()"), self.onNew)
        self.selectorLayout.addWidget(self.newButton)
        
        self.deleteButton = QPushButton("Del")
        self.connect(self.deleteButton, SIGNAL("clicked()"), self.onDelete)
        self.selectorLayout.addWidget(self.deleteButton)
        
        self.mainLayout.addLayout(self.selectorLayout)
        
        
        self.profileEdit.setProfile(self.selectorBox.currentText())
        
        self.mainLayout.addWidget(self.profileEdit)
        
        self.ctrlBox = QHBoxLayout()
        
        self.okButton = QPushButton("Ok")
        self.connect(self.okButton, SIGNAL("clicked()"), self.onSelect)
        self.ctrlBox.addWidget(self.okButton)
        
        self.cancelButton = QPushButton("Cancel")
        self.ctrlBox.addWidget(self.cancelButton)
        
        self.ctrlBox.addStretch(1)
        
        self.mainLayout.addLayout(self.ctrlBox)

    def newProfile(self, name):
        profiles = qmdc.settings.value("profiles").toStringList()
        if profiles.contains(name):
            return False

        self.selectorBox.addItem(name)
        profiles.append(name)
        qmdc.settings.setValue("profiles", profiles)
        return True
        
    """def renameProfile(self, profile):
        self.profileEdit.saveProfile(profile)
        profiles = qmdc.settings.value("profiles").toStringList()
        profiles[self.selectorBox.currentIndex()] = profile
        qmdc.settings.setValue("profiles", profiles)
    """
    def onSelectionChange(self, name):
        self.profileEdit.setProfile(name)
        
    
    def onSelect(self):
        profiles = qmdc.settings.value("profiles").toStringList()
        if profiles[self.selectorBox.currentIndex()] != self.selectorBox.currentText():
            qmdc.settings.remove("profile_" + profiles[self.selectorBox.currentIndex()])
            profiles[self.selectorBox.currentIndex()] = self.selectorBox.currentText()
            qmdc.settings.setValue("profiles", profiles)
            
        self.profileEdit.saveProfile(self.selectorBox.currentText())
        self.profileEdit.setProfile(self.selectorBox.currentText())

        self.emit(SIGNAL("selected(PyQt_PyObject)"), self.profileEdit.profile())

    def onNew(self):
        if self.newProfile("New profile"):
            return
        i = 1
        while not self.newProfile("New profile " + str(i)):
            i = i + 1
            
    def onDelete(self):
        profiles = qmdc.settings.value("profiles").toStringList()
        profiles.removeAll(self.selectorBox.currentText())
        
        qmdc.settings.setValue("profiles", profiles)
        
        if len(profiles) == 0:
            qmdc.settings.setValue("profiles", ["Default"])
        
        qmdc.settings.remove("profile_" + self.selectorBox.currentText())
        
        self.selectorBox.clear()
        for name in qmdc.settings.value("profiles").toStringList():
            self.selectorBox.addItem(name)
        
        
        """        name, got = QInputDialog.getText(self, "New profile", "Profile name")
        if got:
            if qmdc.settings.value("profiles").toStringList().contains(name):
                QMessageBox.critical(self, "Profile exists", "Profile with this name exists.")
                self.onNew()
            self.selectorBox.addItem(name)
        """            

        """
        self.listLayout = QHBoxLayout()
        
        self.listModel = QStringListModel()
        self.listView = QListView(self)
        self.listView.setModel(self.listModel)
        
        self.listModel.setStringList(qmdc.settings.value("profiles").toStringList())
        
        self.listLayout.addWidget(self.listView)
        
        
        self.listButtonLayout = QVBoxLayout()
        
        self.newButton = QPushButton("New profile")
        self.listButtonLayout.addWidget(self.newButton)
        
        self.deleteButton = QPushButton("Delete")
        self.listButtonLayout.addWidget(self.deleteButton)
        
        self.listButtonLayout.addStretch(1)
        
        self.listLayout.addLayout(self.listButtonLayout)
        
        self.mainLayout.addLayout(self.listLayout)
        """

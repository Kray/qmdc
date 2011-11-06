class Profile:
    def __init__(self, name):
        profile = "profile_" + name
        
        self.name = name
        
        self.host = qmdc.settings.value(profile + "/host").toString()
        self.port = qmdc.settings.value(profile + "/port").toInt()[0]
        self.user = qmdc.settings.value(profile + "/user").toString()

class ProfileEdit(QFrame):
    def __init__(self, parent):
        super(ProfileEdit, self).__init__(parent)
        
        self.form = QFormLayout(self)
        
        #self.typeSelect = QComboBox()
        #self.typeSelect.addItems(["Connect", "Embedded"])
        
        self.hostEdit = QLineEdit(self)
        self.hostEdit.setText("127.0.0.1")
        
        self.portBox = QSpinBox(self)
        self.portBox.setRange(1, 65536)
        self.portBox.setValue(6800)
        
        self.userEdit = QLineEdit(self)
        
        self.passEdit = QLineEdit(self)
        self.passEdit.setEchoMode(QLineEdit.Password)
        
        
        #self.directorySelect = QPushButton("")
        
        #self.form.addRow("Music dir:", self.directorySelect)
        #self.connect(self.directorySelect, SIGNAL("clicked()"), self.onChangeDirectory)
        
        #self.form.addRow("Type:", self.typeSelect)
        
        self.form.addRow("Host:", self.hostEdit)
        self.form.addRow("Port:", self.portBox)
        
        self.form.addRow("User:", self.userEdit)
        self.form.addRow("Password:", self.passEdit)

    def profile(self):
        profile = Profile(self.name)
        profile.password = self.passEdit.text()
        return profile
    
    def setProfile(self, name):
        self.name = name
        profile = "profile_" + name
      
        self.hostEdit.setText("127.0.0.1")
        self.portBox.setValue(6800)
        
        if qmdc.settings.contains(profile + "/host"):
            self.hostEdit.setText(qmdc.settings.value(profile + "/host").toString())
            
        if qmdc.settings.contains(profile + "/port"):
            self.portBox.setValue(qmdc.settings.value(profile + "/port").toUInt()[0])
        
        self.userEdit.setText(qmdc.settings.value(profile + "/user").toString())
    
    def saveProfile(self, name):
        profile = "profile_" + name
        qmdc.settings.setValue(profile + "/host", self.hostEdit.text())
        qmdc.settings.setValue(profile + "/port", self.portBox.value())
        qmdc.settings.setValue(profile + "/user", self.userEdit.text())
        
    def onChangeDirectory(self):
        pass
        #self.directorySelect.setText(QFileDialog.getExistingDirectory())
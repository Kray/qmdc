class ConnectDialog(QFrame):
    def __init__(self, parent):
        super(ConnectDialog, self).__init__(parent)
        
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(25,25,25,25)
        self.mainLayout.setSizeConstraint(QLayout.SetFixedSize)
        self.mainLayout.setAlignment(Qt.AlignVCenter)
        
        self.mainLayout.addWidget(QLabel("<b>Connect</b>"))
        self.mainLayout.setStretch(0, 0)
        
        
        self.form = QFormLayout()
        
        self.hostEdit = QLineEdit(self)
        self.hostEdit.setText("127.0.0.1")
        
        self.portBox = QSpinBox(self)
        self.portBox.setRange(1, 65536)
        self.portBox.setValue(6800)
        
        self.userEdit = QLineEdit(self)
        self.userEdit.setText("")
        
        self.passEdit = QLineEdit(self)
        self.passEdit.setText("")
        self.passEdit.setEchoMode(QLineEdit.Password)
        
        
        self.form.addRow("Host:", self.hostEdit)
        self.form.addRow("Port:", self.portBox)
        
        self.form.addRow("User:", self.userEdit)
        self.form.addRow("Password:", self.passEdit)
        
        self.mainLayout.addLayout(self.form)
        
        
        self.connectButton = QPushButton("Connect", self)
        self.connect(self.connectButton, SIGNAL("clicked()"), self.openConnection)
        self.connectButton.setSizePolicy(QSizePolicy(QSizePolicy.Fixed,
                                         QSizePolicy.Fixed))
        
        self.mainLayout.addWidget(self.connectButton, 0, Qt.AlignRight)
        
    def openConnection(self):
        qmdc.openConnection(self.hostEdit.text(), self.portBox.value(),
                             self.userEdit.text(), self.passEdit.text())

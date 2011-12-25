class TranscodingOptions(QDialog):
    def __init__(self, codecs, parent):
        super(TranscodingOptions, self).__init__(parent)
        
        self.setWindowTitle("Transcoding options")
        
        self.layout = QVBoxLayout(self)
        
        self.codecs = codecs
        
        self.enable = False
        self.codec = ""
        self.bitrate = 128
        
        if len(self.codecs) == 0:
            self.layout.addWidget(QLabel("Transcoding not supported by server."))
        else:
            self.enableBox = QCheckBox("Enable Transcoding", self)
            self.layout.addWidget(self.enableBox)
            self.optionsForm = QFormLayout()
            
            self.codecBox = QComboBox(self)
            self.codecBox.addItems(self.codecs)
            
            self.bitrateBox = QSpinBox(self)
            self.bitrateBox.setRange(64, 320)
            self.bitrateBox.setValue(128)
            
            self.optionsForm.addRow("Codec:", self.codecBox)
            self.optionsForm.addRow("Bitrate (kbps):", self.bitrateBox)
            
            self.layout.addLayout(self.optionsForm)

        self.ctrlBox = QHBoxLayout()
        
        self.okButton = QPushButton("Ok")
        self.okButton.setDefault(True)
        self.connect(self.okButton, SIGNAL("clicked()"), self.onSelect)
        self.ctrlBox.addWidget(self.okButton)
        
        self.cancelButton = QPushButton("Cancel")
        self.connect(self.cancelButton, SIGNAL("clicked()"), self.onCancel)
        self.ctrlBox.addWidget(self.cancelButton)
        
        self.ctrlBox.addStretch(1)
        
        self.layout.addLayout(self.ctrlBox)
        
    def onSelect(self):
        if len(self.codecs) == 0:
            self.accept()
            return
            
        options = {}
        if self.enableBox.checkState() == Qt.Checked:
            options["codec"] = self.codecBox.currentText()
            options["bitrate"] = self.bitrateBox.value()
        self.emit(SIGNAL("changed(PyQt_PyObject)"), options)
        
        self.accept()
        
    def onCancel(self):
        self.reject()


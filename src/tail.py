

app = QApplication(["qmdc"])
dbus.mainloop.qt.DBusQtMainLoop(set_as_default=True)
qmdc = QMdc()
app.exec_()


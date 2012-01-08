
pynotify.init("qmdc")
app = QApplication(["qmdc"])
dbus.mainloop.qt.DBusQtMainLoop(set_as_default=True)
qmdc = QMdc()
qmdc.init()
app.exec_()


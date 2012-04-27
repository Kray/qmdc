
def handle_exception(exc_type, exc_value, exc_traceback):
    text = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    QMessageBox.critical(None, "qmdc error", "Unhandled exception:\n{}\nqmdc terminates".format(text))
    print text
    sys.exit(-1)

sys.excepthook = handle_exception

if not no_notify:
    pynotify.init("qmdc")

app = QApplication(["qmdc"])

if not no_dbus:
    dbus.mainloop.qt.DBusQtMainLoop(set_as_default=True)

qmdc = QMdc()
qmdc.init()
app.exec_()
def parseDict(line):
    result = {}
    next_escaped = False
    
    key = ""
    tmp = ""

    for c in line:
        if next_escaped:
            if c == ' ':
                tmp += ' '
            elif c == '\\':
                tmp += '\\'
            elif c == '=':
                tmp += '='
            else: pass # Unknown escape sequence, ignore
            next_escaped = False
            continue
        if c == '\\':
            next_escaped = True
        elif c == '=' and len(key) == 0:
            key = tmp
            tmp = ""
        elif c == ' ':
            if len(key) == 0:
                key = "id"
                
            result[key] = tmp
            key = ""
            tmp = ""
        else:
            tmp += c
    if len(key) > 0 or len(tmp) > 0:
        result[key] = tmp

    return result
    
def escape(src):
    result = ""
    
    for c in src:
        if c == " ":
            result += "\\ "
        elif c == "\\":
            result += "\\\\"
        elif c == "=":
            result += "\\="
        else:
            result += c
    return result


class Connection(socket.socket):
    def __init__(self, host, port):
        socket.socket.__init__(self, socket.AF_INET, socket.SOCK_STREAM)
        
        self.mutex = threading.RLock()
        self.running = False
        
        self.buffer = b''
        self.queue = []
        
        self.connect((host, port))
        self.send(b"hello 1 qmdc\n")
        line = self.receive(["hello"])
    
    def auth(self, user, passw):
        with self.mutex:
            self.send(u"auth {} {}\n".format(user, passw).encode("utf-8"))
            line = self.receive(["auth"])
    def search(self, string):
        with self.mutex:
            self.send(u"search {}\n".format(escape(string)).encode("utf-8"))

            result = []
            while 1:
                msg = self.receive(["track", "search"])
                if msg[0] == "search":
                    break
                if msg[0] != 'track':
                    print u"error: not track '{}'".format(msg)
                track = parseDict(msg[1])
                result.append(track)
            return result
    def open(self, trackid):
        if self.running:
            self.running = False
            self.thread.join()
            
        with self.mutex:
            self.send("open {}\n".format(trackid).encode("utf-8"))
            msg = self.receive(["open"])
            
            result = parseDict(msg[1])
            if len(msg) > 2:
                result["extradata"] = msg[2]
            
            self.queue = []
            
            self.thread = threading.Thread(target=self.process)
            self.thread.start()
            return result
    
    def seek(self, position):
        with self.mutex:
            self.send("seek {}\n".format(position).encode("utf-8"))
            msg = self.receive(["seek"])
            
            self.queue = []
            mdc.flush()
            
            if self.running == False:
                self.thread = threading.Thread(target=self.process)
                self.thread.start()
            
    
    def process(self):
        self.running = True
        while self.running:
            msg = self.receive(["packet"])
            if len(msg[2]) == 0:
                self.running = False
                return
            mdc.packet(msg[2])
    
    def receive(self, methods):
        with self.mutex:
            for item in self.queue:
                if item[0] in methods:
                    del self.queue[0]
                    return item
            while 1:
                msg = self._receive_next()
                if msg[0] == "error":
                    raise MdError(msg[1])
                if msg[0] in methods:
                    return msg
                
    def _receive_next(self):
        with self.mutex:
            lines = self.buffer.split(b'\n')
            if len(self.buffer) == 0 or (len(lines) == 1 and self.buffer[-1] != b'\n'):
                data = self.recv(1024)
                self.buffer += data
                if len(data) == 0:
                    QMessageBox.critical(qmdc, "Error", "Connection terminated.")
                    raise MdError("Connection terminated.")
                return self._receive_next()
            
            line = lines[0].decode("utf-8", errors="replace")
            lines.pop(0)
            self.buffer = b"\n".join(lines)
            msg = []
            split = line.split(" ")
            msg.append(split[0])
            dict = parseDict(line)
            if len(split) > 1:
                msg.append(" ".join(split[1:]))
                if "payload" in dict:
                    msg.append(self._receive_bin(int(dict["payload"])))
            return msg
                
    def _receive_bin(self, size):
        with self.mutex:
            if len(self.buffer) < size:
                data = self.recv(size - len(self.buffer))
                if len(data) == 0:
                    QMessageBox.critical(qmdc, "Error", "Connection terminated.")
                    raise MdError("Connection terminated.")
                self.buffer += data
                return self._receive_bin(size)
            result = self.buffer[:size]
            self.buffer = self.buffer[size:]
            return result

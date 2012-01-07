
def parseDict(line):
    result = {}
    
    key = ""
    tmp = ""

    for c in line:
        if c == '=' and len(key) == 0:
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

class Connection(socket.socket):
    def __init__(self, host, port):
        socket.socket.__init__(self, socket.AF_INET, socket.SOCK_STREAM)
        
        self.mutex = threading.RLock()
        self.running = False
        
        self.buffer = b''
        self.queue = []
        
        self.connect((host, port))

        msg = self.receive(["musicd"])
        if "codecs" in msg[1]:
            self.codecs = msg[1]["codecs"].split(",")
        else:
            self.codecs = []
            
        self.transcoding = {}
    
    def auth(self, user, passw):
        with self.mutex:
            self.send(u"auth\nuser={}\npassword={}\n\n".format(user, passw).encode("utf-8"))
            line = self.receive(["auth"])

    def search(self, string):
        with self.mutex:
            self.send(u"search\nquery={}\n\n".format(string).encode("utf-8"))
            result = []
            while 1:
                msg = self.receive(["track", "search"])
                if msg[0] == "search":
                    break
                result.append(msg[1])
            return result
            
    def randomid(self):
        with self.mutex:
            self.send(u"randomid\n\n".encode("utf-8"))
            msg = self.receive(["randomid"])
            return int(msg[1].get("id"))
    def open(self, trackid):
        if self.running:
            self.running = False
            self.thread.join()
            
        with self.mutex:
            if self.transcoding.get("codec") in self.codecs:
                self.send("open\nid={}\ncodec={}\nbitrate={}\n\n".format(trackid, self.transcoding.get("codec"), self.transcoding.get("bitrate")).encode("utf-8"))
            else:
                self.send("open\nid={}\n\n".format(trackid).encode("utf-8"))
            
            stream = {}
            track = {}
            
            while 1:
                msg = self.receive(["track", "open"])
                if msg[0] == "open":
                    stream = msg[1]
                    break
                elif msg[0] == "track":
                    track = msg[1]
            
            self.queue = []
            
            self.thread = threading.Thread(target=self.process)
            self.thread.start()
            
            return stream, track
    
    def seek(self, position):
        with self.mutex:
            self.send("seek\nposition={}\n\n".format(position).encode("utf-8"))
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
            if len(msg[1]["payload"]) == 0:
                self.running = False
                return
            mdc.packet(msg[1]["payload"])
    
    def receive(self, methods):
        with self.mutex:
            for item in self.queue:
                if item[0] in methods:
                    del self.queue[0]
                    return item
            while 1:
                msg = self._receive_next()
                if msg[0] == "error":
                    raise MdError(msg[1].get("name"))
                if msg[0] in methods:
                    return msg
                self.queue.append(msg)
                
    def _receive_next(self):
        with self.mutex:
            msgs = self.buffer.split(b'\n\n')
            if len(self.buffer) == 0 or (len(msgs) == 1 and self.buffer[-2:] != b"\n\n"):
                data = self.recv(1024)
                self.buffer += data
                if len(data) == 0:
                    QMessageBox.critical(qmdc, "Error", "Connection terminated.")
                    raise MdError("Connection terminated.")
                return self._receive_next()
            
            msg = msgs[0].decode("utf-8", errors="replace")
            msgs.pop(0)
            self.buffer = b"\n\n".join(msgs)
            result = []
            split = msg.split("\n")
            result.append(split[0])
            split.pop(0)
            result.append({})
            for property in split:
                parts = property.split("=")
                if len(parts) == 1 or len(parts[0]) == 0:
                    continue
                if parts[0][-1] == ":":
                    result[1][parts[0][:-1]] = self._receive_bin(int(parts[1]))
                else:
                    result[1][parts[0]] = "=".join(parts[1:])

            return result
                
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


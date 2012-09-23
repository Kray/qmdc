class TrackInfo(QWidget):
    def __init__(self, parent):
        super(TrackInfo, self).__init__(parent)

        self.layout = QVBoxLayout(self)
        
        self.albumimg = QLabel(self)
        self.layout.addWidget(self.albumimg)
        
        self.nowPlaying = QLabel("<b>Not playing</b>", self)
        self.nowPlaying.setWordWrap(True)
        self.layout.addWidget(self.nowPlaying)
        
        self.lyrics = QTextEdit(self)
        self.lyrics.readOnly = True
        self.layout.addWidget(self.lyrics, 1)

        self.connect(qmdc, SIGNAL("trackOpened()"), self.trackChanged)
        self.connect(qmdc, SIGNAL("trackFinished()"), self.trackFinished)
        
        self.connect(qmdc, SIGNAL("trackAlbumImgLoaded()"), self.albumImgLoaded)

        self.connect(qmdc, SIGNAL("trackLyricsLoading()"), self.lyricsLoading)
        self.connect(qmdc, SIGNAL("trackLyricsLoaded()"), self.lyricsLoaded)
        self.connect(qmdc, SIGNAL("trackLyricsUnavailable()"), self.lyricsUnavailable)
    
    def trackChanged(self):
        self.nowPlaying.setText(u"<b>{}</b><br/>by <b>{}</b><br/>on <b>{}</b>"
          .format(qmdc.trackTitle, qmdc.trackArtist, qmdc.trackAlbum))
        self.albumimg.setPixmap(QPixmap())
        self.lyrics.setPlainText(u"")

    def trackFinished(self):
        self.nowPlaying.setText(u"<b>Not playing</b>")

    def albumImgLoaded(self):
        self.albumimg.setPixmap(QPixmap.fromImage(QImage.fromData(qmdc.trackAlbumImg)))
    
    def lyricsLoading(self):
        self.lyrics.setPlainText("Fetching lyrics...")

    def lyricsLoaded(self):
        self.lyrics.setPlainText(QString.fromUtf8(qmdc.trackLyrics))

    def lyricsUnavailable(self):
        self.lyrics.setPlainText("Lyrics unavailable")


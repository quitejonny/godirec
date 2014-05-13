import sys
import re
import glob
import id3reader
from mainwindow import *
from mutagen.easyid3 import EasyID3
from PyQt4 import QtCore, QtGui
from godiRec import Recorder

class GodiRec(QtGui.QMainWindow, Ui_GodiRec):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        Ui_GodiRec.__init__(self)
        self.rec = Recorder(channels=2) 
        self.setupUi(self)
        self.pushButton_play.clicked.connect(self.btn_play_clicked)
        self.pushButton_stop.clicked.connect(self.btn_stop_clicked)
        self.pushButton_rec.clicked.connect(self.btn_rec_clicked)
        self.pushButton_cut.clicked.connect(self.btn_cut_clicked)
        self.pushButton_save.clicked.connect(self.btn_save_clicked)
        self.pushButton_change.clicked.connect(self.btn_change_clicked)
        self.update_listTracks()
        self.cur_track = None
        
    def btn_play_clicked(self):
        if self.pushButton_play.text() == "Pause":
            self.pushButton_play.setText("Play")
            self.pushButton_rec.setText("Rec")
            self.pushButton_rec.setEnabled(False)
            self.pushButton_save.setEnabled(False)
            self.recfile.stop_recording()
        else:
            self.pushButton_play.setText("Pause")
            self.pushButton_rec.setText("Recording")
            self.pushButton_rec.setEnabled(False)
            self.recfile.start_recording()

    def btn_stop_clicked(self):
        self.pushButton_rec.setText("Rec")
        self.pushButton_rec.setEnabled(True)
        self.pushButton_play.setEnabled(True)
        self.pushButton_save.setEnabled(True)
        update_listTracks()

    def btn_rec_clicked(self):
        if self.pushButton_rec.text() != "Recording":
            self.pushButton_rec.setText("Recording")
            self.pushButton_rec.setEnabled(False)
            self.pushButton_play.setText("Pause")
            self.pushButton_save.setEnabled(False)
            #self.recfile2.start_recording()                
            self.recfile = self.rec.open()
            self.recfile = self.recfile.start_recording()

    #Erzeugt neue Datei und nimmt weiter auf
    def btn_cut_clicked(self):
        self.recfile.stop_recording()
        self.recfile.close()
        self.rec.save("track_1.mp3", ".temp/track_1.wav")
        self.recfile = self.rec.open()
        self.recfile.start_recording()
        self.update_listTracks()

    #Schreibt Tags in MP3 datei
    def btn_change_clicked(self):
        title = str(self.lineEdit_titel.text())
        artist = str(self.lineEdit_artist.text())
        album = str(self.lineEdit_album.text())
        genre = str(self.lineEdit_genre.text())
        #kommentar wird von ID3 nicht unterstuetzt
        #comments = str(self.lineEdit_kommentar.text())
        #TODO: add getdate
        audio = EasyID3(self.cur_track)
        audio["artist"] = artist
        audio["title"] = title
        audio["album"] = album
        audio["genre"] = genre
        #audio["comments"] = comments
        audio.save()
        print "Taggs gespeichert"

    def btn_save_clicked(self):
        #TODO: Speichere in Ordner (defult [Datum]-Godi), pfad waehlbar
        self.update_listTracks()

    #updatet die Listenansicht
    def update_listTracks(self):
        files = glob.glob('*.mp3')
        list = self.listTracks
        model = QtGui.QStandardItemModel(list)
        for f in files:
            model.appendRow(QtGui.QStandardItem(f))
        list.setModel(model)
        list.clicked.connect(self.on_listTracks_changed)

    #Click listener auf ItemListView
    #Es zeigt die Tags des angeklickten Files an
    def on_listTracks_changed(self, index):
        self.cur_track = str(index.model().itemFromIndex(index).text())
        id3r = id3reader.Reader(self.cur_track)
        if id3r.getValue("title"):
            self.lineEdit_titel.setText(id3r.getValue("title"))
        if id3r.getValue("performer"):
            self.lineEdit_artist.setText(id3r.getValue("performer"))
        if id3r.getValue("album"):
            self.lineEdit_album.setText(id3r.getValue("album"))
        if id3r.getValue("genre"):
            self.lineEdit_genre.setText(id3r.getValue("genre"))
        if id3r.getValue("comment"):
            self.lineEdit_kommentar.setText(id3r.getValue("comment"))


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = GodiRec()
    window.show()
    sys.exit(app.exec_())

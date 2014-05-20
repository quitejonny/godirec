# -*- coding: utf-8 -*-
import sys
import os
import re
import glob
import id3reader
import datetime
import threading
from mainwindow import *
from dialog import Ui_Dialog
from mutagen.easyid3 import EasyID3
from PyQt4 import QtCore, QtGui, uic
from godiRec import Recorder

#Dialog soll Workspace Phat abfragen und Projekt Namen, diese erstellen

#und an das Programm zurückgeben.
class PathDialog(QtGui.QDialog):

    def __init__(self):
        QtGui.QDialog.__init__(self)
        ui_file = os.path.join("ui", "dialog.ui")
        uic.loadUi(ui_file, self)
        print("PathDialog init")


class GodiRec(QtGui.QMainWindow):

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        ui_file = os.path.join("ui", "godi_rec.ui")
        uic.loadUi(ui_file, self)
        self.rec = Recorder(channels=2) 
        self.pushButton_play.clicked.connect(self.btn_play_clicked)
        self.pushButton_stop.clicked.connect(self.btn_stop_clicked)
        self.pushButton_rec.clicked.connect(self.btn_rec_clicked)
        self.pushButton_cut.clicked.connect(self.btn_cut_clicked)
        self.pushButton_save.clicked.connect(self.btn_save_clicked)
        self.pushButton_change.clicked.connect(self.btn_change_clicked)
        self.actionExit.triggered.connect(self.exit)
        self.actionNeues_Projekt.triggered.connect(self.act_neues_projekt)
        self.update_listTracks()
        self.cur_track = None
        self.timer = None
        self.cur_path = ""
        
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
        self.timer.cancel()
        self.recfile.stop_recording()
        self.recfile.close()
        update_listTracks()

    def btn_rec_clicked(self):
        if self.pushButton_rec.text() != "Recording":
            self.pushButton_rec.setText("Recording")
            self.pushButton_rec.setEnabled(False)
            self.pushButton_play.setText("Pause")
            self.pushButton_save.setEnabled(False)
            #TODO: Tracks automatisch erzeugen mit Track_[Nr].wav
            # Nr hier bei aufsteigend.
            self.recfile = self.rec.open()
            self.recfile = self.recfile.start_recording()
            self.timer = threading.Timer(1.0,self.update_time).start()

    #Erzeugt neue Datei und nimmt weiter auf
    def btn_cut_clicked(self):
        self.recfile.stop_recording()
        self.recfile.close()
        #TODO: letzten track umwandeln
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
        year = str(self.dateEdit.date())
        #kommentar wird von ID3 nicht unterstuetzt
        #comments = str(self.lineEdit_kommentar.text())
        #TODO: add getdate
        audio = EasyID3(self.cur_track)
        audio["artist"] = artist
        audio["title"] = title
        audio["album"] = album
        audio["genre"] = genre
        audio["date"] = year #funktioniert nicht
        #audio["comments"] = comments
        audio.save()
        print("Taggs gespeichert")

    def btn_save_clicked(self):
        #TODO: Speichere in Ordner (defult [Datum]-Godi), pfad waehlbar
        self.cur_path = QtGui.QFileDialog.getExistingDirectory(
                self,"Ordner waehlen",".")
        self.fileEdit.setText(self.cur_path)
        self.update_listTracks()

    def update_time(self):
        if self.recfile != None:
            time = self.recfile.time_i
            print time
            self.label_time.setText(str(time["current_time"]))
            #TODO: ist immer 0, selber Zeit messen von start bis ende

    #updatet die Listenansicht
    def update_listTracks(self):
        self.cur_path = str(self.fileEdit.text())
        find = os.path.join(self.cur_path, "*.mp3")
        files = glob.glob(find)
        list = self.listTracks
        model = QtGui.QStandardItemModel(list)
        for f in files:
            model.appendRow(QtGui.QStandardItem(os.path.basename(f)))
        list.setModel(model)
        list.clicked.connect(self.on_listTracks_changed)

    #Click listener auf ItemListView
    #Es zeigt die Tags des angeklickten Files an
    def on_listTracks_changed(self, index):
        self.cur_track = os.path.join(self.cur_path,
                     str(index.model().itemFromIndex(index).text()))
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
            #date nicht unterstuetzt
        if id3r.getValue("date"):
            print id3r.getValue("date")
            self.dateEdit.setDate(id3r.getValue("date"))

    def act_neues_projekt(self):
        #TODO: Speichere in Ordner (defult [Datum]-Godi), pfad waehlbar
        #temp_path = QtGui.QFileDialog.getExistingDirectory(
        #    self,"Neues Projekt erzeugen in:",".")
        #today = datetime.date.today()
        #projektName = "{:%Y_%m_%d}-Godi".format(today)
        #print projektName
        #print temp_path
        #self.cur_path = os.path.join(temp_path, projektName)
        #if not os.path.exists(self.cur_path):
        #    os.makedirs(self.cur_path)
        #self.fileEdit.setText(self.cur_path)
        #self.update_listTracks()
        #Dialog()
        print("new Projekt")
        # path_dialog muss eine Variable von self sein. Andernfalls wird das
        # Fenster nach Ausfuehrung direkt wieder zerstoert.
        self.path_dialog = PathDialog()
        self.path_dialog.show()
        
    def exit(self):
        self.close()
        sys.exit(app.exec_())


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = GodiRec()
    window.show()
    sys.exit(app.exec_())



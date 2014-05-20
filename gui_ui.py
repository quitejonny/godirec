# -*- coding: utf-8 -*-
import sys
import os
import re
import glob
import id3reader
import datetime
import threading
from mutagen.easyid3 import EasyID3
from PyQt4 import QtCore, QtGui, uic
from godiRec import Recorder

class PathDialog(QtGui.QDialog):
    """ Dialog soll Workspace Phat abfragen und Projekt Namen, diese erstellen
        und an das Programm zurückgeben."""

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
        for i in ("Play", "Stop", "Rec", "Cut", "Save", "Change"):
            getattr(self, i+"Button").clicked.connect(
                    getattr(self, "onButton{}Clicked".format(i)))
        # self.ButtonPlay.clicked.connect(self.onButtonPlayClicked)
        # self.ButtonStop.clicked.connect(self.onButtonStopClicked)
        # self.ButtonRec.clicked.connect(self.onButtonRecClicked)
        # self.ButtonCut.clicked.connect(self.onButtonCutClicked)
        # self.ButtonSave.clicked.connect(self.onButtonSaveClicked)
        # self.ButtonChange.clicked.connect(self.onButtonChangeClicked)
        self.actionExit.triggered.connect(self.exit)
        self.actionNeues_Projekt.triggered.connect(self.act_neues_projekt)
        self.update_tracks_list()
        self.cur_track = None
        self.timer = None
        self.cur_path = ""
        
    def onButtonPlayClicked(self):
        if self.ButtonPlay.text() == "Pause":
            self.ButtonPlay.setText("Play")
            self.ButtonRec.setText("Rec")
            self.ButtonRec.setEnabled(False)
            self.ButtonSave.setEnabled(False)
            self.recfile.stop_recording()
        else:
            self.ButtonPlay.setText("Pause")
            self.ButtonRec.setText("Recording")
            self.ButtonRec.setEnabled(False)
            self.recfile.start_recording()

    def onButtonStopClicked(self):
        self.ButtonRec.setText("Rec")
        self.ButtonRec.setEnabled(True)
        self.ButtonPlay.setEnabled(True)
        self.ButtonSave.setEnabled(True)
        self.timer.cancel()
        self.recfile.stop_recording()
        self.recfile.close()
        self.update_tracks_list()

    def onButtonRecClicked(self):
        if self.ButtonRec.text() != "Recording":
            self.ButtonRec.setText("Recording")
            self.ButtonRec.setEnabled(False)
            self.ButtonPlay.setText("Pause")
            self.ButtonSave.setEnabled(False)
            #TODO: Tracks automatisch erzeugen mit Track_[Nr].wav
            # Nr hier bei aufsteigend.
            self.recfile = self.rec.open()
            self.recfile = self.recfile.start_recording()
            self.timer = threading.Timer(1.0,self.update_time)
            self.timer.start()

    def onButtonCutClicked(self):
        """ Erzeugt neue Datei und nimmt weiter auf"""
        self.recfile.stop_recording()
        self.recfile.close()
        #TODO: letzten track umwandeln
        self.rec.save("track_1.mp3", ".temp/track_1.wav")
        self.recfile = self.rec.open()
        self.recfile.start_recording()
        self.update_tracks_list()

    def onButtonButtonClicked(self):
        """ Schreibt Tags in MP3 datei"""
        #kommentar wird von ID3 nicht unterstuetzt
        #comments = str(self.LineEditComment.text())
        #TODO: add getdate
        audio = EasyID3(self.cur_track)
        for i in ('Title', 'Performer', 'Album', 'Genre'):
            audio[i] = getattr(self, 'LineEdit'+i).text()
        audio["date"] = str(self.dateEdit.date()) #funktioniert nicht
        #audio["comments"] = comments
        audio.save()
        print("Taggs gespeichert")

    def onButtonSaveClicked(self):
        #TODO: Speichere in Ordner (defult [Datum]-Godi), pfad waehlbar
        self.cur_path = QtGui.QFileDialog.getExistingDirectory(
                self,"Ordner waehlen",".")
        self.fileEdit.setText(self.cur_path)
        self.update_tracks_list()

    def update_time(self):
        if self.recfile != None:
            time = self.recfile.time_i
            print time
            self.label_time.setText(str(time["current_time"]))
            #TODO: ist immer 0, selber Zeit messen von start bis ende

    def update_tracks_list(self):
        """ updatet die Listenansicht"""
        self.cur_path = str(self.fileEdit.text())
        find = os.path.join(self.cur_path, "*.mp3")
        files = glob.glob(find)
        list = self.tracks_list
        model = QtGui.QStandardItemModel(list)
        for f in files:
            model.appendRow(QtGui.QStandardItem(os.path.basename(f)))
        list.setModel(model)
        list.clicked.connect(self.on_tracks_list_changed)

    def on_tracks_list_changed(self, index):
        """ Click listener auf ItemListView
            Es zeigt die Tags des angeklickten Files an"""
        self.cur_track = os.path.join(self.cur_path,
                     str(index.model().itemFromIndex(index).text()))
        id3r = id3reader.Reader(self.cur_track)
        for i in ('Title', 'Performer', 'Album', 'Genre', 'Comment'):
            if id3r.getValue(i):
                getattr(self, 'LineEdit'+i).setText(id3r.getValue(i))
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
        #self.update_tracks_list()
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



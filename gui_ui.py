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
        self.cur_path1 = ""
        print("PathDialog init")
        for i in ("Dir", "Create"):
            getattr(self, "Button"+i).clicked.connect(
                    getattr(self, "onButton{}Clicked".format(i)))
        today = datetime.date.today()
        projektName = "{:%Y_%m_%d}-Godi".format(today)
        self.LineEditProjekt.setText(projektName)

    def onButtonDirClicked(self):
        temp_path = QtGui.QFileDialog.getExistingDirectory(
            self,"Neues Projekt erzeugen in:",".")
        self.LineEditPath.setText(temp_path)
        #self.cur_path = os.path.join(temp_path, projektName)
        #self.LineEditFile.setText(self.cur_path)
        #self.updateListTracks()

    def onButtonCreateClicked(self):
        temp_path = str(self.LineEditPath.text())
        projektName = str(self.LineEditProjekt.text())
        self.cur_path1 = os.path.join(temp_path, projektName)
        if not os.path.exists(self.cur_path1):
            os.makedirs(self.cur_path1)
        self.close()

    def getValues(self):
        return str(self.cur_path1)
        

class GodiRec(QtGui.QMainWindow):

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        ui_file = os.path.join("ui", "godi_rec.ui")
        uic.loadUi(ui_file, self)
        self.rec = Recorder(channels=2) 
        for i in ("Play", "Stop", "Rec", "Cut", "Save", "Change"):
            getattr(self, "Button"+i).clicked.connect(
                    getattr(self, "onButton{}Clicked".format(i)))
        self.ActionExit.triggered.connect(self.exit)
        self.ActionNewProject.triggered.connect(self.createNewProject)
        self.cur_track = None
        self.cur_path = ""
        
    def onButtonPlayClicked(self):
        if self.ButtonPlay.text() == "Pause":
            self.ButtonPlay.setText("Play")
            self.ButtonRec.setText("Rec")
            self.ButtonRec.setEnabled(False)
            self.ButtonSave.setEnabled(False)
            self.recfile.stop_recording()
        else:
            try:
                self.recfile.start_recording()
                self.ButtonPlay.setText("Pause")
                self.ButtonRec.setText("Recording")
                self.ButtonRec.setEnabled(False)
            except AttributeError:
                pass

    def onButtonStopClicked(self):
        if self.ButtonRec.text() == "Recording":
            self.ButtonRec.setText("Rec")
            self.ButtonRec.setEnabled(True)
            self.ButtonPlay.setEnabled(True)
            self.ButtonSave.setEnabled(True)
            self.recfile.stop_recording()
            self.recfile.close()
            fpath = os.path.join(self.rec.tmpdir, self.recfile.fname)
            dpath = os.path.join(self.cur_path, re.sub(".wav",".mp3",
                                                   self.recfile.fname))
            self.rec.save(dpath, fpath)
        self.updateListTracks()

    def onButtonRecClicked(self):
        if self.ButtonRec.text() != "Recording":
            self.ButtonRec.setText("Recording")
            self.ButtonRec.setEnabled(False)
            self.ButtonPlay.setText("Pause")
            self.ButtonSave.setEnabled(False)
            self.recfile = self.rec.open()
            self.recfile = self.recfile.start_recording()

    def onButtonCutClicked(self):
        """ Erzeugt neue Datei und nimmt weiter auf"""
        if self.ButtonRec.text() == "Recording":
            self.recfile.stop_recording()
            self.recfile.close()
            fpath = os.path.join(self.rec.tmpdir, self.recfile.fname)
            dpath = os.path.join(self.cur_path, re.sub(".wav",".mp3",
                                                    self.recfile.fname))
            self.rec.save(dpath, fpath)
            self.recfile = self.rec.open()
            self.recfile.start_recording()
            self.updateListTracks()

    def onButtonChangeClicked(self):
        """ Schreibt Tags in MP3 datei"""
        #kommentar wird von ID3 nicht unterstuetzt
        #comments = str(self.LineEditComment.text())
        #valid_keys: album, composer, genre, date,lyricist,
        # title, version, artist, tracknumber
        #TODO: add getdate
        audio = EasyID3(self.cur_track)
        for i in ('Title', 'Album', 'Genre', 'Artist'):
            print ""+getattr(self, 'LineEdit'+i).text()
            audio[i.lower()] = str(getattr(self, 'LineEdit'+i).text())
        audio["date"] = str(self.dateEdit.date()) #funktioniert nicht
        #audio["comments"] = comments
        audio.save()
        print("Taggs gespeichert")

    def onButtonSaveClicked(self):
        #TODO: Speichere in Ordner (defult [Datum]-Godi), pfad waehlbar
        #self.cur_path = QtGui.QFileDialog.getExistingDirectory(
        #        self,"Ordner waehlen",".")
        #self.LineEditFile.setText(self.cur_path)
        self.updateListTracks()

    def update_time(self):
        if self.recfile != None:
            time = self.recfile.time_i
            print time
            self.label_time.setText(str(time["current_time"]))
            #TODO: ist immer 0, selber Zeit messen von start bis ende

    def updateListTracks(self):
        """ updatet die Listenansicht"""
        print self.cur_path
        find = os.path.join(self.cur_path, "*.mp3")
        files = glob.glob(find)
        list = self.ListTracks
        model = QtGui.QStandardItemModel(list)
        for f in files:
            model.appendRow(QtGui.QStandardItem(os.path.basename(f)))
        list.setModel(model)
        list.clicked.connect(self.onListTracksChanged)

    def onListTracksChanged(self, index):
        """ Click listener auf ItemListView
            Es zeigt die Tags des angeklickten Files an"""
        self.cur_track = os.path.join(self.cur_path,
                     str(index.model().itemFromIndex(index).text()))
        id3r = id3reader.Reader(self.cur_track)
        for i in ('Title', 'Artist', 'Album', 'Genre', 'Comment'):
            if id3r.getValue(i.lower()):
                getattr(self, 'LineEdit'+i).setText(id3r.getValue(i.lower()))
            else:
                getattr(self, 'LineEdit'+i).setText("")
        #date nicht unterstuetzt
        if id3r.getValue("date"):
            print id3r.getValue("date")
            self.dateEdit.setDate(id3r.getValue("date"))

    def createNewProject(self):
        # path_dialog muss eine Variable von self sein. Andernfalls wird das
        # Fenster nach Ausfuehrung direkt wieder zerstoert.
        self.path_dialog = PathDialog()
        self.path_dialog.show()
        self.path_dialog.exec_()
        self.cur_path = self.path_dialog.getValues()
        self.updateListTracks()

    def exit(self):
        self.close()
        sys.exit(app.exec_())


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = GodiRec()
    window.show()
    sys.exit(app.exec_())



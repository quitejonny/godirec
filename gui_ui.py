# -*- coding: utf-8 -*-
import sys
import os
import re
import glob
import id3reader
import datetime
import threading
import shelve
from datetime import datetime
from mutagen.easyid3 import EasyID3
from PyQt4 import QtCore, QtGui, uic
import dialog
import mainwindow
import godiRec


class RecorderListModel(QtCore.QAbstractListModel): 

    def __init__(self, rec_manager, parent=None): 
        QtCore.QAbstractListModel.__init__(self, parent) 
        self.set_rec_manager(rec_manager)

    def set_rec_manager(self, rec_manager):
        self.rec_manager = rec_manager
        self.rec_manager.set_callback(self.update)

    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.rec_manager.tracklist) 
 
    def data(self, index, role): 
        if index.isValid() and role == QtCore.Qt.DisplayRole:
            track = self.rec_manager.get_track(index.row())
            return QtCore.QVariant(track.origin_file)
            #return QtCore.QVariant(track["title"])
        else: 
            return QtCore.QVariant()

    def itemFromIndex(self, index):
        return self.rec_manager.get_track(index.row())

    def update(self):
        self.layoutChanged.emit()


class PathDialog(QtGui.QDialog, dialog.Ui_Dialog):
    """ Dialog soll Workspace Phat abfragen und Projekt Namen, diese erstellen
        und an das Programm zurückgeben."""

    def __init__(self, path = ""):
        QtGui.QDialog.__init__(self)
        dialog.Ui_Dialog.__init__(self)
        self.setupUi(self)
        self.cur_path1 = ""
        for i in ("Dir", "Create"):
            getattr(self, "Button"+i).clicked.connect(
                    getattr(self, "onButton{}Clicked".format(i)))
        today = datetime.today()
        projektName = "{:%Y_%m_%d}-Godi".format(today)
        self.LineEditProjekt.setText(projektName)
        self.LineEditPath.setText(path)

    def onButtonDirClicked(self):
        temp_path = QtGui.QFileDialog.getExistingDirectory(
            self,"Neues Projekt erzeugen in:",".")
        self.LineEditPath.setText(temp_path)

    def onButtonCreateClicked(self):
        temp_path = str(self.LineEditPath.text())
        projektName = str(self.LineEditProjekt.text())
        self.cur_path1 = os.path.join(temp_path, projektName)
        if not os.path.exists(self.cur_path1):
            os.makedirs(self.cur_path1)
        self.close()

    def getValues(self):
        return str(self.cur_path1)
        

class GodiRec(QtGui.QMainWindow, mainwindow.Ui_GodiRec):

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        mainwindow.Ui_GodiRec.__init__(self)
        self.setupUi(self)
        self.rec_manager = godiRec.Manager('/home/johannes/Desktop/test/')
        self.rec = godiRec.Recorder(self.rec_manager)
        self.lm = RecorderListModel(self.rec_manager, self)
        self.ListTracks.setModel(self.lm)
        self.settings = shelve.open("setting.dat", writeback = True)
        for i in ("Play", "Stop", "Rec", "Cut", "Save", "Change"):
            getattr(self, "Button"+i).clicked.connect(
                    getattr(self, "onButton{}Clicked".format(i)))
            getattr(self, "Button"+i).setEnabled(False)
        self.ActionExit.triggered.connect(self.exit)
        self.ActionNewProject.triggered.connect(self.createNewProject)
        self.setIcons()
        self.iconPause = QtGui.QIcon()
        self.iconPause.addPixmap(QtGui.QPixmap("ui/pause10.png"))
        self.iconPlay = QtGui.QIcon()
        self.iconPlay.addPixmap(QtGui.QPixmap("ui/media23.png"))
        self.cur_track = None
        self.cur_path = ""
        self.start_time = "00"
        self.wordlistTitel = ["Lied","Begrueßung","Praeludium","Infos",
                         "Ankuendigungen", "Kinderlied", "Segen", 
                         "Postludium", "Predigt", "Sonstiges"]
        self.wordlistArtist = ["Andreas T. Reichert", "Samuel Falk", 
                               "Thomas Klein", "Sigfried Pries"]
        self.completerTitel = QtGui.QCompleter(self.wordlistTitel, self)
        self.completerArtist = QtGui.QCompleter(self.wordlistArtist, self)
        self.LineEditTitle.setCompleter(self.completerTitel)
        self.LineEditPerformer.setCompleter(self.completerArtist)

    def setIcons(self):
        """ This function is used as workaround for not loading icons in
            python generated ui code"""
        icons = {"Play": "media23.png", "Stop": "media26.png",
                 "Rec": "record6.png", "Cut": "cutting.png"}
        for i, img in icons.iteritems():
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(os.path.join('ui', img)))
            getattr(self, "Button"+i).setIcon(icon)
        
    def onButtonPlayClicked(self):
        if self.ButtonPlay.text() == "Pause":
            self.ButtonPlay.setIcon(self.iconPlay)
            self.ButtonRec.setText("Rec")
            self.ButtonRec.setEnabled(False)
            self.ButtonSave.setEnabled(False)
            self.rec.pause()
        else:
            try:
                self.rec.play()
                self.ButtonPlay.setIcon(self.iconPause)
                self.ButtonRec.setText("Recording")
                self.ButtonRec.setEnabled(False)
            except AttributeError:
                pass

    def onButtonStopClicked(self):
        if not self.ButtonRec.isEnabled():
            self.ButtonRec.setEnabled(True)
            self.ButtonCut.setEnabled(False)
            self.ButtonPlay.setEnabled(True)
            self.ButtonPlay.setIcon(self.iconPlay)
            self.ButtonSave.setEnabled(True)
            self.rec.stop()
            # album = re.sub("_", " ",str(self.LabelProjekt.text()))
            # th = threading.Thread(self.rec.save(dpath, fpath, album))
        self.timer.cancel()

    def onButtonRecClicked(self):
        if self.ButtonRec.isEnabled():
            self.ButtonRec.setEnabled(False)
            self.ButtonCut.setEnabled(True)
            self.ButtonPlay.setIcon(self.iconPause)
            self.rec.play()
            self.timer = threading.Timer(1.0, self.update_time)
            self.timer.start()
            self.start_time = datetime.now()

    def onButtonCutClicked(self):
        """ Erzeugt neue Datei und nimmt weiter auf"""
        if not self.ButtonRec.isEnabled():
            self.rec.cut()
            self.start_time = datetime.now()
            # album = re.sub("_", " ",str(self.LabelProjekt.text()))
            # th = threading.Thread(self.rec.save(dpath, fpath, album))

    def onButtonChangeClicked(self):
        """ Schreibt Tags in MP3 datei"""
        #kommentar wird von ID3 nicht unterstuetzt
        #comments = str(self.LineEditComment.text())
        #valid_keys: album, composer, genre, date,lyricist,
        # title, version, artist, tracknumber
        #TODO: add getdate
        tags = godiRec.Tags()
        for i in ('Title', 'Album', 'Genre', 'Artist'):
            print(""+getattr(self, 'LineEdit'+i).text())
            tags[i.lower()] = str(getattr(self, 'LineEdit'+i).text())
        # audio = EasyID3(self.cur_track)
        # for i in ('Title', 'Album', 'Genre'):
        #     audio[i.lower()] = str(getattr(self, 'LineEdit'+i).text())
        # audio["artist"] = str(self.LineEditPerformer.text())
        # audio["date"] = str(self.dateEdit.date()) #funktioniert nicht
        #audio["comments"] = comments
        audio.save()
        print("Taggs gespeichert")

    def onButtonSaveClicked(self):
        self.lm.update()

    def update_time(self):
        if self.rec != None:
            over = (datetime.now() - self.start_time)
            print over
            seconds = over.seconds
            minuten = (seconds % 3600) // 60
            self.LabelTime.setText(("{}:{}/--:--".format(minuten, seconds %60)))
        self.timer = threading.Timer(1.0, self.update_time)
        self.timer.start()

    def updateListTracks(self):
        """ updatet die Listenansicht"""
        # print self.cur_path
        # find = os.path.join(self.cur_path, "*.mp3")
        # files = glob.glob(find)
        # list = self.ListTracks
        # model = QtGui.QStandardItemModel(list)
        # for f in files:
        #     model.appendRow(QtGui.QStandardItem(os.path.basename(f)))
        # list.setModel(model)
        # list.clicked.connect(self.onListTracksChanged)
        pass

    def onListTracksChanged(self, index):
        """ Click listener auf ItemListView
            Es zeigt die Tags des angeklickten Files an"""
        self.cur_track = os.path.join(self.cur_path,
                     str(index.model().itemFromIndex(index).text()))
        id3r = id3reader.Reader(self.cur_track)
        for i in ('Title', 'Album', 'Performer', 'Genre', 'Comment'):
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
        if self.settings.has_key('path'):
            self.path_dialog = PathDialog(self.settings['path'])
        else:
            self.path_dialog = PathDialog()
        self.path_dialog.show()
        self.path_dialog.exec_()
        self.cur_path = self.path_dialog.getValues()
        self.settings['path'] = os.path.dirname(self.cur_path)
        self.settings.sync()
        self.LabelProjekt.setText(os.path.basename(self.cur_path))
        self.rec_manager = godiRec.Manager(self.cur_path)
        self.rec = godiRec.Recorder(self.rec_manager)
        self.lm.set_rec_manager(self.rec_manager)
        for i in ("Play", "Stop", "Rec", "Save", "Change"):
            getattr(self, "Button"+i).setEnabled(True)
        # self.updateListTracks()

    def exit(self):
        self.close()
        sys.exit(app.exec_())


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = GodiRec()
    window.show()
    sys.exit(app.exec_())



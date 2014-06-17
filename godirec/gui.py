# -*- coding: utf-8 -*-
import sys
import os
import multiprocessing
from datetime import datetime
from PyQt4 import QtCore, QtGui, uic
import godirec
import pkg_resources


class RecorderListModel(QtCore.QAbstractListModel): 

    def __init__(self, rec_manager=godirec.Manager(""), parent=None): 
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
            return track.basename
        else: 
            return None

    def itemFromIndex(self, index):
        return self.rec_manager.get_track(index.row())

    def update(self):
        self.layoutChanged.emit()
        index = self.index(len(self.rec_manager.tracklist)-1)

    def getLastItemIndex(self):
        return self.index(len(self.rec_manager.tracklist)-1)


class PathDialog(QtGui.QDialog):
    """ Dialog soll Workspace Phat abfragen und Projekt Namen, diese erstellen
        und an das Programm zurückgeben."""

    def __init__(self, path = ""):
        QtGui.QDialog.__init__(self)
        dialog_ui_file = pkg_resources.resource_filename(__name__, 'data/ui/dialog.ui')
        uic.loadUi(dialog_ui_file, self)
        self.cur_path1 = ""
        for i in ("Dir", "Create"):
            getattr(self, "Button"+i).clicked.connect(
                    getattr(self, "onButton{}Clicked".format(i)))
        projektName = "{:%Y_%m_%d}-Godi".format(datetime.today())
        self.LineEditProjekt.setText(projektName)
        self.LineEditPath.setText(path)
        self.iconDir = QtGui.QIcon()
        folder_yellow = pkg_resources.resource_filename(__name__, 'data/ui/folder-yellow.png')
        self.iconDir.addPixmap(QtGui.QPixmap(folder_yellow))
        self.ButtonDir.setIcon(self.iconDir)
        self.ButtonCreate.setFocus()

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
        

class GodiRec(QtGui.QMainWindow):

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        godi_rec_ui = pkg_resources.resource_filename(__name__, 'data/ui/godi_rec.ui')
        uic.loadUi(godi_rec_ui, self)
        self.RecListModel = RecorderListModel(parent=self)
        self.ListTracks.setModel(self.RecListModel)
        self.ListTracks.clicked.connect(self.onListTracksIndexChanged)
        self.settings = QtCore.QSettings("EFG Aachen", "GodiRec")
        for i in ("Stop", "Rec", "Cut"):
            getattr(self, "Button"+i).clicked.connect(
                    getattr(self, "onButton{}Clicked".format(i)))
            getattr(self, "Button"+i).setEnabled(False)
        self.ActionExit.triggered.connect(self.exit)
        self.ActionNewProject.triggered.connect(self.createNewProject)
        self.status = 0 #Status 0=no projekt, 1=no stream running, 2=rec
        self.setIcons()
        self.iconPause = QtGui.QIcon()
        pause_png = pkg_resources.resource_filename(__name__, 'data/ui/pause10.png')
        self.iconPause.addPixmap(QtGui.QPixmap(pause_png))
        self.iconRec = QtGui.QIcon()
        record_png = pkg_resources.resource_filename(__name__, 'data/ui/record6.png')
        self.iconRec.addPixmap(QtGui.QPixmap(record_png))
        microphone_ico = pkg_resources.resource_filename(__name__, 'data/ui/microphone2.ico')
        self.setWindowIcon(QtGui.QIcon(microphone_ico))
        self.current_track = godirec.Track("")
        self.cur_path = ""
        self.wordlistTitel = ["Lied","Begrüßung","Präludium","Infos",
                         "Ankündigungen", "Kinderlied", "Segen",
                         "Postludium", "Predigt", "Sonstiges"]
        self.wordlistArtist = ["Andreas T. Reichert", "Samuel Falk", 
                               "Thomas Klein", "Sigfried Pries"]
        self.completerTitel = QtGui.QCompleter(self.wordlistTitel, self)
        self.completerArtist = QtGui.QCompleter(self.wordlistArtist, self)
        self.LineEditTitle.setCompleter(self.completerTitel)
        self.LineEditArtist.setCompleter(self.completerArtist)

    def setIcons(self):
        """ This function is used as workaround for not loading icons in
            python generated ui code"""
        icons = {"Stop": "media26.png", "Rec": "record6.png", 
                 "Cut": "cutting.png"}
        for i, img in icons.items():
            icon = QtGui.QIcon()
            img_file = pkg_resources.resource_filename(__name__, 'data/ui/{}'.format(img))
            icon.addPixmap(QtGui.QPixmap(img_file))
            getattr(self, "Button"+i).setIcon(icon)
        
    def onButtonStopClicked(self):
        if self.status == 1 or self.status == 2:
            self.ButtonRec.setIcon(self.iconRec)
            self.ButtonCut.setEnabled(False)
            self.rec.stop()
            self.onListTracksIndexChanged()

    def onButtonRecClicked(self):
        if self.status == 1:
            self.ButtonRec.setIcon(self.iconPause)
            self.ButtonCut.setEnabled(True)
            self.status = 2
            self.rec.play()
            index = self.RecListModel.getLastItemIndex()
            self.ListTracks.setCurrentIndex(index)
            self.onListTracksIndexChanged()
        elif self.status == 2:
            self.status = 1
            self.ButtonRec.setIcon(self.iconRec)
            self.rec.pause()

    def onButtonCutClicked(self):
        """ Erzeugt neue Datei und nimmt weiter auf"""
        if self.status == 1 or self.status == 2:
            self.rec.cut()
            index = self.RecListModel.getLastItemIndex()
            self.ListTracks.setCurrentIndex(index)
            self.onListTracksIndexChanged()

    def onButtonChangeClicked(self):
        """ Schreibt Tags in MP3 datei"""
        self.onListTracksIndexChanged()

    def onButtonSaveClicked(self):
        self.RecListModel.update()

    def updateTime(self, timer):
        if self.rec != None:
            track_time = timer.get_track_time()
            rec_time = timer.get_recording_time()
            self.LabelTime.setText(track_time+"/"+rec_time)

    def onListTracksIndexChanged(self):
        # save old Tags if tags have changed
        tags = self.tags()
        if self.current_track.tags != tags:
            self.current_track.tags = tags
            self.current_track.save()
        index = self.ListTracks.selectedIndexes()[0]
        self.current_track = self.RecListModel.itemFromIndex(index)
        self.setTags(self.current_track)

    def setTags(self, track):
        for tag in set(track.tags.keys()).difference(set(['date'])):
            getattr(self, 'LineEdit'+tag.title()).setText(track.tags[tag])
        if track.tags['date'] == "":
            year = datetime.now().year
        else:
            year = int(track.tags['date'])
        self.LineEditDate.setDate(QtCore.QDate(year, 1, 1))

    def tags(self):
        tags = godirec.Tags()
        for tag in set(tags.keys()).difference(set(['date'])):
            tags[tag] = str(getattr(self, 'LineEdit'+tag.title()).text())
        tags['date'] = str(self.LineEditDate.date().toPyDate().year)
        return tags

    def createNewProject(self):
        # path_dialog muss eine Variable von self sein. Andernfalls wird das
        # Fenster nach Ausfuehrung direkt wieder zerstoert.
        if 'path' in self.settings.allKeys():
            self.path_dialog = PathDialog(self.settings.value('path',type=str))
        else:
            self.path_dialog = PathDialog()
        self.path_dialog.show()
        self.path_dialog.exec_()
        self.cur_path = self.path_dialog.getValues()
        self.settings.setValue('path', os.path.dirname(self.cur_path))
        self.setWindowTitle(os.path.basename(self.cur_path))
        self.rec_manager = godirec.Manager(self.cur_path)
        self.rec = godirec.Recorder(self.rec_manager)
        self.rec.timer.set_callback(self.updateTime)
        self.RecListModel.set_rec_manager(self.rec_manager)
        self.status = 1
        for i in ("Stop", "Rec"):
            getattr(self, "Button"+i).setEnabled(True)

    def exit(self):
        self.close()
        sys.exit(app.exec_())


if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = QtGui.QApplication(sys.argv)
    QtCore.QObject.connect(app,QtCore.SIGNAL("lastWindowClosed()"),app,QtCore.SLOT("quit()"))
    window = GodiRec()
    window.show()
    sys.exit(app.exec_())



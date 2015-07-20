# -*- coding: utf-8 -*-
# GodiRec is a program for recording a church service
# Copyright (C) 2014 Daniel Supplieth and Johannes Roos
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import os
from datetime import datetime
from PyQt5 import QtCore, QtGui, uic, QtWidgets
from PyQt5.QtWidgets import QMessageBox
import logging
import copy
import queue
import godirec
from godirec.gui import upload, settings
from godirec.gui.helper import createIcon
from godirec import core, audio


class SignalThread(QtCore.QThread):

    def __init__(self, q_object):
        QtCore.QThread.__init__(self)
        self._q_object = q_object
        self.queue = queue.Queue()
        self.start()

    def signal(self):
        return self.queue.put

    def run(self):
        while True:
            signal, *args = self.queue.get()
            getattr(self._q_object, signal).emit(*args)


class RecorderListModel(QtCore.QAbstractListModel):

    layoutUpdate = QtCore.pyqtSignal()

    def __init__(self, rec_manager=core.Manager(""), parent=None):
        QtCore.QAbstractListModel.__init__(self, parent)
        self.signals = SignalThread(self)
        self.set_rec_manager(rec_manager)
        self.layoutUpdate.connect(self.update)

    def set_rec_manager(self, rec_manager):
        if hasattr(self, "rec_manager"):
            delattr(self, "rec_manager")
        self.rec_manager = rec_manager
        self.rec_manager.set_callback(self.signals.signal(), "layoutUpdate")

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.rec_manager.tracklist)

    def data(self, index, role):
        if index.isValid() and role == QtCore.Qt.DisplayRole:
            row = index.row()
            if row > self.getLastItemIndex().row():
                row = self.getLastItemIndex().row()
            track = self.rec_manager.get_track(row)
            if track.tags.title:
                return "{:02d} - {}".format(int(track.tags.tracknumber),
                                            track.tags.title)
            else:
                return track.basename
        else:
            return None

    def itemFromIndex(self, index):
        return self.rec_manager.get_track(index.row())

    def update(self):
        self.layoutChanged.emit()

    def getLastItemIndex(self):
        return self.index(len(self.rec_manager.tracklist)-1)


class DialogOpener(QtWidgets.QDialog):

    @classmethod
    def open(cls, ui_file, parent=None):
        dialog_opener = cls(ui_file, parent=parent)
        dialog_opener.show()


    def __init__(self, ui_file, parent=None):
        QtWidgets.QDialog.__init__(self, parent=parent)
        about_ui_file = godirec.resource_stream("godirec", ui_file)
        uic.loadUi(about_ui_file, self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowIcon(createIcon('data/ui/microphone2.ico'))


class AboutDialog(DialogOpener):

    def __init__(self, ui_file, parent=None):
        DialogOpener.__init__(self, ui_file, parent=parent)
        self.label_ver.setText("v"+godirec.__version__)


NO_STREAM_RUNNING = "no stream is running"
NO_PROJECT = "no project opened"
RECORDING = "currently recording"
STREAM_PAUSING = "currently pausing"


class GodiRecWindow(QtWidgets.QMainWindow):

    statusSet = QtCore.pyqtSignal()
    statusClear = QtCore.pyqtSignal()
    progressUpdate = QtCore.pyqtSignal(float)

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        godi_rec_ui = godirec.resource_stream("godirec", 'data/ui/godi_rec.ui')
        uic.loadUi(godi_rec_ui, self)
        self.signals = SignalThread(self)
        self.RecListModel = RecorderListModel(parent=self)
        self.ListTracks.setModel(self.RecListModel)
        self.selection = self.ListTracks.selectionModel()
        self.selection.selectionChanged.connect(self.onListTracksIndexChanged)
        self.qtSettings = QtCore.QSettings("EFG Aachen", "GodiRec")
        self.settings = settings.Store(self.qtSettings, self)
        for i in ("Stop", "Rec", "Cut"):
            getattr(self, "Button"+i).clicked.connect(
                getattr(self, "onButton{}Clicked".format(i)))
        self.enableRecButtons(False)
        self.enableTagEdits(False)
        self.ActionExit.triggered.connect(self.close)
        self.ActionNewProject.triggered.connect(self.createNewProject)
        self.ActionSermon.triggered.connect(self.uploadSermon)
        self.ActionSettings.triggered.connect(self.openSettings)
        self.ActionOpenProject.triggered.connect(self.openProject)
        self.ActionAbout.triggered.connect(lambda: AboutDialog.open
                                           ("data/ui/about.ui", self))
        self.ActionHelp.triggered.connect(lambda: DialogOpener.open
                                          ("data/ui/help.ui", self))
        # Status: NO_STREAM_RUNNING, NO_PROJECT, RECORDING
        self.status = NO_PROJECT
        self.setIcons()
        self.updateWordList()
        self.iconPause = createIcon('data/ui/pause10.png')
        self.iconRec = createIcon('data/ui/record6.png')
        self.setWindowIcon(createIcon('data/ui/microphone2.ico'))
        self.current_track = core.Track("", "")
        self.ProgressBar = QtWidgets.QProgressBar()
        self.statusbar.addWidget(self.ProgressBar, 1)
        self.ProgressBar.hide()
        # connect status for statusbar
        self.statusSet.connect(self.setStatus)
        self.statusClear.connect(self.clearStatus)
        self.progressUpdate.connect(self.updateProgressBar)
        core.future_pool.set_start_callback(self.signals.signal(),
                                            "statusSet")
        core.future_pool.set_done_callback(self.signals.signal(),
                                           "statusClear")
        audio.WaveConverter.set_progress_callback(self.signals.signal(),
                                                  "progressUpdate")
        logging.info('GUI loaded')
        self.menuUpload.menuAction().setVisible(False)

    def uploadSermon(self):
        upload.start(self.rec_manager, self.settings, self)

    def enableRecButtons(self, isEnabled):
        for i in ("Stop", "Rec", "Cut"):
            getattr(self, "Button"+i).setEnabled(isEnabled)

    def enableTagEdits(self, isEnabled):
        edits = ("Title", "Artist", "Album", "Genre", "Date", "Comment")
        for edit in edits:
            getattr(self, 'LineEdit'+edit).setEnabled(isEnabled)

    def updateWordList(self):
        edits = ("Title", "Artist", "Album", "Genre", "Comment")
        edit_dict = {
            e: getattr(self, "Label"+e).text().strip(":") for e in edits
        }
        completion = self.settings.tags
        for edit in edits:
            key = edit_dict[edit]
            completer = QtWidgets.QCompleter(self.settings.tags[key], self)
            completer.setCaseSensitivity(False)
            getattr(self, 'LineEdit'+edit).setCompleter(completer)

    def setIcons(self):
        """This function is used as workaround for not loading icons in
           python generated ui code"""
        icons = {"Stop": "media26.png", "Rec": "record6.png",
                 "Cut": "cutting.png"}
        for i, img in icons.items():
            icon = createIcon('data/ui/{}'.format(img))
            getattr(self, "Button"+i).setIcon(icon)

    def onButtonStopClicked(self):
        if self.status in (NO_STREAM_RUNNING, RECORDING, STREAM_PAUSING):
            self.ButtonRec.setIcon(self.iconRec)
            self.ButtonCut.setEnabled(False)
            self.ButtonStop.setEnabled(False)
            self.rec.stop()
            self.onListTracksIndexChanged()
            self.status = NO_STREAM_RUNNING

    def onButtonRecClicked(self):
        if self.status == NO_STREAM_RUNNING:
            edits = ("Title", "Artist", "Album", "Genre", "Date", "Comment")
            for edit in edits:
                getattr(self, 'LineEdit'+edit).setEnabled(True)
        if self.status in (NO_STREAM_RUNNING, STREAM_PAUSING):
            self.ButtonRec.setIcon(self.iconPause)
            self.ButtonCut.setEnabled(True)
            self.ButtonStop.setEnabled(True)
            self.status = RECORDING
            self.rec.play()
            index = self.RecListModel.getLastItemIndex()
            self.ListTracks.setCurrentIndex(index)
            self.onListTracksIndexChanged()
            self.LineEditTitle.setFocus()
        elif self.status is RECORDING:
            self.status = STREAM_PAUSING
            self.ButtonRec.setIcon(self.iconRec)
            self.rec.pause()

    def onButtonCutClicked(self):
        """stops recording, creates new file and starts recording again"""
        if self.status in (NO_STREAM_RUNNING, RECORDING, STREAM_PAUSING):
            self.rec.cut()
            self.ButtonRec.setIcon(self.iconPause)
            self.status = RECORDING
            index = self.RecListModel.getLastItemIndex()
            self.ListTracks.setCurrentIndex(index)
            self.onListTracksIndexChanged()
            self.LineEditTitle.setFocus()

    def onButtonChangeClicked(self):
        """writes tags to audio files"""
        self.onListTracksIndexChanged()

    def onButtonSaveClicked(self):
        self.RecListModel.update()

    def setStatus(self, message=""):
        """shows the given message in the program statusbar"""
        self.ProgressBar.setValue(0.0)
        self.ProgressBar.show()

    def clearStatus(self):
        """clears the status of the program statusbar"""
        self.ProgressBar.hide()

    def updateProgressBar(self, value):
        self.ProgressBar.setValue(value)

    def updateTime(self):
        if self.rec is not None:
            track_time = self.rec.timer.get_track_time()
            rec_time = self.rec.timer.get_recording_time()
            self.LabelTime.setText(track_time+"/"+rec_time)

    def onListTracksIndexChanged(self):
        """is called when the index in ListTracks has changed

        it saved the old Tags in its corresponding track and loads the
        tags of the new selected track
        """
        # save old Tags if tags have changed
        tags = self.tags()
        tags["tracknumber"] = self.current_track.tags["tracknumber"]
        if self.current_track.tags != tags:
            has_different_albums = self.current_track.tags.album != tags.album
            self.current_track.tags = tags
            if has_different_albums:
                self.rec_manager.set_album(tags.album)
                self.rec_manager.save_tracks()
            else:
                self.current_track.save()
        self.rec_manager.dump(self.proj_file)
        index = self.ListTracks.selectedIndexes()[0]
        self.current_track = self.RecListModel.itemFromIndex(index)
        self.setTags(self.current_track)
        self.RecListModel.update()

    def setTags(self, track):
        """sets the tags of a given track in program window"""
        exclude = set(['date', 'tracknumber'])
        for tag in set(track.tags.keys()).difference(exclude):
            getattr(self, 'LineEdit'+tag.title()).setText(track.tags[tag])
        if track.tags['date'] == "":
            year = datetime.now().year
        else:
            year = int(track.tags['date'])
        self.LineEditDate.setDate(QtCore.QDate(year, 1, 1))

    def tags(self):
        """returns a Tags object with the given tags in program window"""
        tags = core.Tags()
        exclude = set(['date', 'tracknumber'])
        for tag in set(tags.keys()).difference(exclude):
            tags[tag] = str(getattr(self, 'LineEdit'+tag.title()).text())
        tags['date'] = str(self.LineEditDate.date().toPyDate().year)
        return tags

    def openProject(self):
        """open an old project. Recording is not possible"""
        if self.isRunning():
            return
        path = self.settings.path
        caption = self.tr("Open Project")
        file_filter = self.tr("Godirec File (*.gdr)")
        filename = QtWidgets.QFileDialog.getOpenFileName(self, caption, path,
                                                         file_filter)[0]
        if filename != "":
            self.setupProject(filename, False)

    def getSaveFilename(self, path=""):
        basename = "{:%Y_%m_%d}-Godi".format(datetime.today())
        caption = self.tr("Create new project:")
        file_filter = self.tr("Godirec File (*.gdr)")
        # create new project directory if default directory already exists
        for i in range(1000):
            ending = "-" + str(i) if i > 0 else ""
            projectName = "{}{}.gdr".format(basename, ending)
            projectPath = os.path.join(path, projectName)
            if not os.path.exists(projectPath):
                return QtWidgets.QFileDialog.getSaveFileName(self, caption,
                        projectPath, file_filter)[0]

    def createNewProject(self):
        if self.isRunning():
            return
        proj_file = self.getSaveFilename(self.settings.path)
        if proj_file != "":
            self.setupProject(proj_file)

    def setupProject(self, filename, isForRecording=True):
        if hasattr(self, "rec"):
            self.rec.levelUpdated.disconnect()
            self.rec.close()
            delattr(self, "rec")
        self.menuUpload.menuAction().setVisible(True)
        self.enableRecButtons(False)
        self.enableTagEdits(not isForRecording)
        self.updateLevel([0,0])
        if isForRecording:
            current_path = os.path.splitext(filename)[0]
            if not os.path.exists(current_path):
                os.makedirs(current_path)
            self.settings.path = os.path.dirname(current_path)
            self.settings.save()
            self.rec_manager = core.Manager(current_path)
            self.rec = core.Recorder(self.rec_manager, parent=self)
            self.rec.timer.timeout.connect(self.updateTime)
            self.rec.levelUpdated.connect(self.updateLevel)
            f_list = self.settings.formats
            self.rec.format_list = [audio.codec_dict[f] for f in f_list]
            self.ButtonRec.setEnabled(True)
        else:
            self.rec_manager = core.Manager.load_from_file(filename)
            removed_files = self.rec_manager.removed_files
            if len(removed_files) > 0:
                files = set([os.path.dirname(f) for f in removed_files])
                msg = self.tr("File(s) from the following folders could not"
                              " be found:\n{}")
                msg = msg.format("\n".join(files))
                title = self.tr("Files Not Found")
                QMessageBox.information(self, title, msg)
        self.proj_file = filename
        self.RecListModel.set_rec_manager(self.rec_manager)
        self.RecListModel.update()
        if not isForRecording:
            self.ListTracks.setCurrentIndex(self.RecListModel.index(0))
        self.status = NO_STREAM_RUNNING
        self.LabelTime.setText("-- / --")
        self.setWindowTitle(self.rec_manager.project_name)

    def updateLevel(self, levels):
        try:
            self.LeftLevelBar.setValue(levels[0]*100)
            self.RightLevelBar.setValue(levels[1]*100)
        except Exception as e:
            raise e

    def openSettings(self):
        """opens the settings dialog"""
        self.settings_dialog = settings.SettingsDialog(self.settings, self)
        # update word list if settings are accepted
        if self.settings_dialog.exec_():
            self.updateWordList()

    def openAbout(self):
        """opens the About dialog"""
        self.about_dialog = AboutDialog(parent=self)
        self.about_dialog.show()

    def openHelp(self):
        """opens the Help dialog"""
        self.help_dialog = HelpDialog(parent=self)
        self.help_dialog.show()

    def isRunning(self):
        if self.RecListModel.rowCount():
            self.onListTracksIndexChanged()
        if self.status in (RECORDING, STREAM_PAUSING):
            title = self.tr("Stream Closed")
            message = self.tr("To close the program,\n"
                              "you have to close the stream first.")
            QMessageBox.information(self, title, message)
            return True
        elif core.future_pool.has_running_processes():
            title = self.tr("Please Wait")
            message = self.tr("To close the program, you have to close the"
                              " stream first!")
            QMessageBox.information(self, title, message)
            return True
        return False

    def closeEvent(self, event):
        """method is called when close event is emitted"""
        if self.isRunning():
            event.ignore()
            return
        if self.status is NO_STREAM_RUNNING and hasattr(self, "rec"):
            self.rec.stop()
        QtWidgets.QMainWindow.closeEvent(self, event)

    def isNewProjectCreatedDialog(self):
        title = self.tr("Create Project")
        message = self.tr("Do you want to create a new project?")
        reply = QMessageBox.question(
            self, title, message, defaultButton=QMessageBox.Yes)
        return reply == QMessageBox.Yes

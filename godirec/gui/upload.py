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


from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QMessageBox
import godirec
from godirec import uploader
from paramiko import ssh_exception


def start(rec_manager, settings, parent):
    uploader = Uploader(rec_manager, settings, parent=parent)
    uploader.start()


class Uploader(QObject):

    def __init__(self, rec_manager, settings, parent=None):
        QObject.__init__(self, parent=parent)
        self._rec_manager = rec_manager
        self._settings = settings

    @property
    def rec_manager(self):
        return self._rec_manager

    def showErrorMessage(self, error):
        if hasattr(self, "progressDialog"):
            self.progressDialog.close()
        if isinstance(error, uploader.UploadError):
            msg = str(error)
        elif isinstance(error, ssh_exception.AuthenticationException):
            msg = self.tr("Authentification failed.")
        elif isinstance(error, ssh_exception.SSHException):
            msg = str(error)
        elif isinstance(error, FileNotFoundError):
            msg = self.tr("Keyfile not found.")
        elif isinstance(error, EOFError):
            msg = self.tr("Connection aborted.")
        else:
            raise error
        QMessageBox.critical(self.parent(), self.tr("Error"), msg)

    def chooseTrack(self, text, tracks):
        trackChooser = TrackChooserDialog(text, tracks, self.parent())
        if trackChooser.exec_():
            return trackChooser.selectedTrack()
        else:
            return None

    def start(self):
        upload_data = self._settings.upload
        host = upload_data["Host"]
        user = upload_data["User"]
        key_file = upload_data["Keyfile"]
        port = int(upload_data["Port"])
        host_dir = upload_data["UploadDir"]
        track_type = upload_data["Filetype"]
        search = upload_data["Search"]
        album_titel = upload_data["AlbumTitle"]
        if(album_titel == ''):
            album_titel = None
        tracks = self.rec_manager.find_tracks(search)
        if len(tracks) > 1:
            text = self.tr("More than one {} was found.")
            text = text.format(search)
            track = self.chooseTrack(text, tracks)
        elif len(tracks) == 0:
            text = self.tr("No {} was found. Please choose the file.")
            text = text.format(search)
            track = self.chooseTrack(text, self.rec_manager.tracklist)
        else:
            track = tracks[0]
        if track is None:
            return
        try:
            parent = self.parent()
            trackFile = uploader.TrackFile(track, track_type, album_titel,
                                           parent)
            self.progressDialog = ProgressDialog(parent=parent)
            sftp = uploader.SftpThread(host, user, key_file, port, parent)
            sftp.uploadUpdated.connect(self.progressDialog.update)
            sftp.errorExcepted.connect(self.showErrorMessage)
            self.progressDialog.show()
            sftp.upload(trackFile, host_dir)
        except (uploader.UploadError) as error:
            self.showErrorMessage(error)


class ProgressDialog(QtWidgets.QDialog):

    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent=parent)
        ui = godirec.resource_stream("godirec", 'data/ui/progressDialog.ui')
        uic.loadUi(ui, self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.message.setText(self.tr("The sermon gets uploaded"))
        self.okButton = self.okButtonBox.button(QtWidgets.QDialogButtonBox.Ok)
        self.okButton.pressed.connect(self.okButtonPressed)

    def okButtonPressed(self):
        self.close()

    def update(self, value, total):
        progress = value/total*100
        self.progressBar.setValue(progress)
        if round(progress, 2) == 100.00:
            self.setFinished(True)

    def setFinished(self, isFinished):
        self.okButtonBox.setEnabled(True)


class TrackChooserDialog(QtWidgets.QDialog):

    def __init__(self, text, tracks, parent=None):
        QtWidgets.QDialog.__init__(self, parent=parent)
        ui = godirec.resource_stream("godirec", "data/ui/listDialog.ui")
        uic.loadUi(ui, self)
        self._current_track = None
        self._tracklist = TrackListModel(tracks, parent=self)
        self.listView.setModel(self._tracklist)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.message.setText(text)
        self.selection = self.listView.selectionModel()
        self.selection.selectionChanged.connect(self._indexChanged)
        self.listView.setCurrentIndex(self._tracklist.index(0))

    def _indexChanged(self):
        index = self.listView.selectedIndexes()[0]
        self._current_track = self._tracklist.itemFromIndex(index)

    def selectedTrack(self):
        return self._current_track


class TrackListModel(QtCore.QAbstractListModel):

    def __init__(self, tracks, parent=None):
        QtCore.QAbstractListModel.__init__(self, parent)
        self._tracks = tracks

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._tracks)

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            return self._tracks[row].tags.title

    def itemFromIndex(self, index):
        return self._tracks[index.row()]

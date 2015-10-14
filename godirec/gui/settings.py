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


import godirec
import logging
import os
from PyQt5 import QtCore, QtGui, uic, QtWidgets
from PyQt5.QtWidgets import QMessageBox
import copy
from godirec.gui.helper import createIcon
from godirec import core, audio, uploader
from paramiko import ssh_exception


class Store(object):
    """Provides API for storing settings

    Abstraction layer, to use settings like a dict or with . notation.
    Data would be saved temporary and stored in settings after exiting the
    Dialog over the OK Button.

    :param QtSettings settings: QtSettings object
    :param QtWindow dialog: QtWindow object
    """

    def __init__(self, settings, dialog):
        self._slots = ("tags", "formats", "log_dir", "upload", "path")
        self._qtsettings = settings
        self._dialog = dialog
        self._tmp = dict()
        self.load()
        self._fill_tmp()

    def _set_attr(attr):
        def set_any(self, value):
            self._tmp[attr] = value
        return set_any

    def _get_attr(attr):
        def get_attr(self):
            return self._tmp[attr]
        return get_attr

    tags = property(_get_attr("tags"), _set_attr("tags"))
    formats = property(_get_attr("formats"), _set_attr("formats"))
    log_dir = property(_get_attr("log_dir"), _set_attr("log_dir"))
    upload = property(_get_attr("upload"), _set_attr("upload"))
    path = property(_get_attr("path"), _set_attr("path"))

    def _fill_tmp(self):
        for slot in self._slots:
            self._tmp[slot] = copy.deepcopy(getattr(self, "_"+slot))

    def load(self):
        """Loads data from Settings

        Use default data for settings and overwrites them with existing
        settings. The data will be stored in a temporary Structure.
        """
        self._tags = dict()
        exclude = set(["date", "tracknumber"])
        for tag in set(core.Tags().keys()).difference(exclude):
            key = str(getattr(self._dialog, "Label"+tag.title()).text())
            key = key.strip(":")
            self._tags[key] = list()
        self._fill_dict("tags")
        self._upload = {
            "Host" : "",
            "Keyfile" : "",
            "User" : "",
            "Port": "22",
            "UploadDir" : "",
            "AlbumTitle" : "",
            "Filetype" : "",
            "Search": ""
        }
        self._fill_dict("upload")
        if "formats" in self._qtsettings.allKeys():
            self._formats = self._qtsettings.value("formats", type=str)
        else:
            self._formats = list(audio.codec_dict.keys())
        self._log_dir = godirec.get_log_dir()
        self._path = "."
        if "path" in self._qtsettings.allKeys():
            self._path = self._qtsettings.value("path", type=str)

    def _fill_dict(self, attr):
        if not attr in self._qtsettings.allKeys():
            return
        setting = self._qtsettings.value(attr, type="QVariantMap")
        for key, value in setting.items():
            getattr(self, "_"+attr)[key] = value

    def commit(self):
        """Save changes from temporary object to settings object."""
        for slot in self._slots:
            setattr(self, "_"+slot, copy.deepcopy(self._tmp[slot]))

    def reset(self):
        """Discard changes from temporary object."""
        self._fill_tmp()

    def save(self):
        """Save changes from temporary object to disk.

        To discard changes from temp use: :func:'reset'
        """
        self.commit()
        for value in ("formats", "tags", "upload"):
            self._qtsettings.setValue(value, self[value])
        self._qtsettings.setValue("path", self.path)
        godirec.change_log_dir(self.log_dir, godirec.config_file)

    def keys(self):
        """return a list of available tag names"""
        return list(self.__slots__)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)


class SettingsDialog(QtWidgets.QDialog):
    """Show data on GUI and provides all functions for GUI.

    :param QtSettings settings: QtSettings object
    :param QtWindow parent: QtQbject which owns the instance of SettingsDialog
    """
    TABS = ["ExportSettings", "Autocompletion", "LogFile", "Upload"]

    def __init__(self, settings, parent):
        QtWidgets.QDialog.__init__(self, parent=parent)
        self.settings = settings
        settings_ui_file = godirec.resource_stream("godirec",
                                                   'data/ui/settings.ui')
        uic.loadUi(settings_ui_file, self)
        self.setWindowIcon(createIcon('data/ui/settings.png'))
        self.accepted.connect(self.settings.save)
        self.rejected.connect(self.settings.reset)
        self.tabWidget.currentChanged.connect(self.tabChanged)
        self.supported_filetypes = sorted(audio.codec_dict.keys())
        # init ExportSettings
        for filetype in self.supported_filetypes:
            checkbox = QtWidgets.QCheckBox(filetype.upper())
            checkbox.clicked.connect(self.checkBoxesChanged)
            setattr(self, "CheckBox"+filetype.title(), checkbox)
            self.VLayoutFiletypes.addWidget(checkbox)
        self.VLayoutFiletypes.addStretch()
        # init Autocompletion
        for key in self.settings.tags:
            self.comboBox.addItem(key)
        self.comboBox.activated[str].connect(self.comboBoxChanged)
        self.pushButtonAdd.clicked.connect(self.addTag)
        self.pushButtonDir.clicked.connect(self.onButtonDirClicked)
        self.pushButtonDelete.clicked.connect(self.deleteTag)
        self.comboBoxChanged(str(self.comboBox.currentText()))
        # init LogFile
        self.pushButtonDir.setIcon(createIcon('data/ui/folder-yellow.png'))
        # init Upload
        self.pushButtonDirKey.setIcon(createIcon('data/ui/folder-yellow.png'))
        self.comboBoxFiletype.currentIndexChanged.connect(
                                                   self.updateUploadFiletype)
        self.spinBoxPort.valueChanged.connect(self.updateUploadPort)
        self.pushButtonTest.clicked.connect(self.testConnection)
        self.pushButtonDirKey.clicked.connect(self.selectKey)
        self.tabChanged(0)

    def selectKey(self):
        """Open Dialog to select Key file."""
        title = self.tr("Choose Keyfile")
        directory = os.path.dirname(self.settings.upload["Keyfile"])
        keyfile = QtWidgets.QFileDialog.getOpenFileName(self, title, directory)
        keyfile = keyfile[0]
        if keyfile:
            self.lineEditKeyfile.setText(keyfile)
            self.settings.upload["Keyfile"] = keyfile

    def testConnection(self):
        """Test sftp connection with data from GUI. Open dialog with result"""
        upload_data = self.settings.upload
        host = upload_data["Host"]
        user = upload_data["User"]
        key_file = upload_data["Keyfile"]
        host_dir = upload_data["UploadDir"]
        port = int(upload_data["Port"])
        host_dir = None if host_dir == "" else host_dir
        msg = self.tr("A connection could be established")
        title = self.tr("Success")
        show_msg = lambda : QMessageBox.information(self, title, msg)
        sftp = uploader.SftpThread(host, user, key_file, port, parent=self)
        sftp.succeeded.connect(show_msg)
        sftp.errorExcepted.connect(self.showErrorMessage)
        sftp.test_connection(host_dir)

    def showErrorMessage(self, error):
        """Reports errors in uploading process.

        Error will shown for:
        * UploadError
        * AuthenticationException
        * FileNotFoundError: Keyfile
        """
        if isinstance(error, (uploader.UploadError,
                      ssh_exception.SSHException)):
            msg = str(error)
        elif isinstance(error, ssh_exception.AuthenticationException):
            msg = self.tr("Authentification failed.")
        elif isinstance(error, FileNotFoundError):
            msg = self.tr("Keyfile not found.")
        else:
            raise error
        QMessageBox.information(self, self.tr("Error"), msg)

    def tabChanged(self, index):
        """When Tab changed load function for this tab will be executed"""
        getattr(self, "load"+self.TABS[index])()

    def loadExportSettings(self):
        self.updateCheckBoxes()

    def loadAutocompletion(self):
        pass

    def loadLogFile(self):
        self.labelPath.setText(godirec.get_log_dir())

    def loadUpload(self):
        """Loads filetypes to be consistent with the settings

        Shuld be execuded when tab changed to upload tab.
        """
        filetype = self.settings.upload["Filetype"]
        port = int(self.settings.upload["Port"])
        self.spinBoxPort.setValue(port)
        for entry, value in self.settings.upload.items():
            if(entry not in ("Filetype", "Port")):
                lineEdit = getattr(self, 'lineEdit'+entry)
                lineEdit.setText(value)
                lineEdit.textChanged.connect(self.updateUpload)
        self.comboBoxFiletype.clear()
        self.comboBoxFiletype.addItems(self.settings.formats)
        index = self.comboBoxFiletype.findText(filetype)
        if index < 0:
            index = 0
        self.comboBoxFiletype.setCurrentIndex(index)

    def comboBoxChanged(self, key):
        """Updates ListView with autocompletion items for Key

        Gets key from changed comboBox and updates ListView with according
        Items

        :param str key: Key value for tags in Settings.tags
        """
        self.model = QtGui.QStandardItemModel(self.listView)
        values = self.settings.tags[key]
        values.sort()
        for value in values:
            item = QtGui.QStandardItem(value)
            item.setCheckable(True)
            self.model.appendRow(item)
        self.listView.setModel(self.model)
        self.pushButtonDelete.setEnabled(bool(values))

    def updateUploadPort(self, value):
        """Stores port in temp settings"""
        self.settings.upload["Port"] = value

    def updateUploadFiletype(self, index):
        """Stores selected filetype in temp settings"""
        value = self.comboBoxFiletype.itemText(index)
        self.settings.upload["Filetype"] = value

    def updateUpload(self):
        """Stroes data from Upload tab in temp settings"""
        for entry in self.settings.upload:
            if entry != "Filetype":
                value = getattr(self, 'lineEdit'+entry).text()
                self.settings.upload[entry] = value

    def onButtonDirClicked(self):
        """opens log FileDialog"""
        temp_path = QtWidgets.QFileDialog.getExistingDirectory(
            self, self.tr("Create Logfile In"), self.labelPath.text())
        if temp_path:
            self.labelPath.setText(temp_path)
            self.settings.log_dir = temp_path

    def addTag(self):
        """Add Tag to autocompletion List by key"""
        value = str(self.lineEditAdd.text())
        if value:
            key = str(self.comboBox.currentText())
            self.settings.tags[key].append(value)
            self.comboBoxChanged(key)
            self.pushButtonDelete.setEnabled(True)
            self.lineEditAdd.setText("")
            logging.info("Add Tag {} to {}".format(value, key))

    def deleteTag(self):
        """Removes Tag from autocompletion list by key"""
        offset = 0
        model = self.listView.model()
        key = str(self.comboBox.currentText())
        for row in range(model.rowCount()):
            item = model.item(row)
            if item.checkState() == QtCore.Qt.Checked:
                value = self.settings.tags[key].pop(row-offset)
                logging.info("Delete Tag {} from {}".format(value, key))
                offset += 1
        if model.rowCount() == 0:
            self.pushButtonDelete.setEnabled(False)
        self.comboBoxChanged(key)

    def updateCheckBoxes(self):
        """Sets checkBoxes for Filetype checked, if they in
        supported_filetypes"""
        for filetype in self.supported_filetypes:
            checkbox = getattr(self, 'CheckBox'+filetype.title())
            if filetype in self.settings.formats:
                checkbox.setCheckState(QtCore.Qt.Checked)
            else:
                checkbox.setCheckState(QtCore.Qt.Unchecked)

    def checkBoxesChanged(self):
        """Stores export types in temp settings"""
        self.formats = list()
        for filetype in self.supported_filetypes:
            checkbox = getattr(self, 'CheckBox'+filetype.title())
            if checkbox.checkState() == QtCore.Qt.Checked:
                self.formats.append(filetype)
        self.settings.formats = self.formats
        logging.info("Changed Exportfile formats")

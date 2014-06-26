# -*- coding: utf-8 -*-
import sys
import os
import traceback
import multiprocessing
from datetime import datetime
from PyQt4 import QtCore, QtGui, uic
import logging
import godirec
from godirec import core


class RecorderListModel(QtCore.QAbstractListModel): 

    def __init__(self, rec_manager=core.Manager(""), parent=None): 
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

    def getLastItemIndex(self):
        return self.index(len(self.rec_manager.tracklist)-1)


class SettingsDialog(QtGui.QDialog):

    def __init__(self, settings, parent):
        QtGui.QDialog.__init__(self, parent=parent)
        self.settings = settings
        settings_ui_file = godirec.resource_stream(__name__,
                                                   'data/ui/settings.ui')
        uic.loadUi(settings_ui_file, self)
        self.supported_filetypes = ['mp3', 'flac', 'ogg', 'wav']
        for filetype in self.supported_filetypes:
            checkbox = QtGui.QCheckBox(filetype.upper())
            setattr(self, "CheckBox"+filetype.title(), checkbox)
            self.VLayoutFiletypes.addWidget(checkbox)
        self.VLayoutFiletypes.addStretch()
        # Load Tags
        if 'tags' in self.settings.allKeys():
            self.tags = self.settings.value('tags', type='QVariantMap')
        else:
            self.tags = dict()
            for tag in set(core.Tags().keys()).difference(set(['date'])):
                key = str(getattr(parent, 'Label'+tag.title()).text())[:-1]
                self.tags[key] = list()
        for key in self.tags:
            self.comboBox.addItem(key)
        # Load FileFormats
        if 'formats' in self.settings.allKeys():
            self.formats = self.settings.value('formats', type=str)
        else:
            self.formats = list()
        for filetype in self.supported_filetypes:
            checkbox = getattr(self, 'CheckBox'+filetype.title())
            checkbox.clicked.connect(self.checkBoxesChanged)
        self.updateCheckBoxes()
        self.comboBox.activated[str].connect(self.comboBoxChanged)
        self.pushButtonAdd.clicked.connect(self.addTag)
        self.pushButtonDelete.clicked.connect(self.deleteTag)
        self.comboBoxChanged(str(self.comboBox.currentText()))

    def comboBoxChanged(self, key):
        self.model = QtGui.QStandardItemModel(self.listView)
        values = self.tags[key]
        values.sort()
        for value in values:
            item = QtGui.QStandardItem(value)
            item.setCheckable(True)
            self.model.appendRow(item)
        self.listView.setModel(self.model)
        self.pushButtonDelete.setEnabled(bool(values))

    def addTag(self):
        value = str(self.lineEditAdd.text())
        if value:
            key = str(self.comboBox.currentText())
            self.tags[key].append(value)
            self.comboBoxChanged(key)
            self.pushButtonDelete.setEnabled(True)
            self.lineEditAdd.setText("")
            self.settings.setValue('tags', self.tags)
            logging.info("Add Tag {} to {}".format(value, key))

    def deleteTag(self):
        model = self.listView.model()
        key = str(self.comboBox.currentText())
        for row in range(model.rowCount()):
            item = model.item(row)
            if item.checkState() == QtCore.Qt.Checked:
                value = self.tags[key].pop(row)
                logging.info("Delete Tag {} from {}".format(value, key))
        if model.rowCount() == 0:
            self.pushButtonDelete.setEnabled(False)
        self.settings.setValue('tags', self.tags)
        self.comboBoxChanged(key)

    def updateCheckBoxes(self):
        for filetype in self.supported_filetypes:
            checkbox = getattr(self, 'CheckBox'+filetype.title())
            if filetype in self.formats:
                checkbox.setCheckState(QtCore.Qt.Checked)
            else:
                checkbox.setCheckState(QtCore.Qt.Unchecked)

    def checkBoxesChanged(self):
        self.formats = list()
        for filetype in self.supported_filetypes:
            checkbox = getattr(self, 'CheckBox'+filetype.title())
            if checkbox.checkState() == QtCore.Qt.Checked:
                self.formats.append(filetype)
        self.settings.setValue('formats', self.formats)
        logging.info("Changed Exportfile formats")
                

class PathDialog(QtGui.QDialog):
    """ Path Dialog will ask for workspace path and project name. If path
        doesn't exist it will be created"""

    def __init__(self, path=""):
        QtGui.QDialog.__init__(self)
        dialog_ui_file = godirec.resource_stream(__name__, 'data/ui/dialog.ui')
        uic.loadUi(dialog_ui_file, self)
        self.cur_path1 = ""
        for i in ("Dir", "Create"):
            getattr(self, "Button"+i).clicked.connect(
                    getattr(self, "onButton{}Clicked".format(i)))
        projectName = "{:%Y_%m_%d}-Godi".format(datetime.today())
        # create new project directory if default directory already exists
        i = 0
        projectPath = os.path.join(path, projectName)
        while os.path.exists(projectPath):
            i += 1
            projectName = "{:%Y_%m_%d}-Godi-{}".format(datetime.today(), i)
            projectPath = os.path.join(path, projectName)
        self.LineEditProjekt.setText(projectName)
        self.LineEditPath.setText(path)
        self.iconDir = createIcon('data/ui/folder-yellow.png')
        self.ButtonDir.setIcon(self.iconDir)
        self.ButtonCreate.setFocus()

    def onButtonDirClicked(self):
        """ opens project FileDialog"""
        temp_path = QtGui.QFileDialog.getExistingDirectory(
            self,"Neues Projekt erzeugen in:",".")
        self.LineEditPath.setText(temp_path)

    def onButtonCreateClicked(self):
        """ closes PathDialog window and creates necessery directories"""
        temp_path = str(self.LineEditPath.text())
        projectName = str(self.LineEditProjekt.text())
        self.cur_path1 = os.path.join(temp_path, projectName)
        if not os.path.exists(self.cur_path1):
            os.makedirs(self.cur_path1)
        self.close()

    def getValues(self):
        """ returns project folder"""
        return str(self.cur_path1)


NO_STREAM_RUNNING = "no stream is running"
NO_PROJECT = "no project opened"
RECORDING = "currently recording"

class GodiRecWindow(QtGui.QMainWindow):

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        godi_rec_ui = godirec.resource_stream(__name__, 'data/ui/godi_rec.ui')
        uic.loadUi(godi_rec_ui, self)
        self.RecListModel = RecorderListModel(parent=self)
        self.ListTracks.setModel(self.RecListModel)
        self.ListTracks.clicked.connect(self.onListTracksIndexChanged)
        self.settings = QtCore.QSettings("EFG Aachen", "GodiRec")
        for i in ("Stop", "Rec", "Cut"):
            getattr(self, "Button"+i).clicked.connect(
                    getattr(self, "onButton{}Clicked".format(i)))
            getattr(self, "Button"+i).setEnabled(False)
        self.ActionExit.triggered.connect(self.closeEvent)
        self.ActionNewProject.triggered.connect(self.createNewProject)
        self.ActionSettings.triggered.connect(self.openSettings)
        # Status: NO_STREAM_RUNNING, NO_PROJECT, RECORDING
        self.status = NO_PROJECT
        self.setIcons()
        self.updateWordList()
        self.iconPause = createIcon('data/ui/pause10.png')
        self.iconRec = createIcon('data/ui/record6.png')
        self.setWindowIcon(createIcon('data/ui/microphone2.ico'))
        self.current_track = core.Track("")
        self.cur_path = ""
        logging.info('GUI loaded')

    def updateWordList(self):
        if 'tags' in self.settings.allKeys():
            tags = self.settings.value('tags', type='QVariantMap')
            for key in tags:
                completer = QtGui.QCompleter(tags[key], self)
                if key == 'Titel':
                    getattr(self, 'LineEditTitle').setCompleter(completer)
                else:
                    getattr(self, 'LineEdit'+key).setCompleter(completer)

    def setIcons(self):
        """ This function is used as workaround for not loading icons in
            python generated ui code"""
        icons = {"Stop": "media26.png", "Rec": "record6.png", 
                 "Cut": "cutting.png"}
        for i, img in icons.items():
            icon = createIcon('data/ui/{}'.format(img))
            getattr(self, "Button"+i).setIcon(icon)
        
    def onButtonStopClicked(self):
        if self.status in (NO_STREAM_RUNNING, RECORDING):
            self.ButtonRec.setIcon(self.iconRec)
            self.ButtonCut.setEnabled(False)
            self.ButtonStop.setEnabled(False)
            self.rec.stop()
            self.onListTracksIndexChanged()
            self.status = NO_STREAM_RUNNING

    def onButtonRecClicked(self):
        if self.status is NO_STREAM_RUNNING:
            self.ButtonRec.setIcon(self.iconPause)
            self.ButtonCut.setEnabled(True)
            self.ButtonStop.setEnabled(True)
            self.status = RECORDING
            self.rec.play()
            index = self.RecListModel.getLastItemIndex()
            self.ListTracks.setCurrentIndex(index)
            self.onListTracksIndexChanged()
        elif self.status is RECORDING:
            self.status = NO_STREAM_RUNNING
            self.ButtonRec.setIcon(self.iconRec)
            self.rec.pause()

    def onButtonCutClicked(self):
        """ Erzeugt neue Datei und nimmt weiter auf"""
        if self.status in (NO_STREAM_RUNNING, RECORDING):
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
        tags = core.Tags()
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
        self.rec_manager = core.Manager(self.cur_path)
        self.rec = core.Recorder(self.rec_manager)
        if 'formats' in self.settings.allKeys():
            self.rec.format_list = self.settings.value('formats', type=str)
        self.rec.timer.set_callback(self.updateTime)
        self.RecListModel.set_rec_manager(self.rec_manager)
        self.status = NO_STREAM_RUNNING
        self.ButtonRec.setEnabled(True)

    def openSettings(self):
        self.settings_dialog = SettingsDialog(self.settings, self)
        self.settings_dialog.show()
        self.settings_dialog.exec_()
        self.updateWordList()

    def closeEvent(self, event=None):
        if self.status in (NO_STREAM_RUNNING, RECORDING):
            self.rec.stop()
        QtGui.QMainWindow.closeEvent(self, event)


def createIcon(pixmap):
    icon = QtGui.QIcon()
    pmap = QtGui.QPixmap()
    png_str = godirec.resource_string(__name__, pixmap)
    pmap.loadFromData(png_str)
    icon.addPixmap(pmap)
    return icon


def handle_exception(exc_type, exc_value, exc_traceback):
    """ handle all exceptions """
    # KeyboardInterrupt is a special case.
    # We don't raise the error dialog when it occurs.
    if issubclass(exc_type, KeyboardInterrupt):
        if QtGui.qApp:
            QtGui.qApp.quit()
        return
    filename, line, _, _ = traceback.extract_tb(exc_traceback).pop()
    filename = os.path.basename(filename)
    error = "{}: {}".format(exc_type.__name__, exc_value)
    QtGui.QMessageBox.critical(
        None, "Error",
        ("<html>A critical error has occured.<br/> "
        "<b>{:s}</b><br/><br/>"
        "It occurred at <b>line {:d}</b> of file <b>{:s}</b>.<br/>"
        "For more information see error log file"
        "</html>").format(error, line, filename)
    )
    logging.error(
        "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    )
    sys.exit(1)


def run():
    sys.excepthook = handle_exception
    multiprocessing.freeze_support()
    app = QtGui.QApplication(sys.argv)
    QtCore.QObject.connect(app, QtCore.SIGNAL("lastWindowClosed()"), app,
                           QtCore.SLOT("quit()"))
    window = GodiRecWindow()
    window.show()
    sys.exit(app.exec_())

# -*- coding: utf-8 -*-
import sys
import os
import traceback
import multiprocessing
from datetime import datetime
from PyQt4 import QtCore, QtGui, uic
import logging
import queue
import godirec
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

    def __init__(self, rec_manager=core.Manager(""), parent=None):
        QtCore.QAbstractListModel.__init__(self, parent)
        self.signals = SignalThread(self)
        self.set_rec_manager(rec_manager)

    def set_rec_manager(self, rec_manager):
        self.rec_manager = rec_manager
        self.rec_manager.set_callback(self.signals.signal(), "layoutChanged")

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.rec_manager.tracklist)

    def data(self, index, role):
        if index.isValid() and role == QtCore.Qt.DisplayRole:
            track = self.rec_manager.get_track(index.row())
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


class SettingsDialog(QtGui.QDialog):

    def __init__(self, settings, parent):
        QtGui.QDialog.__init__(self, parent=parent)
        self.settings = settings
        self._settings_dict = {}
        settings_ui_file = godirec.resource_stream(__name__,
                                                   'data/ui/settings.ui')
        uic.loadUi(settings_ui_file, self)
        self.supported_filetypes = sorted(audio.codec_dict.keys())
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
            exclude = set(['date', 'tracknumber'])
            for tag in set(core.Tags().keys()).difference(exclude):
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
        self.pushButtonDir.clicked.connect(self.onButtonDirClicked)
        self.pushButtonDelete.clicked.connect(self.deleteTag)
        self.comboBoxChanged(str(self.comboBox.currentText()))
        # Load log filename
        self.labelPath.setText(godirec.get_log_dir())

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
        
    def onButtonDirClicked(self):
        """opens log FileDialog"""
        temp_path = QtGui.QFileDialog.getExistingDirectory(
            self, self.tr("Logfile erzeugen in:"), self.labelPath.text())
        if temp_path:
            self.labelPath.setText(temp_path)
            self._settings_dict["log_dir"] = temp_path

    def addTag(self):
        value = str(self.lineEditAdd.text())
        if value:
            key = str(self.comboBox.currentText())
            self.tags[key].append(value)
            self.comboBoxChanged(key)
            self.pushButtonDelete.setEnabled(True)
            self.lineEditAdd.setText("")
            self._settings_dict["tags"] = self.tags
            logging.info("Add Tag {} to {}".format(value, key))

    def deleteTag(self):
        offset = 0
        model = self.listView.model()
        key = str(self.comboBox.currentText())
        for row in range(model.rowCount()):
            item = model.item(row)
            if item.checkState() == QtCore.Qt.Checked:
                value = self.tags[key].pop(row-offset)
                logging.info("Delete Tag {} from {}".format(value, key))
                offset += 1
        if model.rowCount() == 0:
            self.pushButtonDelete.setEnabled(False)
        self._settings_dict["tags"] = self.tags
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
        self._settings_dict["formats"] = self.formats
        logging.info("Changed Exportfile formats")

    def values(self):
        """returns dict which contains changed settings"""
        return self._settings_dict


class PathDialog(QtGui.QDialog):
    """Path Dialog will ask for workspace path and project name.

    If path doesn't exist it will be created
    """

    def __init__(self, path=""):
        QtGui.QDialog.__init__(self)
        dialog_ui_file = godirec.resource_stream(__name__, 'data/ui/dialog.ui')
        uic.loadUi(dialog_ui_file, self)
        self.cur_path = ""
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
        """opens project FileDialog"""
        temp_path = QtGui.QFileDialog.getExistingDirectory(
            self, self.tr("Neues Projekt erzeugen in:"), ".")
        self.LineEditPath.setText(temp_path)

    def onButtonCreateClicked(self):
        """closes PathDialog window and creates necessery directories"""
        temp_path = str(self.LineEditPath.text())
        projectName = str(self.LineEditProjekt.text())
        self.cur_path = os.path.join(temp_path, projectName)
        if not os.path.exists(self.cur_path):
            os.makedirs(self.cur_path)
        self.close()

    def values(self):
        """returns project folder"""
        return str(self.cur_path)


NO_STREAM_RUNNING = "no stream is running"
NO_PROJECT = "no project opened"
RECORDING = "currently recording"
STREAM_PAUSING = "currently pausing"


class GodiRecWindow(QtGui.QMainWindow):

    statusSet = QtCore.pyqtSignal()
    statusClear = QtCore.pyqtSignal()
    timeUpdate = QtCore.pyqtSignal(core.Timer)
    progressUpdate = QtCore.pyqtSignal(float)

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        godi_rec_ui = godirec.resource_stream(__name__, 'data/ui/godi_rec.ui')
        uic.loadUi(godi_rec_ui, self)
        self.signals = SignalThread(self)
        self.RecListModel = RecorderListModel(parent=self)
        self.ListTracks.setModel(self.RecListModel)
        self.ListTracks.clicked.connect(self.onListTracksIndexChanged)
        self.settings = QtCore.QSettings("EFG Aachen", "GodiRec")
        for i in ("Stop", "Rec", "Cut"):
            getattr(self, "Button"+i).clicked.connect(
                getattr(self, "onButton{}Clicked".format(i)))
            getattr(self, "Button"+i).setEnabled(False)
        self.ActionExit.triggered.connect(self.close)
        self.ActionNewProject.triggered.connect(self.createNewProject)
        self.ActionSettings.triggered.connect(self.openSettings)
        # Status: NO_STREAM_RUNNING, NO_PROJECT, RECORDING
        self.status = NO_PROJECT
        self.setIcons()
        self.updateWordList()
        self.iconPause = createIcon('data/ui/pause10.png')
        self.iconRec = createIcon('data/ui/record6.png')
        self.setWindowIcon(createIcon('data/ui/microphone2.ico'))
        self.current_track = core.Track("", "")
        self.cur_path = ""
        self.ProgressBar = QtGui.QProgressBar()
        self.statusbar.addWidget(self.ProgressBar, 1)
        self.ProgressBar.hide()
        # connect status for statusbar
        self.statusSet.connect(self.setStatus)
        self.statusClear.connect(self.clearStatus)
        self.timeUpdate.connect(self.updateTime)
        self.progressUpdate.connect(self.updateProgressBar)
        core.future_pool.set_start_callback(self.signals.signal(), "statusSet")
        core.future_pool.set_done_callback(self.signals.signal(),
                                           "statusClear")
        audio.WaveConverter.set_progress_callback(self.signals.signal(),
                                                  "progressUpdate")
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

    def updateTime(self, timer):
        if self.rec is not None:
            track_time = timer.get_track_time()
            rec_time = timer.get_recording_time()
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

    def createNewProject(self):
        # path_dialog muss eine Variable von self sein. Andernfalls wird das
        # Fenster nach Ausfuehrung direkt wieder zerstoert.
        path = ""
        if 'path' in self.settings.allKeys():
            path = self.settings.value('path', type=str)
        self.path_dialog = PathDialog(path)
        self.path_dialog.show()
        self.path_dialog.exec_()
        current_path = self.path_dialog.values()
        if current_path != "":
            self.cur_path = self.path_dialog.values()
            self.settings.setValue('path', os.path.dirname(current_path))
            self.setWindowTitle(os.path.basename(current_path))
            self.rec_manager = core.Manager(current_path)
            self.rec = core.Recorder(self.rec_manager)
            if 'formats' in self.settings.allKeys():
                f_list = self.settings.value('formats', type=str)
                self.rec.format_list = [audio.codec_dict[f] for f in f_list]
            self.rec.timer.set_callback(self.signals.signal(), "timeUpdate")
            self.RecListModel.set_rec_manager(self.rec_manager)
            self.status = NO_STREAM_RUNNING
            self.ButtonRec.setEnabled(True)

    def openSettings(self):
        """opens the settings dialog"""
        self.settings_dialog = SettingsDialog(self.settings, self)
        self.settings_dialog.show()
        # get settings and save if ok
        if self.settings_dialog.exec_():
            settings = self.settings_dialog.values()
            if "formats" in settings:
                self.settings.setValue("formats", settings["formats"])
            if "tags" in settings:
                self.settings.setValue("tags", settings["tags"])
            if "log_dir" in settings:
                godirec.change_log_dir(settings["log_dir"],
                                       godirec.config_file)
        self.updateWordList()

    def closeEvent(self, event):
        """method is called when close event is emitted"""
        if self.RecListModel.rowCount():
            self.onListTracksIndexChanged()
        if self.status in (RECORDING, STREAM_PAUSING):
            title = self.tr("Stream beenden")
            message = self.tr("Um das Programm zu schließen,\n"
                              "müssen sie zuerst den Stream beenden")
            QtGui.QMessageBox.information(self, title, message)
            event.ignore()
            return
        elif core.future_pool.has_running_processes():
            title = "Bitte warten"
            message = self.tr("Die Tracks müssen erst fertig konvertiert "
                              "sein, bevor das Programm geschlossen werden "
                              "kann!")
            QtGui.QMessageBox.information(self, title, message)
            event.ignore()
            return
        if self.status is NO_STREAM_RUNNING:
            self.rec.stop()
        QtGui.QMainWindow.closeEvent(self, event)


def createIcon(pixmap):
    """creates a Qt-icon from an pixmap

    this function look up the given pixmap in its own resources. Icons
    outside of the godirec project can not be loaded with this function
    """
    icon = QtGui.QIcon()
    pmap = QtGui.QPixmap()
    png_str = godirec.resource_string(__name__, pixmap)
    pmap.loadFromData(png_str)
    icon.addPixmap(pmap)
    return icon


def handle_exception(exc_type, exc_value, exc_traceback):
    """handle all exceptions

    exceptions will be caught by this function. The error will be shown
    in a message box to the user and logged to the configured file.
    """
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
    """start GUI

    The function will create the main thread for Qt Gui. It will set the
    language to system locals an start an instance of the main window.
    """
    sys.excepthook = handle_exception
    multiprocessing.freeze_support()
    app = QtGui.QApplication(sys.argv)
    # set translation language
    locale = QtCore.QLocale.system().name()
    translator = QtCore.QTranslator()
    folder = godirec.resource_filename(__name__, 'data/language')
    if translator.load("godirec_{}".format(locale), folder):
        app.installTranslator(translator)
    QtCore.QObject.connect(app, QtCore.SIGNAL("lastWindowClosed()"), app,
                           QtCore.SLOT("quit()"))
    window = GodiRecWindow()
    window.show()
    sys.exit(app.exec_())

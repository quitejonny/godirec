import pysftp
import json
import os
from datetime import datetime
import re
import godirec
import mutagen
import copy
from contextlib import contextmanager
import tempfile
import shutil
from godirec import core
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from paramiko import ssh_exception
import time
import logging


class SftpThread(QThread):

    uploadUpdated = pyqtSignal(int, int)
    errorExcepted = pyqtSignal(Exception)
    succeeded = pyqtSignal()
    timerStopped = pyqtSignal()
    timerStarted = pyqtSignal(float)

    def __init__(self, host, user, key_file, parent=None):
        QThread.__init__(self, parent=parent)
        self._conn_params = {
            "username": user,
            "host": host,
            "private_key": key_file
        }
        self.timeout = 1.0
        self.timerStopped.connect(self._stopTimer)
        self.timerStarted.connect(self._startTimer)
        self._timerId = None

    def _stopTimer(self):
        timerId = self._timerId
        if timerId is not None:
            self._timerId = None
            self.killTimer(timerId)

    def _startTimer(self, timeout):
        self._timerId = self.startTimer(timeout*1000)

    def upload(self, track_file, host_folder):
        self._host_folder = host_folder
        self._host_path = os.path.join(host_folder, track_file.basename)
        self._track_file = track_file
        self.run = self._run_upload
        self.start()

    def test_connection(self, host_dir=None):
        self._host_folder = host_dir
        self.run = self._run_test
        self.start()

    def _put(self, src_file, host_path):
        self.timerStarted.emit(self.timeout)
        with pysftp.Connection(**self._conn_params) as sftp:
            self.timerStopped.emit()
            if not sftp.exists(self._host_folder):
                err_msg = self.tr("Folder does not exist on host!")
                raise UploadFolderError(err_msg)
            if sftp.exists(self._host_path):
                raise UploadFileExistsError(self.tr("File exists on host!"))
            sftp.put(src_file, host_path, callback=self.uploadUpdated.emit)

    def timerEvent(self, event):
        self.killTimer(self._timerId)
        self.terminate()
        err_msg = self.tr("Connection could not be established")
        self.errorExcepted.emit(UploadConnectionError(err_msg))

    def _run_upload(self):
        try:
            with self._track_file.filename() as src_file:
                self._put(src_file, self._host_path)
        except (UploadError, FileNotFoundError,
                ssh_exception.SSHException) as e:
            self.timerStopped.emit()
            # short time for other msg_box to fully build
            time.sleep(0.05)
            self.errorExcepted.emit(e)
        self.succeeded.emit()

    def _run_test(self):
        try:
            self.timerStarted.emit(self.timeout)
            with pysftp.Connection(**self._conn_params) as sftp:
                self.timerStopped.emit()
                use_folder = self._host_folder is not None
                if use_folder and not sftp.exists(self._host_folder):
                    err_msg = self.tr("Folder does not exist on host!")
                    raise UploadFolderError(err_msg)
        except (UploadError, FileNotFoundError,
                ssh_exception.SSHException) as e:
            self.timerStopped.emit()
            self.errorExcepted.emit(e)
            return
        self.succeeded.emit()


class TrackFile(QObject):

    uploadUpdated = pyqtSignal(int, int)

    def __init__(self, track, filetype, album=None, parent=None):
        QObject.__init__(self, parent=parent)
        self._tags = track.tags
        self._filetype = filetype
        self._file = self._get_file(track)
        self.album = album

    def _get_file(self, track):
        for filename in track.files:
            folder = os.path.basename(os.path.dirname(filename))
            if folder.startswith(self._filetype):
                return filename
        else:
            err_msg = self.tr('filetype "{}" not in track')
            raise UploadFiletypeError(err_msg.format(self._filetype))

    @property
    def album(self):
        if self._album is None:
            return self._tags.album
        return self._album

    @album.setter
    def album(self, value):
        self._album = value

    @property
    def is_ready(self):
        return self._tags.comment != ""

    @property
    def creation_date(self):
        date = datetime.fromtimestamp(os.path.getctime(self._file))
        return date.strftime("%Y-%m-%d")

    @property
    def basename(self):
        value = re.sub('[!@#$§"\*|~%&/=°^´`+<>(){}]', '_', self._tags.title)
        return "{} {}.{}".format(self.creation_date, value, self._filetype)

    @contextmanager
    def filename(self, album=None):
        if not self.is_ready:
            raise UploadCommentError(self.tr("Track has no comment!"))
        # create temporary file
        tmp_file = tempfile.mkstemp()[1]
        shutil.copyfile(self._file, tmp_file)
        tags = copy.deepcopy(self._tags)
        album = album if album is not None else self.album
        if album is not None:
            tags.album = album
            core.Track.save_tags_for_file(tmp_file, tags, self._filetype)
        yield tmp_file
        # delete temporary file
        try:
            os.remove(tmp_file)
        except PermissionError as e:
            logging.info('Could not delete temp file "{}"'.format(tmp_file))


class UploadError(Exception):
    pass


class UploadCommentError(UploadError):
    pass


class UploadFileExistsError(UploadError):
    pass


class UploadConnectionError(UploadError):
    pass


class UploadFolderError(UploadError):
    pass


class UploadFiletypeError(UploadError):
    pass

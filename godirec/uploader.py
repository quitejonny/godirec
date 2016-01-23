import pysftp
import json
import os
from datetime import datetime
import re
import getpass
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
    """Run SFTP connection in its own Qt Thread

    class may be used for sftp operation which last longer and must not block
    the main application

    :param str host: The hostname or ip of the remote machine
    :param str user: Username to log into remote machine
    :param str key_file: Path to keyfile for login on remote machine
    :param QObject parent: Qt Object which owns the SftpThread instance
    """

    uploadUpdated = pyqtSignal(int, int)
    errorExcepted = pyqtSignal(Exception)
    succeeded = pyqtSignal()
    timerStopped = pyqtSignal()
    timerStarted = pyqtSignal(float)

    def __init__(self, host, user, key_file, port=22, parent=None):
        QThread.__init__(self, parent=parent)
        self._conn_params = {
            "username": user if user else getpass.getuser(),
            "host": host,
            "port": port,
            "private_key": key_file
        }
        self.timeout = 5.0
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
        """upload file to directory on host"""
        self._host_folder = host_folder
        # use "/" instead of os.path.join, so the path is right on a linux
        # server system even if you run godirec on a windows machine.
        self._host_path = "/".join([host_folder, track_file.basename])
        self._track_file = track_file
        self.run = self._run_upload
        self.start()

    def test_connection(self, host_dir=None):
        """test if connection to host is esablished

        you have to connect to "succeeded"  and "errorExcepted" signal to get
        feedback from this function
        """
        self._host_folder = host_dir
        self.run = self._run_test
        self.start()

    def has_file_on_host(self, sftp, host_path):
        """checks if the file exists on host

        returns True if the filename exists on host, or the modify date and
        filesize are (almost) the same

        :param pysftp.Connection sftp: open connection object from pysftp
        :param str host_path: path to compare file with source file
        """
        folder = os.path.dirname(host_path)
        if sftp.exists(host_path):
            return True
        src_attr = {
            "size": self._track_file.file_size,
            "cdate": self._track_file.creation_date
        }
        attrs = sftp.listdir_attr(folder)
        for attr in attrs:
            host_attr = {
                "size": attr.st_size,
                "cdate": self._extract_creation_date(attr)
            }
            if self.is_identical_file(src_attr, host_attr):
                return True
        return False

    def _extract_creation_date(self, attr):
        # try to get date from the filename. If it doesn't succeed, use the
        # timestamp instead
        date_fmt = "%Y-%m-%d"
        try:
            date_str = attr.filename[:10]
            date = datetime.strptime(date_str, date_fmt).strftime(date_fmt)
        except ValueError:
            date = datetime.fromtimestamp(attr.st_mtime).strftime(date_fmt)
        return date

    def is_identical_file(self, src_file, host_file):
        """checks if two files are identical

        if the sizes only differ less than 300 bytes and the modify date is the
        same, we assume that the files are the same

        :param dict src_file: has to include the keys "size" and "cdate"
        :param dict host_file: has to include the keys "size" and "cdate"
        """
        has_same_size = abs(src_file["size"] - host_file["size"]) < 300
        has_same_date = src_file["cdate"] == host_file["cdate"]
        return has_same_size and has_same_date

    def _put(self, src_file, host_path):
        self.timerStarted.emit(self.timeout)
        with pysftp.Connection(**self._conn_params) as sftp:
            self.timerStopped.emit()
            if not sftp.exists(self._host_folder):
                err_msg = self.tr("Folder does not exist on host!")
                raise UploadFolderError(err_msg)
            if self.has_file_on_host(sftp, host_path):
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
        # usually you should not catch all exception, however this runs in a
        # different threat and it is essential to terminate it when an error
        # occurs. Error may be read with errorExcepted signal.
        except (Exception) as e:
            self.timerStopped.emit()
            # short time for other msg_box to fully build
            time.sleep(0.05)
            self.errorExcepted.emit(e)
            return
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
        # see _run_upload comment for explanation of Exception use.
        except (Exception) as e:
            self.timerStopped.emit()
            self.errorExcepted.emit(e)
            return
        self.succeeded.emit()


class TrackFile(QObject):
    """Provide interface for providing access to Track object for upload

    :param Track track: track which will should be uploaded
    :param str filetype: filetype to identify uploaded file from track
    :param str|None album: album name which replaces album tag in track
    :param QObject parent: Qt Object which owns the SftpThread instance
    """

    uploadUpdated = pyqtSignal(int, int)

    def __init__(self, track, filetype, album=None, parent=None):
        QObject.__init__(self, parent=parent)
        self._tags = track.tags
        self._creation_date = track.creation_date
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
        """album tag which is used on uploaded file"""
        if self._album is None:
            return self._tags.album
        return self._album

    @album.setter
    def album(self, value):
        self._album = value

    @property
    def is_ready(self):
        """checkes if file is ready for upload"""
        return self._tags.comment != ""

    @property
    def file_size(self):
        """size of the track file in bytes"""
        return os.path.getsize(self._file)

    @property
    def creation_date(self):
        """date when the track file was created"""
        return self._creation_date

    @property
    def basename(self):
        """filename of track file which should be used on destination"""
        value = core.Track.replace_special_characters(self._tags.title)
        filetype = self._filetype.split("-")[0]
        return "{} {}.{}".format(self.creation_date, value, filetype)

    @contextmanager
    def filename(self, album=None):
        """context manager with filename of the temporary file to upload

        a temporary file is needed to change the properties of the track file.
        The file will be deleted when leaving the context manager
        CAUTION: removing may not work on a Windows system

        :param str album: name which replaces the album tag on uploaded file
        """
        if not self.is_ready:
            raise UploadCommentError(self.tr("Track has no comment!"))
        # create temporary file
        tmp_file = tempfile.mkstemp()[1]
        shutil.copyfile(self._file, tmp_file)
        tags = copy.deepcopy(self._tags)
        album = album if album is not None else self.album
        if album is not None:
            tags.album = album
            # remove track number
            tags.tracknumber = ""
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

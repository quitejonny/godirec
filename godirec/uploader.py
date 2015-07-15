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
from PyQt5.QtCore import QObject, pyqtSignal


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
            if filename.endswith(self._filetype):
                return filename
        else:
            err_msg = self.tr('filetype "{}" not in track')
            raise AttributeError(err_msg.format(self._filetype))

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
            core.Track.save_tags_for_file(tmp_file, tags)
        yield tmp_file
        # delete temporary file
        os.remove(tmp_file)

    def upload(self, sftp_conn, host_folder, slot=None):
        host_path = os.path.join(host_folder, self.basename)
        if sftp_conn.exists(host_path):
            raise UploadFileExistsError(self.tr("File exists on host!"))
        if slot is not None:
            self.uploadUpdated.connect(slot)
        with self.filename() as src_file:
            signal = self.uploadUpdated.emit if slot is not None else None
            sftp_conn.put(src_file, host_path, callback=signal)
        if slot is not None:
            self.uploadUpdated.disconnect(slot)


class UploadError(Exception):
    pass


class UploadCommentError(UploadError):
    pass


class UploadFileExistsError(UploadError):
    pass

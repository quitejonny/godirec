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

import pyaudio
from PyQt5.QtMultimedia import (QAudioEncoderSettings, QMultimedia,
        QAudioRecorder)
from PyQt5.QtCore import QUrl, QTimer
import os
import shutil
import wave
import audioop
from PyQt5.QtCore import QObject, pyqtSignal
import time
import tempfile
import concurrent.futures
import threading
import re
import mutagen
import logging
from mutagen import id3
import godirec
from godirec import audio


class Tags(object):
    """Tags object stores tags or metadata for music tracks

    The class provides tags for seven diffenrent tags:
    title, artist, album, genre, date, tracknumber, comment
    They may be accessed a dict, for example:
    tags["title"] = "This is a title"
    """

    __slots__ = ("title", "artist", "album", "genre", "date", "tracknumber",
                 "comment")

    def __init__(self, **kwargs):
        """takes properties as keyword arguments

        At initialization of the Tags class it is possible to specify
        tags properties as keyword arguments. Possible arguments are:
        title, artist, album, genre, date, tracknumber and comment

        Example:
        tags = Tags(title="This is a title", tracknumber="1")
        """
        for prop in self.keys():
            setattr(self, prop, "")
        try:
            for arg, value in kwargs.items():
                setattr(self, arg, value)
        except AttributeError as e:
            raise KeyError("The specified keyword {} is not supported by the"
                           " Tags class".format(arg))

    def keys(self):
        """return a list of available tag names"""
        return list(self.__slots__)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)


class Manager(object):
    """keeps track of the tracks an their recording files

    the manager keeps a list of all created tracks. Tracks can be easily
    created with this class and passes the right parameters to the track
    object at initialization.
    """

    def __init__(self, folder, project_name=None):
        """initializes manager 

        two arguments may be passed:
        folder: if not allready created, the manager will create the
            folder. Under this folder the subfolders for the different
            codecs will be created.
        project_name: will be used for creating the subfolder. The name
            is a coumpround of the codec name and the project name.
            Futher more the project name will be used as album tag.
        """
        if project_name is None:
            self._project_name = os.path.basename(folder)
        else:
            self._project_name = project_name
        self._folder = os.path.abspath(folder)
        self._tracks = list()
        self._track_count = 1
        self._callback = godirec.Callback()
        self._wav_folder = ""

    def create_new_track(self):
        """create new track and add it to the manager's track list

        besides the creation of a new track, this function also sets
        the track count and album tag
        """
        if not self.wav_folder:
            self._wav_folder = tempfile.mkdtemp()
        filename = "{:02d} - track.wav".format(self._track_count)
        filename = os.path.join(self.wav_folder, filename)
        tags = Tags()
        tags["tracknumber"] = str(self._track_count)
        if self._tracks:
            tags["album"] = self._tracks[-1].tags.album
        else:
            tags["album"] = self._project_name
        track = Track(filename, self._folder, self._project_name, tags)
        self._tracks.append(track)
        self._track_count += 1
        self._callback.emit()
        return track

    def set_callback(self, func, *callback_args):
        """sets callback function

        it will be called after creation of a new track
        """
        self._callback.set_func(func, *callback_args)

    @property
    def wav_folder(self):
        return self._wav_folder

    @property
    def tracklist(self):
        return self._tracks

    def set_album(self, album):
        """sets the album tag in each track"""
        for track in self._tracks:
            track.tags.album = album

    def get_track(self, index):
        """returns the track from the tracklist"""
        return self._tracks[index]

    def get_index(self, track):
        return self._tracks.index(track)

    def save_tracks(self, filetypes=[]):
        for track in self._tracks:
            track.save(filetypes)

    def __del__(self):
        if os.path.exists(self.wav_folder):
            shutil.rmtree(self.wav_folder)


class Track(object):
    """Manages track with origin wav file, tags and converted files

    The track object stores the origin wave file and the tags to it. To
    convert the track to other file formats the save function may be
    used. The file paths are internally stored. This gives the
    possibility to change the tags of the files and the filename.
    """

    lock = threading.RLock()

    def __init__(self, origin_file, folder, project_name=None, tags=Tags()):
        self._origin_file = origin_file
        self._basename = os.path.splitext(os.path.basename(origin_file))[0]
        self._origin_basename = self._basename
        self._project_name = project_name
        self._folder = folder
        self._old_title = tags.title
        self._has_file_changed = False
        self.tags = tags
        self._files = list()
        self._futures = Futures()

    def save(self, filetypes=[], folder=None):
        """will save the track with specified filetype.
        
        If no filetype is given, the function will write the metadata
        in the already exported files
        """
        if not filetypes:
            self.save_tags()
        else:
            folder = folder if folder else self._folder
            self._run_convertion(filetypes, folder)

    def _run_convertion(self, filetypes, folder):
        if not self._futures.all_futures:
            future_pool.start_callback()
        try:
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
            for filetype in filetypes:
                filename = "{}.{}".format(self.basename, filetype.codec)
                seperator = "-" if self.project_name else ""
                type_folder = "".join(
                        (str(filetype), seperator, self.project_name)
                )
                filetype_folder = os.path.join(folder, type_folder)
                if not os.path.exists(filetype_folder):
                    os.mkdir(filetype_folder)
                path = os.path.abspath(os.path.join(filetype_folder, filename))
                future = executor.submit(_run_convert_process,
                                         self.origin_file, path, filetype)
                future.add_done_callback(self._run_after_finished_process)
                future.path = path
                self._futures.add(future)
        finally:
            executor.shutdown(wait=False)

    def _run_after_finished_process(self, future):
        self._futures.remove(future)
        e = future.exception()
        if e:
            raise e
        with self.lock:
            self._files.append(future.path)
            self._has_file_changed = True
        if not self._futures:
            self.save_tags()
        if not self._futures.all_futures:
            future_pool.done_callback()

    @property
    def basename(self):
        return self._basename

    @basename.setter
    def basename(self, value):
        if self._futures.has_running_processes():
            return
        new_files = list()
        for f in self._files:
            pattern = "{}(?=\.\w+$)".format(self._basename)
            value = re.sub('[!@#$§"\*|~%&/=°^´`+<>(){}]', '_', value)
            f_new = re.sub(pattern, value, f)
            try:
                os.rename(f, f_new)
                new_files.append(f_new)
            except OSError as ose:
                logging.error(ose, exc_info=True)
        self._files = new_files
        self._basename = value
        self._has_file_changed = False

    @property
    def origin_file(self):
        return self._origin_file

    @property
    def project_name(self):
        return self._project_name

    def save_tags(self):
        if self._has_file_changed or self._old_title != self.tags.title:
            if self.tags.title:
                self.basename = "{:02d} - {}".format(
                    int(self.tags.tracknumber), self.tags.title)
            else:
                self.basename = self._origin_basename
            self._old_title = self.tags.title
        for f in self._files:
            if f.endswith('.mp3'):
                tags = mutagen.id3.ID3()
                tags['TIT2'] = id3.TIT2(encoding=3, text=self.tags['title'])
                tags['TPE1'] = id3.TPE1(encoding=3, text=self.tags['artist'])
                tags['TALB'] = id3.TALB(encoding=3, text=self.tags['album'])
                tags['TDRC'] = id3.TDRC(encoding=3, text=self.tags['date'])
                tags['TCON'] = id3.TCON(encoding=3, text=self.tags['genre'])
                tags['COMM'] = id3.COMM(encoding=3, lang='eng', desc='desc',
                                        text=self.tags['comment'])
                tags['TRCK'] = id3.TRCK(encoding=3,
                                        text=self.tags['tracknumber'])
                tags.update_to_v23()
                tags.save(f, v2_version=3)
            elif f.endswith('.wav'):
                pass
            else:
                # save tags in every track file
                audio = mutagen.File(f, easy=True)
                for tag in self.tags.keys():
                    try:
                        audio[tag] = self.tags[tag]
                    except KeyError:
                        pass
                audio.save()


class Recorder(QObject):
    """A recorder class for recording audio."""

    levelUpdated = pyqtSignal(list)
    
    RECORDING = "RECORDING"
    STOPPED = "STOPPED"
    PAUSING = "PAUSING"

    def __init__(self, manager=Manager(""), channels=2, rate=44100,
                 frames_per_buffer=1024, parent=None):
        QObject.__init__(self, parent=parent)
        self._manager = manager
        self._channels = channels
        self._rate = rate
        self._frames_per_buffer = frames_per_buffer
        self._time_info = 0
        self._state = self.STOPPED
        self.timer = Timer(parent=self)
        self.format_list = audio.codec_dict.values()
        # set some values for sample width
        self._int_bit = 16
        self._pyaudio_int = getattr(pyaudio, "paInt{}".format(self._int_bit))
        self._int_max = 2**self._int_bit/2
        self._sample_width = int(self._int_bit/8)
        
    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        if value not in (self.RECORDING, self.STOPPED, self.PAUSING):
            raise ValueError("State value not not valid!")
        self._state = value

    def play(self):
        if self.state == self.RECORDING:
            # Recorder is already playing, so no need for this function
            return
        self.timer.start()
        if self.state != self.PAUSING:
            self._p = pyaudio.PyAudio()
            self._current_track = self._manager.create_new_track()
            self._wavefile = wave.open(self._current_track.origin_file, 'wb')
            self._wavefile.setnchannels(self._channels)
            self._wavefile.setsampwidth(self._p.get_sample_size(
                                        self._pyaudio_int))
            self._wavefile.setframerate(self._rate)
        self._stream = self._p.open(format=self._pyaudio_int,
                                    channels=self._channels,
                                    rate=self._rate,
                                    input=True,
                                    stream_callback=self._get_callback())
        self._stream.start_stream()
        self.state = self.RECORDING

    def pause(self):
        if self.state == self.RECORDING:
            self._stream.close()
            self.state = self.PAUSING
            self.timer.stop()

    def cut(self):
        if self.state != self.STOPPED:
            self.stop()
            self.timer.cut()
            self.play()

    def stop(self):
        if self.state != self.STOPPED:
            self._stream.close()
            self._p.terminate()
            self._wavefile.close()
            self.state = self.STOPPED
            self.timer.stop()
            self.timer.cut()
            self.save_current_track()

    def save_current_track(self, filetype=''):
        if filetype == '':
            format_list = self.format_list
        else:
            format_list = [filetype]
        try:
            track = self._current_track
            track.save(format_list)
        except AttributeError:
            pass

    @property
    def manager(self):
        return self._manager

    @property
    def track_time(self):
        return self._time_info

    def _get_callback(self):
        def callback(in_data, frame_count, time_info, status):
            self._wavefile.writeframes(in_data)
            self._time_info = time_info
            lsample = audioop.tomono(in_data, self._sample_width, 1, 0)
            rsample = audioop.tomono(in_data, self._sample_width, 0, 1)
            l_max = audioop.max(lsample, self._sample_width)/self._int_max
            r_max = audioop.max(rsample, self._sample_width)/self._int_max
            self.levelUpdated.emit([l_max, r_max])
            return (in_data, pyaudio.paContinue)
        return callback

    def __del__(self):
        self.stop()


class Timer(QTimer):

    def __init__(self, parent=None):
        QTimer.__init__(self, parent=parent)
        self.setInterval(1000)
        self._start_time = 0.0
        self._previous_track_time = 0.0
        self._previous_rec_time = 0.0

    def start(self):
        if not self.isActive():
            self._start_time_count()
        QTimer.start(self)

    def stop(self):
        if self.isActive():
            self._stop_time_count()
        QTimer.stop(self)

    def _stop_time_count(self):
        time_delta = time.time() - self._start_time
        self._previous_track_time += time_delta
        self._previous_rec_time += time_delta

    def _start_time_count(self):
        self._start_time = time.time()

    def cut(self):
        if self.isActive():
            self._stop_time_count()
            self._start_time_count()
        self._previous_track_time = 0.0

    def get_track_time(self):
        if self.isActive():
            time_delta = time.time() - self._start_time
        else:
            time_delta = 0.0
        seconds = self._previous_track_time + time_delta
        return time.strftime("%H:%M:%S", time.gmtime(seconds))

    def get_recording_time(self):
        if self.isActive():
            time_delta = time.time() - self._start_time
        else:
            time_delta = 0.0
        seconds = self._previous_rec_time + time_delta
        return time.strftime("%H:%M:%S", time.gmtime(seconds))


def _run_convert_process(origin_file, path, filetype):
    try:
        song = audio.WaveConverter(origin_file)
        song.export(path, fmt=filetype)
    except Exception as e:
        logging.error(e, exc_info=True)
        raise e


class Futures(set):
    """Stores a set of futures from concurrent.futures

    The Futures object stores a set of futures and manages them as well
    in an class attribute which can be accessed with the all_futures
    property.
    """

    _futures = set()

    def __init__(self, *args, **kwargs):
        set.__init__(self, *args, **kwargs)

    @property
    def all_futures(self):
        """property which includes all futures

        futures of all Futures object are managed by this property and
        given to the user as frozen set
        """
        return frozenset(Futures._futures)

    def add(self, elem):
        """add future to futures object

        if the future object is allready stored in another Futures
        instance, a ValueError will be raised
        """
        if elem in Futures._futures:
            raise ValueError("element is allready in a Futures instance")
        Futures._futures.add(elem)
        set.add(self, elem)

    def remove(self, elem):
        """remove future from futures object

        if the given future does not exist in this Future object an
        error will be raised
        """
        set.remove(self, elem)
        Futures._futures.remove(elem)

    def discard(self, elem):
        """remove future from futures object

        this method works like remove method but does not raise an
        error if no future element can be remove
        """
        if elem in Futures._futures:
            Futures._futures.remove(elem)
        set.discard(self, elem)

    def pop(self, elem):
        """pop last future element

        last future element will be deleted from Futures object an
        returned by this function
        """
        elem = set.pop(self)
        Futures._futures.remove(elem)
        return elem

    def clear(self):
        """all future elements will be deleted from this instance"""
        for elem in self:
            Futures._futures.remove(elem)
        set.clear(self)

    def has_running_processes(self):
        for future in self:
            if future.running():
                return True
        return False


class FuturePool(object):

    _instance = None

    def __new__(cls):
        if FuturePool._instance is None:
            FuturePool._instance = object.__new__(cls)
        return FuturePool._instance

    def __init__(self):
        self._futures = Futures()
        self._start_callback = godirec.Callback()
        self._done_callback = godirec.Callback()

    start_callback = property(lambda s: s._start_callback.emit)

    done_callback = property(lambda s: s._done_callback.emit)

    def set_start_callback(self, func, *args):
        self._start_callback.set_func(func, *args)

    def set_done_callback(self, func, *args):
        self._done_callback.set_func(func, *args)

    def has_running_processes(self):
        for future in self._futures.all_futures:
            if future.running():
                return True
        return False

    def cancel(self):
        for future in self._futures.all_futures:
            if not future.cancel():
                return False
        return True


future_pool = FuturePool()

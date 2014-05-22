# -*- coding: utf-8 -*-
import pyaudio
import os
import wave
import shutil
from pydub import AudioSegment
import tempfile
import threading


class Tags(object):

    __slots__ = ("title", "artist", "album", "genre", "year", "comment")

    def __init__(self, title="", artist="", album="", genre="", year="",
                 comment=""):
        self.title = title
        self.artist = artist
        self.album = album
        self.genre = genre
        self.year = year
        self.comment = comment

    def keys(self):
        return list(self.__slots__)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)


class Manager(object):

    def __init__(self, folder=tempfile.mkdtemp()):
        self._folder = os.path.abspath(folder)
        self._tracks = list()
        self._track_count = 1

    def create_new_track(self):
        fname = "track_{0:d}.wav".format(self._track_count)
        fname = os.path.join(self._folder, fname)
        track = Track(fname)
        self._ref_files.append(track)
        self._track_count += 1
        return track

    def save_all(self, filetype='mp3'):
        for track in self._tracks:
            track.save(filetype)


class Track(object):

    def __init__(self, origin_file, tags=Tags()):
        self._origin_file = origin_file
        self._basename = os.path.splitext(os.path.basename(origin_file))[0]
        self.tags = tags
        self._files = list()

    def save(self, filetype=None):
        thread = threading.Thread(self._save(filetype))
        thread.deamon = True
        thread.start()

    def get_origin_file(self):
        return self._origin_file

    def save_tags(self):
        for f in self._files:
            # save tags in every track file
            pass

    def _save(self, filetype):
        if filetype != None:
            # if file does not exist convert it to filetype an and save tags
            # afterwards
            track = AudioSegment.from_wav(self._origin_file)
        self.save_tags()


class Recorder(object):

    """ A recorder class for recording audio."""

    def __init__(self, manager=Manager(), channels=2, rate=44100,
                 frames_per_buffer=1024):
        self._manager = manager
        self._channels = channels
        self._rate = rate
        self._frames_per_buffer = frames_per_buffer

    def start(self):
        self._p = pyaudio.PyAudio()
        track = self._manager.create_new_track()
        self.wavefile = wave.open(track.get_origin_file(), 'wb')
        self.wavefile.setnchannels(self._channels)
        self.wavefile.setsampwidth(self._p.get_sample_size(pyaudio.paInt16))
        self.wavefile.setframerate(self._rate)
        self.stream = self._p.open(format=pyaudio.paInt16,
                channels=self._channels,
                rate=self._rate,
                input=True,
                stream_callback=self._get_callback())
        self.stream.start_stream()

    def pause(self):
        pass

    def continue(self):
        pass

    def cut(self):
        self.stop()
        self.close()
        self.start()

    def stop(self):
        self._stream.stop_stream()

    def close(self):
        self._stream.close()
        self._p.terminate()
        self._wavefile.close()

    def get_manager(self):
        return self._manager

    def _get_callback(self):
        def callback(in_data, frame_count, time_info, status):
            self.wavefile.writeframes(in_data)
            self.time_i = time_info
            return in_data, pyaudio.paContinue
        return callback

    def __del__(self):
        self.close()
        self.p.terminate()

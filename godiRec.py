# -*- coding: utf-8 -*-
import pyaudio
import os
import wave
import shutil
from pydub import AudioSegment
import tempfile
import threading
import mutagen


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
        filename = "track_{0:d}.wav".format(self._track_count)
        filename = os.path.join(self._folder, fname)
        track = Track(filename)
        self._ref_files.append(track)
        self._track_count += 1
        return track

    @property
    def tracklist(self):
        return self._tracks

    def get_track(self, index):
        return self._tracks[index]

    def save_tracks(self, filetype='mp3'):
        for track in self._tracks:
            track.save(filetype)


class Track(object):

    def __init__(self, origin_file, tags=Tags()):
        self._origin_file = origin_file
        self._basename = os.path.splitext(os.path.basename(origin_file))[0]
        self._folder = os.path.dirname(origin_file)
        self.tags = tags
        self._files = list()

    def save(self, filetype=None, folder=None):
        """ will save the track with the specified filetype. If no filetype is
            given, the function will write the metadata in the already
            exported files"""
        if filetype == None:
            self.save_tags()
        else:
            if folder == None:
                folder = self._folder
            thread = threading.Thread(self._save(filetype, folder))
            thread.deamon = True
            thread.start()

    @property
    def origin_file(self):
        return self._origin_file

    def save_tags(self):
        for f in self._files:
            # save tags in every track file
            audio = mutagen.File(f, easy=True)
            for tag in self.tags.keys():
                audio[tag] = self.tags[tag]
            audio.save()

    def _save(self, filetype, folder):
        if filetype != None:
            # if file does not exist convert it to filetype and save tags
            # afterwards
            track = AudioSegment.from_wav(self._origin_file)
            filename = "{}.{}".format(self._basename, filetype)
            path = os.path.abspath(os.path.join(folder, filename))
            if path not in self._files:
                song = AudioSegment.from_wav(src)
                song.export(path, format=filetype)
        self.save_tags()


class Recorder(object):

    """ A recorder class for recording audio."""

    def __init__(self, manager=Manager(), channels=2, rate=44100,
                 frames_per_buffer=1024):
        self._manager = manager
        self._channels = channels
        self._rate = rate
        self._frames_per_buffer = frames_per_buffer
        self._time_info = 0
        self._is_recording = False

    def play(self):
        if not self._is_recording:
            self._p = pyaudio.PyAudio()
            track = self._manager.create_new_track()
            self._wavefile = wave.open(track.origin_file, 'wb')
            self._wavefile.setnchannels(self._channels)
            self._wavefile.setsampwidth(self._p.get_sample_size(
                                        pyaudio.paInt16))
            self._wavefile.setframerate(self._rate)
            self._stream = self._p.open(format=pyaudio.paInt16,
                    channels=self._channels,
                    rate=self._rate,
                    input=True,
                    stream_callback=self._get_callback())
        self._stream.start_stream()
        self._is_recording = True


    def pause(self):
        if self._is_recording:
            self._stream.stop_stream()

    def cut(self):
        if self._is_recording:
            self.stop()
            self.play()

    def stop(self):
        if self._is_recording:
            self._stream.close()
            self._p.terminate()
            self._wavefile.close()
            self._is_recording = False

    @property
    def is_recording(self):
        return self._is_recording

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
            return in_data, pyaudio.paContinue
        return callback

    def __del__(self):
        self.stop()

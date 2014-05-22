# -*- coding: utf-8 -*-
import pyaudio
import os
import wave
import shutil
from pydub import AudioSegment
import tempfile
from mutagen.easyid3 import EasyID3


class Tag(object):

    __slots__ = ("title", "artist", "album", "genre", "year", "comment")

    def __init__(self, title="", artist="", album="", genre="", year="",
                 comment=""):
        self.title = title
        self.artist = artist
        self.album = album
        self.genre = genre
        self.year = year
        self.comment = comment

    def get_tag_names(self):
        return self.__slots__


class RecordManager(object):

    def __init(self):
        pass


class Recorder(object):

    """ A recorder class for recording audio to a WAV file."""
 
    def __init__(self, channels=2, rate=44100, frames_per_buffer=1024):
        self.channels = channels
        self.rate = rate
        self.frames_per_buffer = frames_per_buffer
        self.track_count = 1 #fuer Titel benennung
        self.tmpdir = tempfile.mkdtemp()
 
    def open(self, fname=None, mode='wb'):
        if fname is None:
            fname = "track_{0:d}.wav".format(self.track_count)
            self.track_count += 1
        return RecordingFile(fname, mode, self.channels, self.rate,
                             self.frames_per_buffer, self.tmpdir)

    def save(self, dst, src, tags = None):
        """ Speichern einzelner Tracks als Mp3. Mit Tags oder ohne"""
        song = AudioSegment.from_wav(src)
        # Geht bestimmt schoener, oder?
        if tags is not None:
            song.export(dst, "mp3", tags)
        else:
            song.export(dst, format="mp3")
        #shutil.copyfile(os.path.join(self.tmpdir, src), dst)

    #def save_tags(self, src, tags):
    #    print src
    #    song = AudioSegment.from_mp3(src)
    #    song.export(src, "mp3", tags)


class RecordingFile:

    def __init__(self, fname, mode, channels, rate, frames_per_buffer, tmpdir):
        self.fname = fname
        self.frames_per_buffer = frames_per_buffer
        self.mode = mode
        self.channels = channels
        self.rate = rate
        self.p = pyaudio.PyAudio()
        self.wavefile = self._prepare_file(self.fname, tmpdir, self.mode)
        self.stream = None

    #def __enter__(self):
     #   return self
 
    #def __exit__(self, exception, value, traceback):
     #   self.close()

    def get_callback(self):
        def callback(in_data, frame_count, time_info, status):
            self.wavefile.writeframes(in_data)
            self.time_i = time_info
            return in_data, pyaudio.paContinue
        return callback

    def start_recording(self):
        self.stream = self.p.open(format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.rate,
                input=True,
                stream_callback=self.get_callback())
        self.stream.start_stream()
        return self

    def stop_recording(self):
        self.stream.stop_stream()
        return self

    def close(self):
        self.stream.close()
        self.p.terminate()
        self.wavefile.close()

    def _prepare_file(self, fname, tmpdir, mode='wb'):
        if not os.path.exists(tmpdir):
            os.makedirs(tmpdir)
        wavefile = wave.open(os.path.join(tmpdir, fname), mode)
        wavefile.setnchannels(self.channels)
        wavefile.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
        wavefile.setframerate(self.rate)
        return wavefile

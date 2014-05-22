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

    def keys(self):
        return list(self.__slots__)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)


class Manager(object):

    def __init__(self):
        pass


class Recorder(object):

    def __init__(self, manager=Manager(), channels=2, rate=44100,
                 frames_per_buffer=1024):
        self._manager = manager
        self._channels = channels
        self._rate = rate
        self._frames_per_buffer = frames_per_buffer
        self._p = pyaudio.PyAudio()

    def start(self):
        self.stream = self.p.open(format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.rate,
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
        self.stream.stop_stream()

    def close(self):
        self.stream.close()
        self.wavefile.close()

    def get_manager(self):
        return self._manager

    def _get_callback(self):
        def callback(in_data, frame_count, time_info, status):
            self.wavefile.writeframes(in_data)
            self.time_i = time_info
            return in_data, pyaudio.paContinue
        return callback

    def _prepare_file(self, filename):
        wavefile = wave.open(filename, 'wb')
        wavefile.setnchannels(self._channels)
        wavefile.setsampwidth(self._p.get_sample_size(pyaudio.paInt16))
        wavefile.setframerate(self._rate)
        return wavefile

    def __del__(self):
        self.close()
        self.p.terminate()


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
    def onButtonCutClicked(self):
        """ Erzeugt neue Datei und nimmt weiter auf"""
        if not self.ButtonRec.isEnabled():
            self.recfile.stop_recording()
            self.recfile.close()
            temp = self.recfile.fname
            self.recfile = self.rec.open()
            self.recfile.start_recording()
            self.start_time = datetime.now()
            fpath = os.path.join(self.rec.tmpdir, temp)
            dpath = os.path.join(self.cur_path, re.sub(".wav",".mp3",
                                                    temp))
            album = re.sub("_", " ",str(self.LabelProjekt.text()))
            th = threading.Thread(self.rec.save(dpath, fpath, album))
            th.deamon = True
            th.start()
            self.updateListTracks()

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

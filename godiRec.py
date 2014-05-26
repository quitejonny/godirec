# -*- coding: utf-8 -*-
import pyaudio
import os
import wave
import time
from pydub import AudioSegment
import tempfile
import threading
import multiprocessing
import mutagen


class Tags(object):

    __slots__ = ("title", "artist", "album", "genre", "date", "comment")

    def __init__(self, title="", artist="", album="", genre="", date="",
                 comment=""):
        self.title = title
        self.artist = artist
        self.album = album
        self.genre = genre
        self.date = date
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
        self._callback = lambda: None

    def create_new_track(self):
        filename = "track_{0:d}.wav".format(self._track_count)
        filename = os.path.join(self._folder, filename)
        track = Track(filename)
        self._tracks.append(track)
        self._track_count += 1
        self._callback()
        return track

    def set_callback(self, func):
        self._callback = func

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
                # TODO: create subfolder if needed which is named after the
                # given filetype
                folder = self._folder
            thread = threading.Thread(self._save(filetype, folder))
            thread.deamon = True
            thread.start()
            # thread = multiprocessing.Process(target=self._save,
            #                                  args=(filetype, folder))
            # thread.start()

    @property
    def basename(self):
        return self._basename

    @property
    def origin_file(self):
        return self._origin_file

    def save_tags(self):
        for f in self._files:
            # save tags in every track file
            audio = mutagen.File(f, easy=True)
            for tag in self.tags.keys():
                try:
                    audio[tag] = self.tags[tag]
                except KeyError:
                    pass
            audio.save()

    def _save(self, filetype, folder):
        if filetype != None:
            # if file does not exist convert it to filetype and save tags
            # afterwards
            track = AudioSegment.from_wav(self._origin_file)
            filename = "{}.{}".format(self._basename, filetype)
            path = os.path.abspath(os.path.join(folder, filename))
            if path not in self._files:
                song = AudioSegment.from_wav(self._origin_file)
                song.export(path, format=filetype)
                self._files.append(path)
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
        self._is_pausing = False
        self.timer = Timer()
        self.format_list = ['mp3', 'flac']

    def play(self):
        if self._is_recording and not self._is_pausing:
            # Recorder is already playing, so no need for this function
            return
        self.timer.start()
        if not self._is_recording:
            self._p = pyaudio.PyAudio()
            self._current_track = self._manager.create_new_track()
            self._wavefile = wave.open(self._current_track.origin_file, 'wb')
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
        self._is_pausing = False


    def pause(self):
        if self._is_recording:
            self._stream.close()
            self._is_pausing = True
            self.timer.stop()

    def cut(self):
        if self._is_recording:
            self.stop()
            self.timer.cut()
            self.play()

    def stop(self):
        if self._is_recording:
            self._stream.close()
            self._p.terminate()
            self._wavefile.close()
            self._is_recording = False
            self.timer.stop()
            self.save_current_track()

    def save_current_track(self, filetype=''):
        if filetype == '':
            format_list = self.format_list
        else:
            format_list = [filetype]
        try:
            track = self._current_track
            for filetype in format_list:
                track.save(filetype)
        except AttributeError:
            pass

    @property
    def is_recording(self):
        return self._is_recording

    @property
    def is_pausing(self):
        return self._is_pausing

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


class Timer(object):

    def __init__(self, callback=None):
        self._start_time = 0.0
        self._previous_track_time = 0.0
        self._previous_rec_time = 0.0
        self._callback = callback
        self.is_running = False

    def set_callback(self, callback_func):
        self._callback = callback_func

    def start(self):
        if not self.is_running:
            self._start_time = time.time()
            self.is_running = True
            if self._callback:
                self.timer = threading.Timer(1.0, self._run_timer)
                self.timer.start()

    def stop(self):
        if self.is_running:
            time_delta = time.time() - self._start_time
            self._previous_track_time += time_delta
            self._previous_rec_time += time_delta
            self.is_running = False
            if self._callback:
                self.timer.cancel()

    def cut(self):
        if self.is_running:
            self.stop()
            self._previous_track_time = 0.0
            self.start()
        else:
            self._previous_track_time = 0.0

    def get_track_time(self):
        if self.is_running:
            time_delta = time.time() - self._start_time
        else:
            time_delta = 0.0
        seconds = self._previous_track_time + time_delta
        return time.strftime("%M:%S", time.gmtime(seconds))

    def get_recording_time(self):
        if self.is_running:
            time_delta = time.time() - self._start_time
        else:
            time_delta = 0.0
        seconds = self._previous_rec_time + time_delta
        return time.strftime("%M:%S", time.gmtime(seconds))

    def _run_timer(self):
        self._callback(self)
        self.timer = threading.Timer(1.0, self._run_timer)
        self.timer.start()


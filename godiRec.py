import pyaudio
import os
import wave
import shutil
from pydub import AudioSegment

class Recorder(object):
    #A recorder class for recording audio to a WAV file.
 
    def __init__(self, channels=2, rate=44100, frames_per_buffer=1024):
        self.channels = channels
        self.rate = rate
        self.frames_per_buffer = frames_per_buffer
        self.track_count = 1 #fuer Titel benennung
 
    def open(self, fname = None, mode='wb'):
        if fname is None:
            fname = ("track_%d.wav" % self.track_count)
        return RecordingFile(fname, mode, self.channels, self.rate,
                            self.frames_per_buffer)

    #Speichern einzelner Tracks als Mp3. Mit Tags oder ohne
    def save(self, dst, src, tags = None):
        song = AudioSegment.from_wav(src)
        # Geht bestimmt schoener, oder?
        if tags is not None:
            song.export(dst, "mp3", tags)
        else:
            song.export(dst, format="mp3")

        #shutil.copyfile(".temp/"+src, dst)

    #def save_tags(self, src, tags):
    #    print src
    #    song = AudioSegment.from_mp3(src)
    #    song.export(src, "mp3", tags)

class RecordingFile:
    def __init__(self, fname, mode, channels, rate, frames_per_buffer):
        self.fname = fname
        self.frames_per_buffer = frames_per_buffer
        self.mode = mode
        self.channels = channels
        self.rate = rate
        self.p = pyaudio.PyAudio()
        self.wavefile = self._prepare_file(self.fname, self.mode)
        self.stream = None

    #def __enter__(self):
     #   return self
 
    #def __exit__(self, exception, value, traceback):
     #   self.close()

    def get_callback(self):
        def callback(in_data, frame_count, time_info, status):
            self.wavefile.writeframes(in_data)
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

    def _prepare_file(self, fname, mode='wb', directory = '.temp'):
	if not os.path.exists(directory):
		os.makedirs(directory)
        wavefile = wave.open(directory+"/"+fname, mode)
        wavefile.setnchannels(self.channels)
        wavefile.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
        wavefile.setframerate(self.rate)
        return wavefile

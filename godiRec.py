import pyaudio
import wave

class Recorder(object):
    #A recorder class for recording audio to a WAV file.
 
    def __init__(self, channels=2, rate=44100, frames_per_buffer=1024):
        self.channels = channels
        self.rate = rate
        self.frames_per_buffer = frames_per_buffer
 
    def open(self, fname, mode='wb'):
        return RecordingFile(fname, mode, self.channels, self.rate,
                            self.frames_per_buffer)

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
        print "start"
        return self

    def stop_recording(self):
        print "1"
        self.stream.stop_stream()
        print "stop"
        return self

    def close(self):
        print "closing"
        self.stream.close()
        self.p.terminate()
        self.wavefile.close()

    def _prepare_file(self, fname, mode='wb'):
        wavefile = wave.open(fname, mode)
        wavefile.setnchannels(self.channels)
        wavefile.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
        wavefile.setframerate(self.rate)
        return wavefile

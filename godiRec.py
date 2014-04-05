import pyaudio
import wave

class GodiRec:
	def __init__(self):
		self.CHUNK = 1024
		self.FORMAT = pyaudio.paInt16
		self.CHANNELS = 2
		self.RATE = 44100
		self.RECORD_SECONDS = 5
		self.WAVE_OUTPUT_FILENAME = "output.wav"
		self.p = pyaudio.PyAudio()

	def recording(self):
		stream = self.p.open(format=self.FORMAT,
				channels=self.CHANNELS,
				rate=self.RATE,
				input=True,
				frames_per_buffer=self.CHUNK)

		frames = []

		for i in range(0, int(self.RATE / self.CHUNK * self.RECORD_SECONDS)):
			    data = stream.read(self.CHUNK)
			    frames.append(data)

		print("* done recording")

		stream.stop_stream()
		stream.close()
		self.p.terminate()

		wf = wave.open(self.WAVE_OUTPUT_FILENAME, 'wb')
		wf.setnchannels(self.CHANNELS)
		wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
		wf.setframerate(self.RATE)
		wf.writeframes(b''.join(frames))
		wf.close()

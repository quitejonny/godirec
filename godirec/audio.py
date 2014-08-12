import sys
import os
import subprocess
import threading
import weakref
import io
import wave
import re
import logging
import godirec


class ConvertParams(object):
    """Defines the convertion parameters for WaveConverter"""

    def __init__(self, codec):
        self._codec = codec
        self._bitrate = None
        self.override = True
        self.acodec = None

    def __str__(self):
        if self._bitrate:
            string = "-".join((self._codec, self._bitrate))
        else:
            string = self._codec
        return string

    def get_converter_list(self):
        """returns the parameters as list for subprocess usage"""
        converter_list = ['-f', self._codec]
        if self.override:
            converter_list.append('-y')
        if self.bitrate:
            converter_list.extend(['-b:a', self.bitrate])
        if self.acodec:
            converter_list.extend(['-acodec', self.acodec])
        return converter_list

    @property
    def override(self):
        """defines wether a existing file will be overritten or not

        by default this property is set to True
        """
        return self._override

    @override.setter
    def override(self, is_file_overritten):
        self._override = is_file_overritten

    @property
    def codec(self):
        """defines the used audio codec such as wav, mp3 or flac"""
        return self._codec

    @codec.setter
    def codec(self, codec):
        self._codec = codec

    @property
    def bitrate(self):
        return self._bitrate

    @bitrate.setter
    def bitrate(self, bitrate):
        self._bitrate = bitrate

def create_codec_dict():
    codecs = [ConvertParams(i) for i in ["flac", "wav"]]
    for bitrate in ["64k", "128k"]:
        codecs.append(ConvertParams("mp3"))
        codecs[-1].bitrate = bitrate
        codecs.append(ConvertParams("ogg"))
        codecs[-1].bitrate = bitrate
        codecs[-1].acodec = 'libvorbis'
    return {str(i): i for i in codecs}


codec_dict = create_codec_dict()


class _MetaWaveConverter(type):
    """Metaclass for WaveConverter

    is needed for the class property "converter"
    """

    def __init__(cls, name, base, dct):
        cls._converter = cls._get_encoder_name()
        type.__init__(cls, name, base, dct)

    @property
    def converter(cls):
        """Get converter path of external used converter"""
        return cls._converter

    @converter.setter
    def converter(cls, value):
        """Set converter path of ffmpeg manually"""
        cls._converter = value

    @classmethod
    def _get_encoder_name(cls):
        """return enconder default application for system

        the encoder may be either avconv or ffmpeg
        """
        if cls._which("avconv"):
            return "avconv"
        elif cls._which("ffmpeg"):
            return "ffmpeg"
        else:
            raise NoEncoderError("Couldn't find ffmpeg or avconv. If you have"
                                 " one of this programs please specify the"
                                 " path")

    @classmethod
    def _which(cls, program):
        """mimics behavior of UNIX which command."""
        #Add .exe program extension for windows support
        if os.name == "nt" and not program.endswith(".exe"):
            program += ".exe"
        envdir_list = os.environ["PATH"].split(os.pathsep)
        for envdir in envdir_list:
            program_path = os.path.join(envdir, program)
            access = os.access(program_path, os.X_OK)
            if os.path.isfile(program_path) and access:
                return program_path


class WaveConverter(object, metaclass=_MetaWaveConverter):
    """Converts a wav file into other codec files like mp3, flac or ogg

    options:
    -f fmt: force input or output file format
    -i filename: input file name
    -y: Overwrite output files without asking
    -c: codec
    -stats: Print encoding progress/statistics. It is on by default.
    -b:a 128k: Sets bitrate for audio to 128kbit/s
    """

    lock = threading.RLock()
    _instances = weakref.WeakSet()
    _time = {}
    _duration = {}
    _progress_callback = godirec.Callback()

    @classmethod
    def set_progress_callback(cls, func, *args):
        cls._progress_callback.set_func(func, *args)

    def __init__(self, wav_file):
        WaveConverter._instances.add(self)
        if wav_file.endswith(".wav"):
            self.wav_file = wav_file
            with wave.open(wav_file) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                with self.lock:
                    self._duration[id(self)] = frames / float(rate)
        else:
            raise NoWaveError("Given file is not a wav file!")

    @classmethod
    def get_progress(cls):
        """returns the progress of the current converting tracks"""
        with cls.lock:
            duration = sum(cls._duration.values())
            time = sum(cls._time.values())
        if duration:
            return round(time / duration * 100.0, 1)
        else:
            return None
 
    @property
    def converter(self):
        """converter path of external used converter"""
        return WaveConverter._converter

    @converter.setter
    def converter(self, value):
        """set converter path of ffmpeg manually"""
        WaveConverter._converter = value

    def export(self, filename, fmt=None):
        """export wav file to specified filename

        the filetype may be specified in with the keyword argument fmt
        """
        self._run_conversion(filename, fmt=fmt)

    def _run_conversion(self, filename, fmt=None):
        conversion_command = [self.converter]
        conversion_command += ["-i", self.wav_file]
        if fmt:
            conversion_command += fmt.get_converter_list()
        conversion_command += [filename]
        kwargs = {}
        if sys.platform == 'win32':
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            kwargs['startupinfo'] = si
        try:
            process = subprocess.Popen(conversion_command,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, **kwargs)
            log = ''
            for line in io.TextIOWrapper(process.stdout):
                log += line
                match = re.findall('time=(\d+\.\d*)', line)
                if match:
                    with self.lock:
                        self._time[id(self)] = float(match[0])
                        self._progress_callback.emit(self.get_progress())
                else:
                    continue
        except Exception as error:
            logging.error(error, exc_info=True)
            logging.error(log)
            raise error
            # raise NoDecoderError("Decoding failed. ffmpeg error")

    def __del__(self):
        if len(self._instances) <= 1:
            with self.lock:
                self._time.clear()
                self._duration.clear()


class WaveConverterError(Exception):
    """Base error for the WaveConverter class"""
    pass


class NoWaveError(WaveConverterError):
    """Error for WaveConverter class

    No wav at initialization is specified
    """
    pass


class NoDecoderError(WaveConverterError):
    """Error for WaveConverter class

    Is raised when somewithing went wrong with the external converter
    """
    pass


class NoEncoderError(WaveConverterError):
    """Error for WaveConverter class

    the class could not find the location of the converter. The
    converter path may be specified manually in the converter property.
    """
    pass


if hasattr(sys, "frozen"):
    folder = os.path.dirname(sys.argv[0])
    WaveConverter.converter = os.path.join(folder, "ffmpeg.exe")

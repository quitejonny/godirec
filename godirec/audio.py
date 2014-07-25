import sys
import os
import subprocess
import logging


class ConvertParams(object):

    def __init__(self, codec):
        self._codec = codec


    def __str__(self):
        return self._codec


class _MetaWaveConverter(type):

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
        """Return enconder default application for system

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
        """Mimics behavior of UNIX which command."""
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
    -progress url: Send program-friendly progress information to url.
    -b:a 128k: Sets bitrate for audio to 128kbit/s
    """

    def __init__(self, wav_file):
        if wav_file.endswith(".wav"):
            self.wav_file = wav_file
        else:
            raise NoWaveError("Given file is not a wav file!")
 
    @property
    def converter(self):
        """Get converter path of external used converter"""
        return WaveConverter._converter

    @converter.setter
    def converter(self, value):
        """Set converter path of ffmpeg manually"""
        WaveConverter._converter = value

    def export(self, filename, fmt=""):
        """Export wav file to specified filename

        the filetype may be specified in with the keyword argument fmt
        """
        self._run_conversion(filename, fmt=fmt)

    def _run_conversion(self, filename, fmt=""):
        conversion_command = [self.converter, '-y']
        if fmt:
            conversion_command += ['-f', fmt]
        conversion_command += ["-i", self.wav_file]
        conversion_command += [filename]
        if sys.platform == 'win32':
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            ret_code = subprocess.call(conversion_command,
                                       stderr=open(os.devnull), startupinfo=si)
        else:
            ret_code = subprocess.call(conversion_command,
                                       stderr=open(os.devnull))
        if ret_code != 0:
            raise NoDecoderError("Decoding failed. ffmpeg error: {}".format(
                                 ret_code))


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

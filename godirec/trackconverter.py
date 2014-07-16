import sys
import os
import concurrent.futures
import threading
import subprocess
import logging


futures_array = list()
_callbacks = {"start": lambda: None, "done": lambda: None}


def start(filetypes, basename, origin_file, track_files, folder, tag_callback):
    if not futures_array:
        _callbacks["start"]()
    if 'wav' in filetypes:
        filetypes.remove('wav')
    futures = set()
    futures_array.append(futures)
    try:
        executor = concurrent.futures.ProcessPoolExecutor(max_workers=2)
        for filetype in filetypes:
            filename = "{}.{}".format(basename, filetype)
            filetype_folder = os.path.join(folder, filetype)
            if not os.path.exists(filetype_folder):
                os.mkdir(filetype_folder)
            path = os.path.abspath(os.path.join(filetype_folder, filename))
            future = executor.submit(_run_convert_process,
                                     origin_file, path, filetype)
            future.tag_callback = tag_callback
            future.path = path
            future.track_files = track_files
            future.add_done_callback(_run_after_finished_process)
            future.futures = futures
            futures.add(future)
    finally:
        executor.shutdown(wait=False)


def _run_after_finished_process(future):
    future.futures.remove(future)
    e = future.exception()
    if e:
        raise e
    path = future.path
    with threading.RLock():
        future.track_files.append(path)
    if not future.futures:
        futures_array.remove(future.futures)
        future.tag_callback()
    if not futures_array:
        _callbacks["done"]()


def cancel():
    for future in futures:
        if not future.cancel():
            return False
    return True


def has_running_processes():
    for futures in futures_array:
        for future in futures:
            if future.running():
                return True
    return False


def set_start_callback(callback):
    _callbacks["start"] = callback


def set_done_callback(callback):
    _callbacks["done"] = callback


def _run_convert_process(origin_file, path, filetype):
    try:
        song = _WaveConverter(origin_file)
        song.export(path)
    except Exception as e:
        logging.error(e, exc_info=True)
        raise e



class _MetaWaveConverter(type):

    def __init__(cls, name, base, dct):
        cls._converter = cls._get_encoder_name()
        type.__init__(cls, name, base, dct)

    @property
    def converter(cls):
        return cls._converter

    @converter.setter
    def converter(cls, value):
        cls._converter = value

    @classmethod
    def _get_encoder_name(cls):
        """
        Return enconder default application for system, either avconv or ffmpeg
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
        """
        Mimics behavior of UNIX which command.
        """
        #Add .exe program extension for windows support
        if os.name == "nt" and not program.endswith(".exe"):
            program += ".exe"
        envdir_list = os.environ["PATH"].split(os.pathsep)
        for envdir in envdir_list:
            program_path = os.path.join(envdir, program)
            access = os.access(program_path, os.X_OK)
            if os.path.isfile(program_path) and access:
                return program_path


class _WaveConverter(object, metaclass=_MetaWaveConverter):

    def __init__(self, wav_file):
        if wav_file.endswith(".wav"):
            self.wav_file = wav_file
        else:
            raise NoWaveError("Given file is not a wav file!")

    @property
    def converter(self):
        return _WaveConverter._converter

    @converter.setter
    def converter(self, value):
        _WaveConverter._converter = value

    def export(self, filename, fmt=""):
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
    pass


class NoWaveError(WaveConverterError):
    pass


class NoDecoderError(WaveConverterError):
    pass


class NoEncoderError(WaveConverterError):
    pass


if hasattr(sys, "frozen"):
    folder = os.path.dirname(sys.argv[0])
    _WaveConverter.converter = os.path.join(folder, "ffmpeg.exe")

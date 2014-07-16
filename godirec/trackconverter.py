import sys
import os
import concurrent.futures
import threading
import subprocess
import logging


futures = set()
_callbacks = {"start": lambda: None, "done": lambda: None}


def start(filetypes, basename, origin_file, track_files, folder, tag_callback):
    if not futures:
        _callbacks["start"]()
    try:
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(convert, filetypes, basename, origin_file,
                                 track_files, folder)
        future.tag_callback = tag_callback
        futures.add(future)
        future.add_done_callback(_run_after_finished_thread)
    finally:
        executor.shutdown(wait=False)


def cancel():
    for future in futures:
        if not future.cancel():
            return False
    return True


def convert(filetypes, basename, origin_file, track_files, folder):
    lock = threading.RLock()
    if 'wav' in filetypes:
        filetypes.remove('wav')
    futures = set()
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as executor:
        for filetype in filetypes:
            filename = "{}.{}".format(basename, filetype)
            filetype_folder = os.path.join(folder, filetype)
            if not os.path.exists(filetype_folder):
                os.mkdir(filetype_folder)
            path = os.path.abspath(os.path.join(filetype_folder, filename))
            future = executor.submit(_run_convert_process,
                                     origin_file, path, filetype)
            futures.add(future)
        concurrent.futures.wait(futures)
    for filetype in filetypes:
        filetype_folder = os.path.join(folder, filetype)
        filename = "{}.{}".format(basename, filetype)
        path = os.path.abspath(os.path.join(filetype_folder, filename))
        with lock:
            track_files.append(path)


def has_running_threads():
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


def _run_after_finished_thread(future):
    futures.remove(future)
    future.tag_callback()
    if not futures:
        _callbacks["done"]()


def _get_encoder_name():
    """
    Return enconder default application for system, either avconv or ffmpeg
    """
    if _which("avconv"):
        return "avconv"
    elif _which("ffmpeg"):
        return "ffmpeg"
    else:
        raise NoEncoderError("Couldn't find ffmpeg or avconv. If you have one"
                             " of this programs please specify the path")


def _which(program):
    """
    Mimics behavior of UNIX which command.
    """
    #Add .exe program extension for windows support
    if os.name == "nt" and not program.endswith(".exe"):
        program += ".exe"
    envdir_list = os.environ["PATH"].split(os.pathsep)
    for envdir in envdir_list:
        program_path = os.path.join(envdir, program)
        if os.path.isfile(program_path) and os.access(program_path, os.X_OK):
            return program_path


class _WaveConverter(object):

    converter = _get_encoder_name()

    def __init__(self, wav_file):
        if wav_file.endswith(".wav"):
            self.wav_file = wav_file
        else:
            raise NoWaveError("Given file is not a wav file!")

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

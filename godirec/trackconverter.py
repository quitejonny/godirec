import sys
import os
import concurrent.futures
import threading
from pydub import AudioSegment


if hasattr(sys, "frozen"):
    folder = os.path.dirname(sys.argv[0])
    AudioSegment.ffmpeg = os.path.join(folder, "ffmpeg.exe")


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
    song = AudioSegment.from_wav(origin_file)
    song.export(path, format=filetype)


def _run_after_finished_thread(future):
    futures.remove(future)
    future.tag_callback()
    if not futures:
        _callbacks["done"]()

#!/usr/bin/env python3
import sys
import os
import glob
import godirec
from setuptools import setup, find_packages

extra_setup = dict()

if sys.platform == 'win32':
    import subprocess
    import py2exe
    sys.argv.append('py2exe')
    extra_setup['options'] = {
        'py2exe': {
            'bundle_files': 1,
            'compressed': True,
            "excludes": [
                "readline",
                "win32api",
                "win32con",
                "ElementTree",
                "PyQt4.elementtree",
                "pyaudioop",
                "sets",
                "multiprocessing.SimpleQueue",
                "elementtree",
                "PyQt4.uic.port_v2",
            ],
            "includes": [
                "sip",
            ],
        },
    }
    extra_setup['windows'] = [{
        'script': "run_gui.py",
        "icon_resources": [
            (1, "godirec/data/ui/microphone2.ico")
        ],
        "dest_base": "GodiRec",
    }]
    extra_setup['zipfile'] = None
    # copy ffmpeg to folder
    ffmpeg_sub = subprocess.Popen(["get-command", "ffmeg"])
    ffmpeg_path = ffmpeg_sub.decode("utf-8").strip("\r\n")
    extra_setup['data_files'] = [
        (os.path.dirname(f), [f]) for f in glob.glob("godirec/data/*/*")
    ]
    extra_setup['data_files'].extend([
        ('', [ffmpeg_path])
    ])


setup(
    name = 'GodiRec',
    version = godirec.__version__,
    description = 'Gottesdienst Aufnahme Programm',
    author = 'Daniel Supplieth & Johannes Roos',
    author_email = 'daniel.supplieth@gmx.de',
    packages = find_packages(),
    include_package_data = True,
    entry_points = {
        'gui_scripts': ['godirec=godirec.gui:run'],
    },
    install_requires = [
        'pydub',
        'setuptools',
        'mutagen',
    ],
    **extra_setup
)

#!/usr/bin/env python3
import sys
import os
import glob
import godirec
from setuptools import setup, find_packages

extra_setup = dict()

if sys.platform == 'win32':
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
                "pyaudioloop",
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
    }]
    extra_setup['zipfile'] = None
    extra_setup['data_files'] = [
        (os.path.dirname(f), [f]) for f in glob.glob("godirec/data/*/*")
    ]


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

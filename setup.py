#!/usr/bin/env python3
import sys
import os
from setuptools import setup, find_packages
import godirec
if sys.platform == 'win32':
    import py2exe
    sys.argv.append('py2exe')

setup(
    name = 'GodiRec',
    version = godirec.__version__,
    description = 'Gottesdienst Aufnahme Programm',
    author = 'Daniel Supplieth & Johannes Roos',
    author_email = 'daniel.supplieth@gmx.de',
    options = {
        'py2exe': {
            'bundle_files': 1,
            'compressed': True,
            "includes": [
                "sip",
                "readline",
                "win32api",
                "win32con"
            ],
        },
    },
    # windows = [
    #     'script': "godirec/gui.py",
    #     "icon_resources": [(1, "ui/microphone2.ico")]},
    # ],
    packages = find_packages(),
    include_package_data = True,
    # zipfile = None,
    entry_points = {
        'gui_scripts': ['godirec=godirec:run_gui'],
    },
    install_requires = [
        'pydub',
        'setuptools',
        'mutagen',
    ],
)

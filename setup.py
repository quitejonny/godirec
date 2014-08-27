#!/usr/bin/env python3
# GodiRec is a program for recording a church service
# Copyright (C) 2014 Daniel Supplieth and Johannes Roos
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
                "logging.config",
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
    extra_setup['data_files'] = [
        (os.path.dirname(f), [f]) for f in glob.glob("godirec/data/*/*")
    ]
    # copy ffmpeg to folder
    ffmpeg_sub = subprocess.Popen(["where", "ffmpeg"], stdout=subprocess.PIPE)
    ffmpeg_path, _ = ffmpeg_sub.communicate()
    ffmpeg_path = ffmpeg_path.decode("utf-8").strip("\r\n")
    extra_setup['data_files'].extend([
        ('', [ffmpeg_path])
    ])
    python_sub = subprocess.Popen(["where", "python"], stdout=subprocess.PIPE)
    python_dir, _ = python_sub.communicate()
    python_dir = os.path.dirname(python_dir.decode("utf-8").strip("\r\n"))
    qico_path = os.path.join(python_dir, "Lib", "site-packages", "PyQt4",
                             "plugins", "imageformats", "qico4.dll")
    extra_setup['data_files'].extend([
        ('imageformats', [qico_path])
    ])


setup(
    name='GodiRec',
    version=godirec.__version__,
    description='Gottesdienst Aufnahme Programm',
    author='Daniel Supplieth & Johannes Roos',
    author_email='daniel.supplieth@gmx.de',
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'gui_scripts': ['godirec=godirec.gui:run'],
    },
    install_requires=[
        'pydub',
        'setuptools',
        'mutagen',
    ],
    **extra_setup
)

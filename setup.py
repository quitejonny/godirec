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
import subprocess
from setuptools import setup, find_packages
try:
    from py2exe.distutils_buildexe import py2exe as ExeCommand
    has_py2exe_module = True
except ImportError:
    from setuptools import Command as ExeCommand
    has_py2exe_module = False


extra_setup = dict()


if has_py2exe_module:
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


class ExeCreator(ExeCommand):

    user_options = []

    def run(self):
        ExeCommand.run(self)

    def initialize_options(self):
        if not sys.platform == 'win32':
            raise ValueError("This option is only available under WINDOWS")
        if not has_py2exe_module:
            raise ValueError("py2exe is not installed")
        ExeCommand.initialize_options(self)

    def finalize_options(self):
        ExeCommand.finalize_options(self)


class WindowsInstaller(ExeCreator):

    user_options = [("nsisdir=", None, "Directory to NSIS folder"),]

    def run(self):
        ExeCreator.run(self)
        cmd_list = [os.path.join(self.nsisdir, "makensis.exe"),
                    os.path.join(os.getcwd(), "make_godirec_installer.nsi")]
        cmd = subprocess.Popen(cmd_list, cwd=self.nsisdir)
        cmd.wait()

    def initialize_options(self):
        ExeCreator.initialize_options(self)
        self.nsisdir = r"C:\Program Files (x86)\NSIS"

    def finalize_options(self):
        ExeCreator.finalize_options(self)


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
    cmdclass={
        'build_windows_installer': WindowsInstaller,
        'build_exe': ExeCreator,
    },
    **extra_setup
)

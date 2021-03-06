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
from PyQt5 import QtWidgets
from PyQt5.QtCore import QLibraryInfo
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
            'bundle_files': 3,
            'compressed': True,
            "excludes": [
                "readline",
                "win32api",
                "win32con",
                "ElementTree",
                "PyQt5.elementtree",
                "pyaudioop",
                "sets",
                "multiprocessing.SimpleQueue",
                "elementtree",
                "PyQt5.uic.port_v2",
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
    ffmpeg_path = os.path.relpath(ffmpeg_path)
    extra_setup['data_files'].extend([
        ('', [ffmpeg_path])
    ])
    python_sub = subprocess.Popen(["where", "python"], stdout=subprocess.PIPE)
    python_dir, _ = python_sub.communicate()
    python_dir = os.path.dirname(python_dir.decode("utf-8").strip("\r\n"))
    def create_dirs(lib_file, *folders):
        pyqt_dir = os.path.join(python_dir, "Lib", "site-packages", "PyQt5")
        return (folders[-1],
        [os.path.join(python_dir, pyqt_dir, *folders + (lib_file,))])
    extra_setup['data_files'].extend([
        create_dirs("qico.dll", "plugins", "imageformats"),
        create_dirs("qwindows.dll", "plugins", "platforms"),
        create_dirs("libEGL.dll", "")
    ])
    # Need to get right Qt translatiopn path
    app = QtWidgets.QApplication(sys.argv)
    qt_folder = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
    qt_glob = os.path.join(qt_folder, "qtbase_??.qm")
    extra_setup['data_files'].extend([
        ("godirec/translations", [f]) for f in glob.glob(qt_glob)
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
        for key, value in extra_setup['options']['py2exe'].items():
            setattr(self, key, value)

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
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    install_requires=[
        'setuptools',
        'mutagen',
        'PyAudio',
        'PyQt5',
        'pysftp'
    ],
    cmdclass={
        'build_windows_installer': WindowsInstaller,
        'build_exe': ExeCreator,
    },
    **extra_setup
)

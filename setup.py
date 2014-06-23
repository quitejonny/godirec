#!/usr/bin/env python3
import sys
import os
import glob
from pkg_resources import resource_filename
import godirec
import setuptools.extension
from setuptools import find_packages
from cx_Freeze import setup, Executable

# GUI applications require a different base on Windows (the default is for a
# console application).
if sys.platform == "win32":
    base = "Win32GUI"
else:
    base = None

executables = [
    Executable("run_gui.py",
               copyDependentFiles=True,
               appendScriptToExe=True,
               appendScriptToLibrary=False,
               base=base,
               compress=True,
               )
]

options = {
    "build_exe": {
        "packages": [
            #"godirec",
        ],
        "zip_includes": glob.glob("godirec/data/*/*"),
        "create_shared_zip": False,
        "include_in_shared_zip": False,
        "optimize": 2,
        "compressed": True,
    }
}

# buildOptions = dict(create_shared_zip=False,
#         include_files=[os.path.join('ui', n) for n in os.listdir('ui')]
#         )


extra_setup = dict()
# 
# if sys.platform == 'win32':
#     import py2exe
#     sys.argv.append('py2exe')
#     extra_setup['options'] = {
#         'py2exe': {
#             'bundle_files': 1,
#             'compressed': True,
#             "includes": [
#                 "sip",
#                 "readline",
#                 "win32api",
#                 "win32con"
#             ],
#             'zipfile': None,
#         },
#     }
#     extra_setup['windows'] = {
#         'script': "godirec/gui.py",
#         "icon_resources": [
#             (1, resource_filename(godirec.__name__, "data/ui/microphone2.ico"))
#         ],
#     }


setup(
    name = 'GodiRec',
    version = godirec.__version__,
    description = 'Gottesdienst Aufnahme Programm',
    author = 'Daniel Supplieth & Johannes Roos',
    author_email = 'daniel.supplieth@gmx.de',
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
    executables=executables,
    options=options,
    **extra_setup
)

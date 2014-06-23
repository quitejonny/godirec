#!/usr/bin/env python3
import sys
import os
import glob
import godirec
from setuptools import setup, find_packages
# import setuptools.extension
# from cx_Freeze import setup, Executable
# 
# GUI applications require a different base on Windows (the default is for a
# console application).
# if sys.platform == "win32":
#     base = "Win32GUI"
# else:
#     base = None
# 
# extra_setup["executables"] = [
#     Executable("run_gui.py",
#                copyDependentFiles=True,
#                appendScriptToExe=True,
#                appendScriptToLibrary=False,
#                base=base,
#                compress=True,
#                )
# ]
# 
# extra_setup["options"] = {
#     "build_exe": {
#         "packages": [
#             #"godirec",
#         ],
#         "zip_includes": [(f, f) for f in glob.glob("godirec/data/*/*")],
#         "create_shared_zip": True,
#         "include_in_shared_zip": False,
#         "optimize": 2,
#         "compressed": True,
#     }
# }

# buildOptions = dict(create_shared_zip=False,
#         include_files=[os.path.join('ui', n) for n in os.listdir('ui')]
#         )


extra_setup = dict()

if sys.platform == 'win32':
    import py2exe
    sys.argv.append('py2exe')
    extra_setup['options'] = {
        'py2exe': {
            'bundle_files': 0,
            'compressed': True,
            "excludes": [
                "readline",
                "win32api",
                "win32con"
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

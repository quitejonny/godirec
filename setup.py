#!/usr/bin/env python3
import sys
import os
# import setuptools.extension
# from cx_Freeze import setup, Executable
from distutils.core import setup

# GUI applications require a different base on Windows (the default is for a
# console application).
if sys.platform == "win32":
    base = "Win32GUI"
else:
    base = None

# executables = [
#     Executable("gui_ui.py",
#                copyDependentFiles=True,
#                appendScriptToExe=True,
#                appendScriptToLibrary=False,
#                base=base,
#                )
# ]

buildOptions = dict(create_shared_zip=False,
        include_files=[os.path.join('ui', n) for n in os.listdir('ui')]
        )

setup(
    name='GodiRec',
    version = "0.1",
    description='Gottesdienst aufnahme Programm',
    author='Daniel Supplieth & Johannes Roos',
    author_email='daniel.supplieth@gmx.de',
    data_files=[('ui', [os.path.join('ui', n) for n in os.listdir('ui')])
    ],
    # options=dict(build_exe=buildOptions),
    # executables=executables,
    script=["godirec.py"],
    packages=["godirec"],
)

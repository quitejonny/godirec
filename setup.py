#!/usr/bin/env python3
import sys
import os
import setuptools.extension
from cx_Freeze import setup, Executable
# from distutils.core import setup

# GUI applications require a different base on Windows (the default is for a
# console application).
if sys.platform == "win32":
    base = "Win32GUI"
else:
    base = None

executables = [
    Executable("gui_ui.py",
               copyDependentFiles=True,
               appendScriptToExe=True,
               appendScriptToLibrary=False,
               base=base,
               )
]

buildOptions = dict(create_shared_zip=False)

setup(
    name='GodiRec',
    version = "0.1",
    description='Gottesdienst aufnahme Programm',
    author='Daniel Supplieth & Johannes Roos',
    author_email='daniel.supplieth@gmx.de',
    #options = {'py2exe': {'bundle_files': 1, 'compressed': True}},
    options=dict(build_exe=buildOptions),
    executables=executables,
)

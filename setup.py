#!/usr/bin/env python

from distutils.core import setup
import py2exe, sys, os

sys.argv.append('py2exe')

setup(
    name='GodiRec',
    version = "0.1",
    description='Gottesdienst aufnahme Programm',
    author='Daniel Supplieth & Johannes Roos',
    author_email='daniel.supplieth@gmx.de',
    options = {'py2exe': {'bundle_files': 1, 'compressed': True}},
    windows = [{'script': "gui_ui.py"}],
    zipfile = None,
)

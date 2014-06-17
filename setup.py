#!/usr/bin/env python3
import sys
from setuptools import setup
if sys.platform == 'win32':
    import py2exe, sys, os
    sys.argv.append('py2exe')

setup(
    name='GodiRec',
    version = "0.1",
    description='Gottesdienst Aufnahme Programm',
    author='Daniel Supplieth & Johannes Roos',
    author_email='daniel.supplieth@gmx.de',
    options = {'py2exe': {'bundle_files': 1, 'compressed': True, "includes":["sip"]}},
    # windows = [{'script': "godirec.pyw", "icon_resources": [(1, "ui\microphone2.ico")]}],
    packages = ["godirec"],
    package_data = {"godirec": ["data/*"]},
    # zipfile = None,
    entry_points = {
        'gui_scripts': ['godirec=godirec.gui:main'],
    },
)

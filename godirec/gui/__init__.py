# -*- coding: utf-8 -*-
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


import multiprocessing
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QLibraryInfo
import sys
import godirec
from godirec import audio
from godirec.gui import main
from godirec.gui.helper import handle_exception, handle_cli_args


def run():
    """start GUI

    The function will create the main thread for Qt Gui. It will set the
    language to system locals an start an instance of the main window.
    """
    def install_translator(filename, folder, app):
        locale = QtCore.QLocale.system().name()
        translator = QtCore.QTranslator()
        if translator.load(filename.format(locale), folder):
            app.installTranslator(translator)
        return translator
    args = handle_cli_args()
    sys.excepthook = handle_exception
    multiprocessing.freeze_support()
    app = QtWidgets.QApplication(sys.argv)
    # set translation language
    folder = godirec.resource_filename("godirec", 'data/language')
    translator1 = install_translator("godirec_{}", folder, app)
    if hasattr(sys, "frozen"):
        qt_folder = godirec.resource_filename("godirec", "translations")
    else:
        qt_folder = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
    translator2 = install_translator("qtbase_{}", qt_folder, app)
    window = main.GodiRecWindow()
    window.show()
    if "gdr_file" in args:
        window.setupProject(args["gdr_file"], False)
    else:
        audio.WaveConverter.confirm_converter_backend()
        if window.isNewProjectCreatedDialog():
            window.createNewProject()
    sys.exit(app.exec_())

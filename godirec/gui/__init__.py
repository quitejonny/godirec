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
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import QLibraryInfo
from PyQt5.QtWidgets import QMessageBox
import sys
import os
import traceback
import argparse
import logging
import godirec
from godirec import audio
from godirec.gui import main, upload


def handle_exception(exc_type, exc_value, exc_traceback):
    """handle all exceptions

    exceptions will be caught by this function. The error will be shown
    in a message box to the user and logged to the configured file.
    """
    # KeyboardInterrupt is a special case.
    # We don't raise the error dialog when it occurs.
    if issubclass(exc_type, KeyboardInterrupt):
        if QtGui.qApp:
            QtGui.qApp.quit()
        return
    filename, line, _, _ = traceback.extract_tb(exc_traceback).pop()
    filename = os.path.basename(filename)
    error = "{}: {}".format(exc_type.__name__, exc_value)
    QMessageBox.critical(
        None, "Error",
        ("<html>A critical error has occured.<br/> "
            "<b>{:s}</b><br/><br/>"
            "It occurred at <b>line {:d}</b> of file <b>{:s}</b>.<br/>"
            "For more information see error log file"
            "</html>").format(error, line, filename)
    )
    logging.error(
        "".join(
            traceback.format_exception(exc_type, exc_value, exc_traceback)
        )
    )
    sys.exit(1)


def handle_cli_args():
    args_dict = {}
    description = ("GodiRec is a Program for recording church services."
                   " It is optimized for recording every part in one single"
                   " file. You can add Tags and choose many export types.")
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('gdr_file', help='Path to gdr-file to open Project',
                        nargs='?', default="")
    parser.add_argument('--version', action="version",
                        version="v"+godirec.__version__)
    args = parser.parse_args()
    gdr_file = args.gdr_file
    if gdr_file != "":
        extension = os.path.splitext(gdr_file)[1]
        if os.path.exists(gdr_file) and extension == ".gdr":
            args_dict["gdr_file"] = gdr_file
    return args_dict


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

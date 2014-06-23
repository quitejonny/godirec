import logging
import logging.config
import sys
from PyQt4 import QtGui
import os.path
import traceback
from pkg_resources import resource_string
import json
import godirec.gui


__version__ = '0.1'


def run_gui():
    godirec.gui.run()


def handle_exception(exc_type, exc_value, exc_traceback):
    """ handle all exceptions """
    # KeyboardInterrupt is a special case.
    # We don't raise the error dialog when it occurs.
    if issubclass(exc_type, KeyboardInterrupt):
        if QtGui.qApp:
            QtGui.qApp.quit()
        return
    filename, line, _, _ = traceback.extract_tb(exc_traceback).pop()
    filename = os.path.basename(filename)
    error = "{}: {}".format(exc_type.__name__, exc_value)
    QtGui.QMessageBox.critical(
        None, "Error",
        ("<html>A critical error has occured.<br/> "
        "<b>{:s}</b><br/><br/>"
        "It occurred at <b>line {:d}</b> of file <b>{:s}</b>.<br/>"
        "For more information see error log file"
        "</html>").format(error, line, filename)
    )
    logging.error(
        "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    )
    sys.exit(1)


config_str = resource_string(__name__, "data/log/config.json").decode('utf-8')
logging.config.dictConfig(json.loads(config_str))
logging.info("Logging loaded")
# sys.excepthook = handle_exception

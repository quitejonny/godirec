import logging
import logging.config
import sys
from PyQt4 import QtGui
import os.path
import traceback
from pkg_resources import resource_filename
import godirec.gui


__version__ = '0.1'


def run_gui():
    godirec.gui.run_gui()

def handle_exception(exc_type, exc_value, exc_traceback):
  """ handle all exceptions """

  ## KeyboardInterrupt is a special case.
  ## We don't raise the error dialog when it occurs.
  if issubclass(exc_type, KeyboardInterrupt):
    if QtGui.qApp:
      QtGui.qApp.quit()
    return

  filename, line, dummy, dummy = traceback.extract_tb( exc_traceback ).pop()
  filename = os.path.basename( filename )
  error    = "%s: %s" % ( exc_type.__name__, exc_value )

  QtGui.QMessageBox.critical(None,"Error",
    "<html>A critical error has occured.<br/> "
  + "<b>%s</b><br/><br/>" % error
  + "It occurred at <b>line %d</b> of file <b>%s</b>.<br/>" % (line, filename)
  + "For more information see error log file"
  + "</html>")

  logging.error("".join(traceback.format_exception(exc_type, exc_value,
                                                   exc_traceback)))
  sys.exit(1)

_log_conf_file = resource_filename(__name__, "data/log/log.conf")
logging.config.fileConfig(_log_conf_file, disable_existing_loggers=False)
logging.info("Logging loaded")
sys.excepthook = handle_exception
